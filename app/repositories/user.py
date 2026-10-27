from datetime import date, timedelta

from sqlalchemy import exists, select

from app.models import Booking, User, UserRole
from app.repositories.base import BaseRepository, search_condition


class UserRepository(BaseRepository[User]):
    model = User
    sort_fields = frozenset({"id", "email", "full_name", "created_at"})

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def has_bookings(self, user_id: int) -> bool:
        return bool(self.db.scalar(select(exists().where(Booking.guest_id == user_id))))

    def list_filtered(
        self,
        *,
        offset: int,
        limit: int,
        sort_by: str,
        sort_order: str,
        role: UserRole | None = None,
        created_from: date | None = None,
        created_to: date | None = None,
        has_bookings: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[User], int]:
        filters = []
        if role is not None:
            filters.append(User.role == role)
        if created_from is not None:
            filters.append(User.created_at >= created_from)
        if created_to is not None:
            filters.append(User.created_at < created_to + timedelta(days=1))
        if has_bookings is not None:
            filters.append(User.bookings.any() if has_bookings else ~User.bookings.any())
        if search:
            filters.append(search_condition(search, User.full_name, User.email, User.phone))
        return self.get_many(
            offset=offset, limit=limit, sort_by=sort_by, sort_order=sort_order, filters=filters
        )
