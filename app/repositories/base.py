from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import ColumnElement, select
from sqlalchemy.orm import Session

from app.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, obj_id: int) -> ModelT | None:
        return self.db.get(self.model, obj_id)

    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        filters: Sequence[ColumnElement[bool]] = (),
        order_by: Any = None,
    ) -> list[ModelT]:
        stmt = (
            select(self.model)
            .where(*filters)
            .order_by(order_by if order_by is not None else self.model.id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def add(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.flush()
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.flush()
