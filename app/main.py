from fastapi import FastAPI

from app import models  # noqa: F401
from app.config import settings
from app.routers import health

app = FastAPI(
    title=settings.app_name,
    description=(
        "Система бронирования номеров отеля: номерной фонд, поиск свободных "
        "номеров, бронирование, заселение/выселение, оплаты и отчёты."
    ),
    version="0.1.0",
)

app.include_router(health.router)
