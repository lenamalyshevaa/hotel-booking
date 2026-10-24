from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import RoomStatus

if TYPE_CHECKING:
    from app.models.booking_room import BookingRoom
    from app.models.room_type import RoomType


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(10), unique=True)
    floor: Mapped[int]
    room_type_id: Mapped[int] = mapped_column(ForeignKey("room_types.id"), index=True)
    status: Mapped[RoomStatus] = mapped_column(
        Enum(RoomStatus, name="room_status"),
        default=RoomStatus.available,
        server_default=RoomStatus.available.value,
    )

    # Категория нужна почти всегда (цена, вместимость), поэтому
    # загружаем её сразу тем же запросом через JOIN (lazy="joined").
    room_type: Mapped[RoomType] = relationship(back_populates="rooms", lazy="joined")

    booking_items: Mapped[list[BookingRoom]] = relationship(back_populates="room")

    def __repr__(self) -> str:
        return f"<Room id={self.id} number={self.number!r}>"
