from datetime import datetime
from typing import Annotated, ClassVar

from pydantic import AfterValidator, ConfigDict, EmailStr, Field

from app.models import UserRole
from app.schemas.common import PatchSchema, Schema


def _check_password_bytes(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 bytes")
    return value


Email = Annotated[EmailStr, AfterValidator(str.lower), Field(examples=["guest@mail.ru"])]
Password = Annotated[
    str, Field(min_length=8, examples=["Password123!"]), AfterValidator(_check_password_bytes)
]
FullName = Annotated[str, Field(min_length=1, max_length=100, examples=["Иван Иванов"])]
Phone = Annotated[str, Field(max_length=20, examples=["+7-900-000-00-00"])]


class UserCreate(Schema):
    email: Email
    password: Password
    full_name: FullName
    phone: Phone | None = None
    role: UserRole = UserRole.guest


class UserUpdate(PatchSchema):
    nullable_fields: ClassVar[frozenset[str]] = frozenset({"phone"})

    email: Email | None = None
    password: Password | None = None
    full_name: FullName | None = None
    phone: Phone | None = None
    role: UserRole | None = None


class UserResponse(Schema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    phone: str | None
    role: UserRole
    created_at: datetime
