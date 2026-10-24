from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import BookingStatus

if TYPE_CHECKING:
    from app.models.booking_room import BookingRoom
    from app.models.payment import Payment
    from app.models.user import User


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("check_out > check_in", name="dates_order"),
        CheckConstraint("total_price >= 0", name="total_non_negative"),
        Index("ix_bookings_check_in_check_out", "check_in", "check_out"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    guest_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    check_in: Mapped[date] = mapped_column(Date)
    check_out: Mapped[date] = mapped_column(Date)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status"),
        default=BookingStatus.pending,
        server_default=BookingStatus.pending.value,
        index=True,
    )
    # Сумма фиксируется в момент брони (историчность): если тариф потом
    # изменится, уже созданная бронь стоить больше не станет.
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    guest: Mapped[User] = relationship(back_populates="bookings")

    # Номера брони нужны практически при любом показе брони, поэтому
    # lazy="selectin": для списка из N броней ORM делает 1 дополнительный
    # запрос с WHERE booking_id IN (...), а не N отдельных (проблема N+1).
    items: Mapped[list[BookingRoom]] = relationship(
        back_populates="booking",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    payments: Mapped[list[Payment]] = relationship(back_populates="booking")

    @property
    def nights(self) -> int:
        return (self.check_out - self.check_in).days

    def __repr__(self) -> str:
        return (
            f"<Booking id={self.id} guest_id={self.guest_id} "
            f"{self.check_in}..{self.check_out} status={self.status.value}>"
        )
