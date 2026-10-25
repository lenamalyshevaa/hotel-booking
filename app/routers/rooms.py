from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RoomStatus
from app.routers.deps import PaginationDep
from app.schemas.common import error_responses
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
    responses=error_responses(400),
)
def create_room(data: RoomCreate, service: ServiceDep):
    return service.create(data)


@router.get("", response_model=list[RoomResponse], summary="Номерной фонд")
def list_rooms(
    service: ServiceDep,
    page: PaginationDep,
    room_type_id: Annotated[int | None, Query(description="Фильтр по категории")] = None,
    room_status: Annotated[
        RoomStatus | None, Query(alias="status", description="Фильтр по состоянию")
    ] = None,
    floor: Annotated[int | None, Query(description="Фильтр по этажу")] = None,
):
    return service.list(
        skip=page.skip, limit=page.limit, room_type_id=room_type_id, status=room_status, floor=floor
    )


@router.get(
    "/{room_id}",
    response_model=RoomResponse,
    summary="Номер по id",
    responses=error_responses(404),
)
def get_room(room_id: int, service: ServiceDep):
    return service.get(room_id)


@router.put(
    "/{room_id}",
    response_model=RoomResponse,
    summary="Полностью заменить номер",
    responses=error_responses(400, 404),
)
def replace_room(room_id: int, data: RoomCreate, service: ServiceDep):
    return service.update(room_id, data, partial=False)


@router.patch(
    "/{room_id}",
    response_model=RoomResponse,
    summary="Изменить отдельные поля номера",
    responses=error_responses(400, 404),
)
def update_room(room_id: int, data: RoomUpdate, service: ServiceDep):
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
