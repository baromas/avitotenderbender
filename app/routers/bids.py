from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .. import crud, schemas, models
from ..database import get_db
from typing import List
router = APIRouter()


@router.post("/new", response_model=schemas.Bid, summary="Создание нового предложения")
async def create_bid(bid: schemas.BidCreate, db: AsyncSession = Depends(get_db)):
    """
    Создает новое предложение для существующего тендера.
    """
    # Проверяем, существует ли пользователь или организация, указанная в authorId
    if bid.authorType == "User":
        result = await db.execute(select(models.Employee).filter(models.Employee.id == bid.authorId))
        author = result.scalar_one_or_none()
        if not author:
            raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен")
    elif bid.authorType == "Organization":
        result = await db.execute(select(models.Organization).filter(models.Organization.id == bid.authorId))
        author = result.scalar_one_or_none()
        if not author:
            raise HTTPException(status_code=401, detail="Организация не существует или некорректна")
    else:
        raise HTTPException(status_code=400, detail="Некорректный тип автора")

    # Проверяем, существует ли тендер с указанным tenderId
    tender = await crud.get_tender_by_id(db=db, tender_id=bid.tenderId)
    if not tender:
        raise HTTPException(status_code=404, detail="Тендер не найден")

    # Проверяем, что у пользователя или организации есть права на создание предложения
    if bid.authorType == "User":
        result = await db.execute(select(models.OrganizationResponsible).filter(
            models.OrganizationResponsible.user_id == bid.authorId,
            models.OrganizationResponsible.organization_id == tender.organization_id
        ))
        responsible = result.scalar_one_or_none()
        if not responsible:
            raise HTTPException(status_code=403, detail="Недостаточно прав для выполнения действия")

    # Создаем предложение
    new_bid = await crud.create_bid(db=db, bid=bid)
    return new_bid


@router.post("/new", response_model=schemas.Bid, summary="Создание нового предложения")
async def create_bid(bid: schemas.BidCreate, db: AsyncSession = Depends(get_db)):
    """Создает новое предложение для существующего тендера."""
    return await crud.create_bid(db=db, bid=bid)


@router.get("/my", response_model=List[schemas.Bid], summary="Получение предложений пользователя")
async def get_user_bids(username: str, db: AsyncSession = Depends(get_db)):
    """Возвращает список предложений текущего пользователя."""
    bids = await crud.get_bids_by_user(db=db, username=username)
    if bids is None:
        raise HTTPException(status_code=404, detail="Предложения не найдены для данного пользователя")
    return bids


@router.patch("/{bid_id}/edit", response_model=schemas.Bid, summary="Редактирование предложения")
async def edit_bid(bid_id: str, bid: schemas.BidCreate, db: AsyncSession = Depends(get_db)):
    """Редактирование существующего предложения."""
    existing_bid = await crud.get_bid_by_id(db=db, bid_id=bid_id)
    if not existing_bid:
        raise HTTPException(status_code=404, detail="Предложение не найдено")

    updated_bid = await crud.update_bid(db=db, bid_id=bid_id, bid=bid)
    return updated_bid


@router.put("/{bid_id}/rollback/{version}", response_model=schemas.Bid, summary="Откат версии предложения")
async def rollback_bid(bid_id: str, version: int, db: AsyncSession = Depends(get_db)):
    """Откатить параметры предложения к указанной версии."""
    bid = await crud.rollback_bid_version(db=db, bid_id=bid_id, version=version)
    if bid is None:
        raise HTTPException(status_code=404, detail="Не удалось откатить предложение до указанной версии")
    return bid
