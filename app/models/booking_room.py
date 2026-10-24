from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    FetchedValue,
    ForeignKey,
    Numeric,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.room import Room


class BookingRoom(Base):
    """price_per_night: цена за ночь на момент брони. Осознанная денормализация:
    тариф в room_types может меняться, а бронь должна помнить свою цену.

    check_in, check_out, is_active: копия дат и «активности» брони.
    Их заполняет и поддерживает триггер в БД (см. миграцию 0001),
    приложение их не пишет. Нужны они для exclusion constraint
    no_overlapping_active_bookings, который запрещает двойное бронирование:
    ограничение может проверять только колонки своей таблицы.
    """

    __tablename__ = "booking_rooms"
    __table_args__ = (
        UniqueConstraint("booking_id", "room_id"),
        CheckConstraint("price_per_night >= 0", name="price_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"), index=True
    )
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), index=True)
    price_per_night: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # FetchedValue(): значение вычисляет сервер (триггер), ORM его не отправляет.
    check_in: Mapped[date] = mapped_column(
        Date, server_default=FetchedValue(), server_onupdate=FetchedValue()
    )
    check_out: Mapped[date] = mapped_column(
        Date, server_default=FetchedValue(), server_onupdate=FetchedValue()
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=text("true"), server_onupdate=FetchedValue()
    )

    booking: Mapped[Booking] = relationship(back_populates="items")
    # Номер нужен всегда, когда показываем строку брони, поэтому грузим его JOIN-ом.
    room: Mapped[Room] = relationship(back_populates="booking_items", lazy="joined")

    def __repr__(self) -> str:
        return f"<BookingRoom booking_id={self.booking_id} room_id={self.room_id}>"
