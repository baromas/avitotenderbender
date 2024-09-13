from fastapi import FastAPI
from .routers import tenders, bids
from .database import engine, Base
from .init_data import create_base_data

# Создаем экземпляр приложения FastAPI
app = FastAPI(
    title="Tender Management API",
    description="API для управления тендерами и предложениями для Avito",
    version="1.0"
)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("startup")
async def startup_event():
    await create_tables()
    await create_base_data()


# Регистрируем маршруты из тендеров и предложений
app.include_router(tenders.router, prefix="/api/tenders", tags=["tenders"])
app.include_router(bids.router, prefix="/api/bids", tags=["bids"])


# Тестовый эндпоинт для проверки доступности приложения
@app.get("/api/ping", summary="Проверка доступности сервера")
async def ping():
    return "ok"
