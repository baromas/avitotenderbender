from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .. import crud, schemas
from ..database import get_db

router = APIRouter()


@router.get("/", response_model=List[schemas.Bid], summary="Получение списка предложений")
async def get_bids(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Возвращает список предложений с возможностью пагинации."""
    return await crud.get_bids(db=db, skip=skip, limit=limit)


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
