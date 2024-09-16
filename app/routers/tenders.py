from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from .. import crud, schemas, models
from ..database import get_db

router = APIRouter()


@router.get("/", response_model=List[schemas.Tender], summary="Получение списка тендеров")
async def get_tenders(
        limit: int = Query(10, description="Максимальное число возвращаемых объектов"),
        offset: int = Query(0, description="Количество объектов, которое нужно пропустить с начала"),
        service_type: Optional[List[str]] = Query(None, description="Фильтрация тендеров по типу услуг"),
        db: AsyncSession = Depends(get_db)
):
    """
    Возвращает список тендеров с возможностью фильтрации по типу услуг.
    Если фильтры не заданы, возвращаются все тендеры.
    """
    try:
        tenders = await crud.get_tenders(db=db, limit=limit, offset=offset, service_type=service_type)
        return tenders
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Неверный формат запроса или его параметры: {str(e)}")


@router.post("/new", response_model=schemas.Tender, summary="Создание нового тендера")
async def create_tender(tender: schemas.TenderCreate, db: AsyncSession = Depends(get_db)):
    """
    Создает новый тендер. Доступно только ответственным за организацию.
    """
    # Проверяем, существует ли пользователь с данным username
    result = await db.execute(select(models.Employee).filter(models.Employee.username == tender.creator_username))
    employee = result.scalar_one_or_none()

    if not employee:
        # Если пользователь не найден
        raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен")

    # Проверяем, связан ли пользователь с указанной организацией
    result = await db.execute(select(models.OrganizationResponsible).filter(
        models.OrganizationResponsible.user_id == employee.id,
        models.OrganizationResponsible.organization_id == tender.organization_id
    ))
    responsible = result.scalar_one_or_none()

    if not responsible:
        # Если пользователь не имеет права создавать тендер от имени этой организации
        raise HTTPException(status_code=403, detail="Недостаточно прав для выполнения действия")

    # Если все проверки пройдены, создаем тендер
    return await crud.create_tender(db=db, tender=tender)


@router.get("/my", response_model=List[schemas.Tender], summary="Получить тендеры пользователя")
async def get_user_tenders(
        username: str = Query(..., description="Имя пользователя"),
        limit: int = Query(default=5, ge=1, description="Максимальное число возвращаемых объектов."),
        offset: int = Query(default=0, ge=0,
                            description="Количество объектов, которые должны быть пропущены с начала."),
        db: AsyncSession = Depends(get_db)
):
    """Возвращает список тендеров текущего пользователя с поддержкой пагинации."""
    try:
        # Проверяем существование пользователя
        user_query = await db.execute(select(models.Employee).where(models.Employee.username == username))
        user = user_query.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=401, detail={"Пользователь не существует или некорректен."})

        # Получаем тендеры пользователя с пагинацией
        tenders_query = await db.execute(
            select(models.Tender)
            .where(models.Tender.creator_username == username)
            .order_by(models.Tender.name)
            .offset(offset)
            .limit(limit)
        )
        tenders = tenders_query.scalars().all()

        if not tenders:
            raise HTTPException(status_code=404, detail="Тендеры отсутствуют для данного пользователя")

        return tenders

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Неверный формат запроса или его параметры: {str(e)}")


@router.patch("/{tender_id}/edit", response_model=schemas.Tender, summary="Редактирование тендера")
async def edit_tender(
        tender_id: str,
        tender: schemas.TenderUpdate,
        username: str = Query(..., description="Username of the user making the request"),
        db: AsyncSession = Depends(get_db)
):
    """
    Редактирование существующего тендера.
    """
    # Проверяем, существует ли пользователь с данным username
    result = await db.execute(select(models.Employee).filter(models.Employee.username == username))
    employee = result.scalar_one_or_none()

    if not employee:
        raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен")

    # Проверяем, существует ли тендер
    existing_tender = await crud.get_tender_by_id(db=db, tender_id=tender_id)
    if not existing_tender:
        raise HTTPException(status_code=404, detail="Тендер не найден")

    # Проверяем, связан ли пользователь с указанной организацией
    result = await db.execute(select(models.OrganizationResponsible).filter(
        models.OrganizationResponsible.user_id == employee.id,
        models.OrganizationResponsible.organization_id == existing_tender.organization_id
    ))
    responsible = result.scalar_one_or_none()

    if not responsible:
        raise HTTPException(status_code=403, detail="Недостаточно прав для выполнения действия")

    # Проверяем, что тип услуги корректен
    if tender.service_type and tender.service_type not in schemas.TenderServiceType.__members__:
        raise HTTPException(
            status_code=400,
            detail=f"Некорректный тип услуги. Допустимые значения:"
                   f" {', '.join(schemas.TenderServiceType.__members__.keys())}"
        )

    # Обновляем тендер
    updated_tender = await crud.update_tender(db=db, tender_id=tender_id, tender_data=tender)
    return updated_tender


@router.put("/{tender_id}/rollback/{version}", response_model=schemas.Tender, summary="Откат версии тендера")
async def rollback_tender(tender_id: str, version: int, username: str, db: AsyncSession = Depends(get_db)):
    """Откатить параметры тендера к указанной версии и инкрементировать версию."""

    # Получаем пользователя
    result = await db.execute(select(models.Employee).filter(models.Employee.username == username))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=401, detail="Пользователь не существует или некорректен")

    # Получаем текущий тендер
    tender = await crud.get_tender_by_id(db=db, tender_id=tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Тендер не найден")

    # Получаем версию из истории
    history_entry = await crud.get_tender_history_by_version(db=db, tender_id=tender_id, version=version)
    if not history_entry:
        raise HTTPException(status_code=404, detail="Указанная версия тендера не найдена")

    # Сохраняем текущую версию тендера в истории
    await crud.save_current_version_to_history(db=db, tender=tender)

    # Откатываемся к указанной версии
    tender.name = history_entry.name
    tender.description = history_entry.description
    tender.service_type = history_entry.service_type
    tender.status = history_entry.status
    tender.organization_id = history_entry.organization_id
    tender.creator_username = history_entry.creator_username
    tender.version += 1  # Инкрементируем версию

    # Сохраняем изменения в базе данных
    db.add(tender)
    await db.commit()
    await db.refresh(tender)

    return tender
