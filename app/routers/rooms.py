from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RoomStatus
from app.routers.deps import PaginationDep, SearchQuery, SortingDep
from app.schemas.common import Page, error_responses
from app.schemas.room import RoomCreate, RoomResponse, RoomUpdate
from app.services.room import RoomService

router = APIRouter(prefix="/rooms", tags=["rooms"])


def get_service(db: Annotated[Session, Depends(get_db)]) -> RoomService:
    return RoomService(db)


ServiceDep = Annotated[RoomService, Depends(get_service)]


@router.post(
    "",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать номер",
    responses=error_responses(400, 409),
)
def create_room(data: RoomCreate, service: ServiceDep):
    """Создать номер. Номер должен быть уникальным, категория должна существовать."""
    return service.create(data)


@router.get(
    "",
    response_model=Page[RoomResponse],
    summary="Номерной фонд",
    responses=error_responses(400),
)
def list_rooms(
    service: ServiceDep,
    page: PaginationDep,
    sort: SortingDep,
    room_type_id: Annotated[int | None, Query(description="Фильтр по категории")] = None,
    room_status: Annotated[
        RoomStatus | None, Query(alias="status", description="Фильтр по состоянию")
    ] = None,
    floor: Annotated[int | None, Query(description="Фильтр по этажу")] = None,
    min_capacity: Annotated[
        int | None, Query(ge=1, description="Вместимость категории не меньше")
    ] = None,
    max_price: Annotated[
        Decimal | None, Query(ge=0, description="Цена категории за ночь до")
    ] = None,
    search: SearchQuery = None,
):
    """Номерной фонд с фильтрами, поиском, сортировкой и пагинацией.

    Поиск по номеру и названию категории. Поля сортировки: id, number, floor, status."""
    return service.get_many(
        page,
        sort,
        room_type_id=room_type_id,
        status=room_status,
        floor=floor,
        min_capacity=min_capacity,
        max_price=max_price,
        search=search,
    )


@router.get(
    "/{room_id}",
    response_model=RoomResponse,
    summary="Номер по id",
    responses=error_responses(404),
)
def get_room(room_id: int, service: ServiceDep):
    """Получить номер по id вместе с категорией."""
    return service.get(room_id)


@router.put(
    "/{room_id}",
    response_model=RoomResponse,
    summary="Полностью заменить номер",
    responses=error_responses(400, 404, 409),
)
def replace_room(room_id: int, data: RoomCreate, service: ServiceDep):
    """Полностью заменить номер: неприсланный статус вернётся к available."""
    return service.update(room_id, data, partial=False)


@router.patch(
    "/{room_id}",
    response_model=RoomResponse,
    summary="Изменить отдельные поля номера",
    responses=error_responses(400, 404, 409),
)
def update_room(room_id: int, data: RoomUpdate, service: ServiceDep):
    """Изменить только присланные поля номера."""
    return service.update(room_id, data, partial=True)


@router.delete(
    "/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить номер",
    description=(
        "Номер с бронями удалить нельзя (409): история броней должна сохраниться. "
        "Чтобы вывести номер из продажи, поставьте статус maintenance."
    ),
    responses=error_responses(404, 409),
)
def delete_room(room_id: int, service: ServiceDep) -> None:
    service.delete(room_id)
