from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.sql import func
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException
from .models import Tender, Bid, BidDecision, BidReview, OrganizationResponsible
from .schemas import TenderCreate, BidCreate, TenderUpdate


async def get_tenders(db: AsyncSession, skip: int = 0, limit: int = 10) -> List[Tender]:
    """Возвращает список всех тендеров с возможностью пагинации."""
    result = await db.execute(select(Tender).offset(skip).limit(limit))
    return result.scalars().all()


async def create_tender(db: AsyncSession, tender: TenderCreate) -> Tender:
    """Создает новый тендер."""
    db_tender = Tender(**tender.dict())
    db.add(db_tender)
    await db.commit()
    await db.refresh(db_tender)
    return db_tender


async def get_tenders_by_user(db: AsyncSession, username: str) -> List[Tender]:
    """Возвращает список тендеров, созданных конкретным пользователем."""
    result = await db.execute(select(Tender).where(Tender.creator_username == username))
    return result.scalars().all()


async def get_tender_by_id(db: AsyncSession, tender_id: str):
    result = await db.execute(select(Tender).where(Tender.id == tender_id))
    return result.scalars().first()


async def update_tender(db: AsyncSession, tender_id: str, tender: TenderUpdate):
    existing_tender = await get_tender_by_id(db, tender_id)
    if not existing_tender:
        raise HTTPException(status_code=404, detail="Тендер не найден")

    update_data = tender.dict(exclude_unset=True)  # Исключаем поля, которые не установлены
    for key, value in update_data.items():
        setattr(existing_tender, key, value)

    db.add(existing_tender)
    await db.commit()
    await db.refresh(existing_tender)
    return existing_tender


async def rollback_tender_version(db: AsyncSession, tender_id: UUID, version: int) -> Optional[Tender]:
    """Откатывает тендер до указанной версии."""
    tender = await db.get(Tender, tender_id)
    if not tender or tender.version < version:
        raise NoResultFound("Тендер или версия не найдены")

    tender.version = version
    tender.updated_at = func.now()

    db.add(tender)
    await db.commit()
    await db.refresh(tender)
    return tender


async def get_bids(db: AsyncSession, skip: int = 0, limit: int = 10) -> List[Bid]:
    """Возвращает список всех предложений с возможностью пагинации."""
    result = await db.execute(select(Bid).offset(skip).limit(limit))
    return result.scalars().all()


async def create_bid(db: AsyncSession, bid: BidCreate) -> Bid:
    """Создает новое предложение."""
    db_bid = Bid(**bid.dict())
    db.add(db_bid)
    await db.commit()
    await db.refresh(db_bid)
    return db_bid


async def get_bids_by_user(db: AsyncSession, username: str) -> List[Bid]:
    """Возвращает список предложений, созданных конкретным пользователем."""
    result = await db.execute(select(Bid).where(Bid.creator_username == username))
    return result.scalars().all()


async def update_bid(db: AsyncSession, bid_id: UUID, bid: BidCreate) -> Optional[Bid]:
    """Обновляет существующее предложение."""
    return await update_entity(db, Bid, bid_id, bid)


async def rollback_bid_version(db: AsyncSession, bid_id: UUID, version: int) -> Optional[Bid]:
    """Откатывает предложение до указанной версии."""
    bid = await db.get(Bid, bid_id)
    if not bid or bid.version < version:
        raise NoResultFound("Предложение или версия не найдены")

    bid.version = version
    bid.updated_at = func.now()

    db.add(bid)
    await db.commit()
    await db.refresh(bid)
    return bid


async def update_entity(db: AsyncSession, model, entity_id: UUID, update_data) -> Optional:
    """Обновляет данные существующей сущности (тендера или предложения)."""
    entity = await db.get(model, entity_id)
    if not entity:
        raise NoResultFound(f"{model.__name__} не найден")

    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(entity, key, value)
    entity.updated_at = func.now()  # Обновление времени изменения

    db.add(entity)
    await db.commit()
    await db.refresh(entity)
    return entity


async def process_bid_decision(db: AsyncSession, bid_id: UUID, decision: str, username: str) -> Bid:
    """Процесс согласования или отклонения предложения."""
    bid = await db.get(Bid, bid_id)
    if not bid:
        raise NoResultFound("Предложение не найдено")

    responsible_count = await db.execute(select(func.count(OrganizationResponsible.id))
                                         .where(OrganizationResponsible.organization_id == bid.organization_id))
    responsible_count = responsible_count.scalar()

    quorum = min(3, responsible_count)

    # Если решение отклонить, сразу помечаем предложение как отклоненное
    if decision == "Rejected":
        bid.status = "CANCELED"
    else:
        # Проверяем количество согласований
        decisions = await db.execute(select(BidDecision)
                                     .where(BidDecision.bid_id == bid_id))
        decisions = decisions.scalars().all()

        approve_count = sum(1 for d in decisions if d.decision == "Approved")

        # Если количество решений равно или больше кворума, утверждаем предложение
        if approve_count + 1 >= quorum:  # +1 учитывает текущее решение
            bid.status = "PUBLISHED"
        else:
            new_decision = BidDecision(bid_id=bid_id, decision=decision, username=username)
            db.add(new_decision)

    bid.updated_at = func.now()
    db.add(bid)
    await db.commit()
    await db.refresh(bid)
    return bid


async def get_reviews_for_bid(db: AsyncSession, bid_id: UUID) -> List[BidReview]:
    """Возвращает отзывы на предложение."""
    result = await db.execute(select(BidReview).where(BidReview.bid_id == bid_id))
    return result.scalars().all()


async def create_review_for_bid(db: AsyncSession, bid_id: UUID, review: str, username: str) -> BidReview:
    """Создает отзыв на предложение."""
    bid_review = BidReview(bid_id=bid_id, description=review, username=username)
    db.add(bid_review)
    await db.commit()
    await db.refresh(bid_review)
    return bid_review
