from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Booking, BookingStatus, Payment, Room, RoomType


class StatsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def rooms_total(self) -> tuple[int, float | None]:
        row = self.db.execute(
            select(func.count(Room.id), func.round(func.avg(RoomType.price_per_night), 2)).join(
                Room.room_type
            )
        ).one()
        return row[0], row[1]

    def rooms_by_status(self):
        return self.db.execute(
            select(Room.status, func.count(Room.id).label("count"))
            .group_by(Room.status)
            .order_by(Room.status)
        ).all()

    def rooms_by_room_type(self):
        return self.db.execute(
            select(
                RoomType.id.label("room_type_id"),
                RoomType.name,
                RoomType.price_per_night,
                func.count(Room.id).label("rooms"),
            )
            .outerjoin(Room, Room.room_type_id == RoomType.id)
            .group_by(RoomType.id)
            .order_by(func.count(Room.id).desc(), RoomType.name)
        ).all()

    def bookings_summary(self):
        not_cancelled = Booking.status != BookingStatus.cancelled
        return self.db.execute(
            select(
                func.count(Booking.id).label("total_bookings"),
                func.coalesce(func.sum(Booking.total_price).filter(not_cancelled), 0).label("revenue"),
                func.round(func.avg(Booking.total_price).filter(not_cancelled), 2).label(
                    "avg_booking_price"
                ),
                func.round(func.avg(Booking.check_out - Booking.check_in), 1).label("avg_nights"),
            )
        ).one()

    def bookings_by_status(self):
        return self.db.execute(
            select(
                Booking.status,
                func.count(Booking.id).label("count"),
                func.sum(Booking.total_price).label("total_price"),
            )
            .group_by(Booking.status)
            .order_by(Booking.status)
        ).all()

    def revenue_by_month(self, date_from: date | None, date_to: date | None):
        month = func.to_char(func.date_trunc("month", Payment.paid_at), "YYYY-MM")
        stmt = select(
            month.label("month"),
            func.count(Payment.id).label("payments"),
            func.sum(Payment.amount).label("amount"),
        )
        if date_from is not None:
            stmt = stmt.where(Payment.paid_at >= date_from)
        if date_to is not None:
            stmt = stmt.where(Payment.paid_at < date_to + timedelta(days=1))
        return self.db.execute(stmt.group_by(month).order_by(month)).all()
