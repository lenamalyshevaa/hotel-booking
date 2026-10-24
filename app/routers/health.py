from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

router = APIRouter(tags=["service"])


@router.get("/", summary="Информация о сервисе")
def root() -> dict:
    return {"service": settings.app_name, "status": "running", "docs": "/docs"}


@router.get(
    "/health",
    summary="Проверка доступности API и базы данных",
    responses={503: {"description": "База данных недоступна"}},
)
def health(db: Session = Depends(get_db)) -> dict:
    """Выполняет `SELECT 1`. Если БД не отвечает, возвращает 503, а не падает."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    return {"status": "ok", "database": "ok"}
