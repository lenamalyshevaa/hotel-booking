from sqlalchemy import exists, select

from app.models import Booking, User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User
    sort_fields = frozenset({"id", "email", "full_name", "created_at"})

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def has_bookings(self, user_id: int) -> bool:
        return bool(self.db.scalar(select(exists().where(Booking.guest_id == user_id))))

    def list_filtered(
        self, *, offset: int, limit: int, sort_by: str, sort_order: str, role: UserRole | None = None
    ) -> tuple[list[User], int]:
        filters = [User.role == role] if role is not None else []
        return self.get_many(
            offset=offset, limit=limit, sort_by=sort_by, sort_order=sort_order, filters=filters
        )
