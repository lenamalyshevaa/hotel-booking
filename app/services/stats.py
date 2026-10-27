from datetime import date

from sqlalchemy.orm import Session

from app.core.errors import check_range
from app.repositories.stats import StatsRepository


class StatsService:
    def __init__(self, db: Session) -> None:
        self.repo = StatsRepository(db)

    def rooms(self) -> dict:
        total, avg_price = self.repo.rooms_total()
        return {
            "total_rooms": total,
            "avg_price_per_night": avg_price,
            "by_status": [row._asdict() for row in self.repo.rooms_by_status()],
            "by_room_type": [row._asdict() for row in self.repo.rooms_by_room_type()],
        }

    def bookings(self) -> dict:
        return {
            **self.repo.bookings_summary()._asdict(),
            "by_status": [row._asdict() for row in self.repo.bookings_by_status()],
        }

    def revenue_by_month(self, date_from: date | None, date_to: date | None) -> dict:
        check_range(date_from, date_to, "date_from", "date_to")
        months = [row._asdict() for row in self.repo.revenue_by_month(date_from, date_to)]
        return {
            "date_from": date_from,
            "date_to": date_to,
            "total_amount": sum((m["amount"] for m in months), start=0),
            "months": months,
        }
