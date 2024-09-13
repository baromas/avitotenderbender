from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .. import crud, schemas
from ..database import get_db

router = APIRouter()


@router.get("/", response_model=List[schemas.Tender], summary="Получение списка тендеров")
async def get_tenders(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Возвращает список тендеров с возможностью пагинации."""
    return await crud.get_tenders(db=db, skip=skip, limit=limit)


@router.post("/new", response_model=schemas.Tender, summary="Создание нового тендера")
async def create_tender(tender: schemas.TenderCreate, db: AsyncSession = Depends(get_db)):
    """Создает новый тендер. Доступно только ответственным за организацию."""
    return await crud.create_tender(db=db, tender=tender)


@router.get("/my", response_model=List[schemas.Tender], summary="Получить тендеры пользователя")
async def get_user_tenders(username: str, db: AsyncSession = Depends(get_db)):
    """Возвращает список тендеров текущего пользователя."""
    tenders = await crud.get_tenders_by_user(db=db, username=username)
    if tenders is None:
        raise HTTPException(status_code=404, detail="Тендеры не найдены для данного пользователя")
    return tenders


@router.patch("/{tender_id}/edit", response_model=schemas.Tender, summary="Редактирование тендера")
async def edit_tender(tender_id: str, tender: schemas.TenderUpdate, db: AsyncSession = Depends(get_db)):
    """Редактирование существующего тендера."""
    existing_tender = await crud.get_tender_by_id(db=db, tender_id=tender_id)
    if not existing_tender:
        raise HTTPException(status_code=404, detail="Тендер не найден")

    updated_tender = await crud.update_tender(db=db, tender_id=tender_id, tender=tender)
    return updated_tender


@router.put("/{tender_id}/rollback/{version}", response_model=schemas.Tender, summary="Откат версии тендера")
async def rollback_tender(tender_id: str, version: int, db: AsyncSession = Depends(get_db)):
    """Откатить параметры тендера к указанной версии."""
    tender = await crud.rollback_tender_version(db=db, tender_id=tender_id, version=version)
    if tender is None:
        raise HTTPException(status_code=404, detail="Не удалось откатить тендер до указанной версии")
    return tender
