from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.deps import PaginationDep, SearchQuery, SortingDep
from app.schemas.common import Page, error_responses
from app.schemas.room_type import RoomTypeCreate, RoomTypeResponse, RoomTypeUpdate
from app.services.room_type import RoomTypeService

router = APIRouter(prefix="/room-types", tags=["room-types"])


def get_service(db: Annotated[Session, Depends(get_db)]) -> RoomTypeService:
    return RoomTypeService(db)


ServiceDep = Annotated[RoomTypeService, Depends(get_service)]


@router.post(
    "",
    response_model=RoomTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать категорию номера",
    responses=error_responses(409),
)
def create_room_type(data: RoomTypeCreate, service: ServiceDep):
    """Создать категорию номера. Название должно быть уникальным, иначе 409."""
    return service.create(data)


@router.get(
    "",
    response_model=Page[RoomTypeResponse],
    summary="Список категорий",
    responses=error_responses(400),
)
def list_room_types(
    service: ServiceDep,
    page: PaginationDep,
    sort: SortingDep,
    min_capacity: Annotated[int | None, Query(ge=1, description="Вместимость не меньше")] = None,
    min_price: Annotated[Decimal | None, Query(ge=0, description="Цена за ночь от")] = None,
    max_price: Annotated[Decimal | None, Query(ge=0, description="Цена за ночь до")] = None,
    search: SearchQuery = None,
):
    """Список категорий с фильтрами, поиском, сортировкой и пагинацией.

    Поиск по названию и описанию. Поля сортировки: id, name, capacity, price_per_night."""
    return service.get_many(
        page,
        sort,
        min_capacity=min_capacity,
        min_price=min_price,
        max_price=max_price,
        search=search,
    )


@router.get(
    "/{room_type_id}",
    response_model=RoomTypeResponse,
    summary="Категория по id",
    responses=error_responses(404),
)
def get_room_type(room_type_id: int, service: ServiceDep):
    """Получить категорию по id."""
    return service.get(room_type_id)


@router.put(
    "/{room_type_id}",
    response_model=RoomTypeResponse,
    summary="Полностью заменить категорию",
    responses=error_responses(404, 409),
)
def replace_room_type(room_type_id: int, data: RoomTypeCreate, service: ServiceDep):
    """Полностью заменить категорию: неприсланные поля получают значения по умолчанию."""
    return service.update(room_type_id, data, partial=False)


@router.patch(
    "/{room_type_id}",
    response_model=RoomTypeResponse,
    summary="Изменить отдельные поля категории",
    responses=error_responses(404, 409),
)
def update_room_type(room_type_id: int, data: RoomTypeUpdate, service: ServiceDep):
    """Изменить только присланные поля категории."""
    return service.update(room_type_id, data, partial=True)


@router.delete(
    "/{room_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить категорию",
    description="Нельзя удалить категорию, к которой привязаны номера (409).",
    responses=error_responses(404, 409),
)
def delete_room_type(room_type_id: int, service: ServiceDep) -> None:
    service.delete(room_type_id)
