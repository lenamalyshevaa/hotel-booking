from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UserRole
from app.routers.deps import PaginationDep, SearchQuery, SortingDep
from app.schemas.common import Page, error_responses
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
    responses=error_responses(409),
)
def create_user(data: UserCreate, service: ServiceDep):
    """Создать пользователя. Email уникален без учёта регистра, пароль хранится как bcrypt-хэш."""
    return service.create(data)


@router.get(
    "",
    response_model=Page[UserResponse],
    summary="Список пользователей",
    responses=error_responses(400),
)
def list_users(
    service: ServiceDep,
    page: PaginationDep,
    sort: SortingDep,
    role: Annotated[UserRole | None, Query(description="Фильтр по роли")] = None,
    created_from: Annotated[date | None, Query(description="Зарегистрирован не раньше")] = None,
    created_to: Annotated[date | None, Query(description="Зарегистрирован не позже")] = None,
    has_bookings: Annotated[bool | None, Query(description="Есть ли у пользователя брони")] = None,
    search: SearchQuery = None,
):
    """Список пользователей с фильтрами, поиском, сортировкой и пагинацией.

    Поиск по ФИО, email и телефону. Поля сортировки: id, email, full_name, created_at."""
    return service.get_many(
        page,
        sort,
        role=role,
        created_from=created_from,
        created_to=created_to,
        has_bookings=has_bookings,
        search=search,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Пользователь по id",
    responses=error_responses(404),
)
def get_user(user_id: int, service: ServiceDep):
    """Получить пользователя по id. Пароль и его хэш не возвращаются."""
    return service.get(user_id)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Полностью заменить пользователя",
    responses=error_responses(404, 409),
)
def replace_user(user_id: int, data: UserCreate, service: ServiceDep):
    """Полностью заменить пользователя, включая пароль."""
    return service.update(user_id, data, partial=False)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Изменить отдельные поля пользователя",
    responses=error_responses(404, 409),
)
def update_user(user_id: int, data: UserUpdate, service: ServiceDep):
    """Изменить только присланные поля пользователя (роль, телефон, пароль и т.д.)."""
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
