from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UserRole
from app.routers.deps import PaginationDep
from app.schemas.common import error_responses
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_service(db: Annotated[Session, Depends(get_db)]) -> UserService:
    return UserService(db)


ServiceDep = Annotated[UserService, Depends(get_service)]


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать пользователя",
    responses=error_responses(400),
)
def create_user(data: UserCreate, service: ServiceDep):
    return service.create(data)


@router.get("", response_model=list[UserResponse], summary="Список пользователей")
def list_users(
    service: ServiceDep,
    page: PaginationDep,
    role: Annotated[UserRole | None, Query(description="Фильтр по роли")] = None,
):
    return service.list(skip=page.skip, limit=page.limit, role=role)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Пользователь по id",
    responses=error_responses(404),
)
def get_user(user_id: int, service: ServiceDep):
    return service.get(user_id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Полностью заменить пользователя",
    responses=error_responses(400, 404),
)
def replace_user(user_id: int, data: UserCreate, service: ServiceDep):
    return service.update(user_id, data, partial=False)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Изменить отдельные поля пользователя",
    responses=error_responses(400, 404),
)
def update_user(user_id: int, data: UserUpdate, service: ServiceDep):
    return service.update(user_id, data, partial=True)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить пользователя",
    description="Пользователя с бронями удалить нельзя (409).",
    responses=error_responses(404, 409),
)
def delete_user(user_id: int, service: ServiceDep) -> None:
    service.delete(user_id)
