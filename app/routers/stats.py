from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import error_responses
from app.schemas.stats import BookingStats, RevenueReport, RoomStats
from app.services.stats import StatsService

router = APIRouter(tags=["stats"])


def get_service(db: Annotated[Session, Depends(get_db)]) -> StatsService:
    return StatsService(db)


ServiceDep = Annotated[StatsService, Depends(get_service)]


@router.get("/stats/rooms", response_model=RoomStats, summary="Статистика номерного фонда")
def room_stats(service: ServiceDep):
    """Всего номеров, средняя цена за ночь, количество номеров по состояниям и по категориям."""
    return service.rooms()


@router.get("/stats/bookings", response_model=BookingStats, summary="Статистика броней")
def booking_stats(service: ServiceDep):
    """Всего броней, выручка и средняя стоимость (без отменённых), средняя длительность,
    количество и сумма броней по статусам."""
    return service.bookings()


@router.get(
    "/reports/revenue-by-month",
    response_model=RevenueReport,
    summary="Отчёт: выручка по месяцам",
    responses=error_responses(400),
)
def revenue_by_month(
    service: ServiceDep,
    date_from: Annotated[date | None, Query(description="Оплаты не раньше этой даты")] = None,
    date_to: Annotated[date | None, Query(description="Оплаты не позже этой даты")] = None,
):
    """Сумма и количество оплат по месяцам за выбранный период."""
    return service.revenue_by_month(date_from, date_to)
