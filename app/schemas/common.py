from dataclasses import dataclass
from typing import ClassVar, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, model_validator


class Schema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class PatchSchema(Schema):
    nullable_fields: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def _reject_explicit_nulls(self):
        nulls = sorted(
            name
            for name in self.model_fields_set
            if getattr(self, name) is None and name not in self.nullable_fields
        )
        if nulls:
            raise ValueError(f"Fields cannot be null: {', '.join(nulls)}")
        return self


T = TypeVar("T")


@dataclass
class Pagination:
    page: int
    per_page: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


@dataclass
class Sorting:
    sort_by: str
    sort_order: Literal["asc", "desc"]


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int


def make_page(items: list, total: int, page: Pagination) -> dict:
    return {
        "items": items,
        "total": total,
        "page": page.page,
        "per_page": page.per_page,
        "total_pages": (total + page.per_page - 1) // page.per_page,
    }


class ErrorResponse(BaseModel):
    detail: str
    error_code: str
    field: str | None = None


def error_responses(*codes: int) -> dict:
    descriptions = {
        400: "Некорректные данные (нарушено бизнес-правило или неверное поле сортировки)",
        404: "Объект не найден",
        409: "Конфликт: значение уже занято или удаление нарушит целостность данных",
    }
    return {code: {"model": ErrorResponse, "description": descriptions[code]} for code in codes}
