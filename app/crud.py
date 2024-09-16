from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.sql import func
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException
from .models import (Tender, Bid, BidDecision, BidReview, OrganizationResponsible, TenderHistory, TenderServiceType,
                     TenderStatus)
from .schemas import TenderCreate, BidCreate, TenderUpdate


async def get_tenders(
        db: AsyncSession,
        limit: int = 10,
        offset: int = 0,
        service_type: Optional[List[str]] = None
):
    """
    Получение списка тендеров с учетом пагинации и фильтрации по типу услуг.
    """
    query = select(Tender)

    # Фильтрация по типу услуг, если указана
    if service_type:
        query = query.filter(Tender.service_type.in_(service_type))

    # Пагинация и сортировка
    query = query.order_by(Tender.name).offset(offset).limit(limit)

    result = await db.execute(query)
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


from fastapi import HTTPException


async def update_tender(db: AsyncSession, tender_id: str, tender_data: TenderUpdate):
    # Получаем текущий тендер
    existing_tender = await get_tender_by_id(db, tender_id)
    if not existing_tender:
        raise HTTPException(status_code=404, detail="Тендер не найден")

    # Сохраняем текущую версию тендера в истории
    history_entry = TenderHistory(
        tender_id=existing_tender.id,
        name=existing_tender.name,
        description=existing_tender.description,
        service_type=existing_tender.service_type.value,  # Преобразуем Enum в строку
        status=existing_tender.status.value,  # Преобразуем Enum в строку
        organization_id=existing_tender.organization_id,
        creator_username=existing_tender.creator_username,
        version=existing_tender.version,
        created_at=existing_tender.created_at,
        updated_at=existing_tender.updated_at
    )

    db.add(history_entry)

    # Проверка на наличие данных для обновления
    update_data = tender_data.dict(exclude_unset=True)  # Исключаем поля, которые не установлены
    if not update_data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")

    # Обновляем данные тендера
    for key, value in update_data.items():
        if isinstance(value, (TenderServiceType, TenderStatus)):  # Проверяем конкретные перечисления
            value = value.value  # Преобразуем Enum в строку перед обновлением
        setattr(existing_tender, key, value)

    # Инкрементируем версию тендера
    existing_tender.version += 1

    # Сохраняем изменения в базе данных
    db.add(existing_tender)
    await db.commit()
    await db.refresh(existing_tender)

    return existing_tender


async def rollback_tender_version(db: AsyncSession, tender_id: str, version: int):
    # Получаем требуемую версию тендера из таблицы истории
    result = await db.execute(select(TenderHistory).filter(
        TenderHistory.tender_id == tender_id,
        TenderHistory.version == version
    ))
    history_entry = result.scalar_one_or_none()

    if not history_entry:
        return None  # Версия не найдена

    # Обновляем текущий тендер данными из истории
    tender = await get_tender_by_id(db=db, tender_id=tender_id)
    if tender is None:
        return None

    tender.name = history_entry.name
    tender.description = history_entry.description
    tender.service_type = TenderServiceType(history_entry.service_type)
    tender.status = TenderStatus(history_entry.status)
    tender.organization_id = history_entry.organization_id
    tender.creator_username = history_entry.creator_username
    tender.version = history_entry.version

    await db.commit()
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
        bid.status = "Canceled"
    else:
        # Проверяем количество согласований
        decisions = await db.execute(select(BidDecision)
                                     .where(BidDecision.bid_id == bid_id))
        decisions = decisions.scalars().all()

        approve_count = sum(1 for d in decisions if d.decision == "Approved")

        # Если количество решений равно или больше кворума, утверждаем предложение
        if approve_count + 1 >= quorum:  # +1 учитывает текущее решение
            bid.status = "Published"
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


async def save_current_version_to_history(db: AsyncSession, tender: Tender):
    # Сохраняем текущую версию тендера в таблицу истории
    history_entry = TenderHistory(
        tender_id=tender.id,
        name=tender.name,
        description=tender.description,
        service_type=tender.service_type.value,
        status=tender.status.value,
        organization_id=tender.organization_id,
        creator_username=tender.creator_username,
        version=tender.version,
        created_at=tender.created_at,
        updated_at=tender.updated_at
    )

    db.add(history_entry)
    db.commit()


async def get_tender_history_by_version(db: AsyncSession, tender_id: str, version: int):
    result = await db.execute(
        select(TenderHistory)
        .where(
            TenderHistory.tender_id == tender_id,
            TenderHistory.version == version
        )
    )
    return result.scalar_one_or_none()
