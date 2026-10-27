import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app import models  # noqa: F401
from app.config import settings
from app.core.errors import AppError
from app.routers import health, room_types, rooms, stats, users

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description=(
        "Система бронирования номеров отеля: номерной фонд, поиск свободных "
        "номеров, бронирование, заселение/выселение, оплаты и отчёты."
    ),
    version="0.3.0",
    openapi_tags=[
        {"name": "room-types", "description": "Категории номеров (справочник)"},
        {"name": "rooms", "description": "Номерной фонд"},
        {"name": "users", "description": "Пользователи: гости и персонал"},
        {"name": "stats", "description": "Статистика и отчёты"},
        {"name": "service", "description": "Служебные эндпоинты"},
    ],
)


def error_body(detail: str, error_code: str, field: str | None = None) -> dict:
    body = {"detail": detail, "error_code": error_code}
    if field is not None:
        body["field"] = field
    return body


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code, content=error_body(exc.detail, exc.error_code, exc.field)
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("Integrity error on %s %s: %s", request.method, request.url.path, exc.orig)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=error_body("Operation violates a database constraint", "CONFLICT"),
    )


@app.exception_handler(Exception)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_body("Internal server error", "INTERNAL_ERROR"),
    )


app.include_router(room_types.router)
app.include_router(rooms.router)
app.include_router(users.router)
app.include_router(stats.router)
app.include_router(health.router)
