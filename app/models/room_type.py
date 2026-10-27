from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.room import Room


class RoomType(Base):
    __tablename__ = "room_types"
    __table_args__ = (
        CheckConstraint("capacity > 0", name="capacity_positive"),
        CheckConstraint("price_per_night >= 0", name="price_non_negative"),
        Index(
            "ix_room_types_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    capacity: Mapped[int]
    price_per_night: Mapped[Decimal] = mapped_column(Numeric(10, 2), index=True)
    description: Mapped[str | None] = mapped_column(Text)

    rooms: Mapped[list[Room]] = relationship(back_populates="room_type")

    def __repr__(self) -> str:
        return f"<RoomType id={self.id} name={self.name!r}>"
