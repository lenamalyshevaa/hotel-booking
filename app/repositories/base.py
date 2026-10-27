from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import BadRequestError
from app.database import Base

ModelT = TypeVar("ModelT", bound=Base)


def search_condition(search: str, *columns) -> ColumnElement[bool]:
    escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    return or_(*(column.ilike(pattern, escape="\\") for column in columns))


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]
    sort_fields: frozenset[str] = frozenset({"id"})

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, obj_id: int) -> ModelT | None:
        return self.db.get(self.model, obj_id)

    def get_many(
        self,
        *,
        offset: int,
        limit: int,
        sort_by: str = "id",
        sort_order: str = "asc",
        filters: Sequence[ColumnElement[bool]] = (),
    ) -> tuple[list[ModelT], int]:
        if sort_by not in self.sort_fields:
            allowed = ", ".join(sorted(self.sort_fields))
            raise BadRequestError(
                f"Invalid sort field: {sort_by}. Allowed: {allowed}", field="sort_by"
            )
        sort_columns = self.sort_columns(sort_by)
        if sort_order == "desc":
            sort_columns = [column.desc() for column in sort_columns]

        stmt = select(self.model).where(*filters)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery()))
        items = self.db.scalars(
            stmt.order_by(*sort_columns, self.model.id).offset(offset).limit(limit)
        )
        return list(items), total

    def sort_columns(self, sort_by: str) -> list:
        return [getattr(self.model, sort_by)]

    def add(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.flush()
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.flush()
