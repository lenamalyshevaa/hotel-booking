from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app import models  # noqa: F401
from app.config import settings
from app.core.errors import AppError
from app.routers import health, room_types, rooms, users

app = FastAPI(
    title=settings.app_name,
    description=(
        "Система бронирования номеров отеля: номерной фонд, поиск свободных "
        "номеров, бронирование, заселение/выселение, оплаты и отчёты."
    ),
    version="0.2.0",
    openapi_tags=[
        {"name": "room-types", "description": "Категории номеров (справочник)"},
        {"name": "rooms", "description": "Номерной фонд"},
        {"name": "users", "description": "Пользователи: гости и персонал"},
        {"name": "service", "description": "Служебные эндпоинты"},
    ],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Operation violates a database constraint"},
    )


app.include_router(room_types.router)
app.include_router(rooms.router)
app.include_router(users.router)
app.include_router(health.router)
