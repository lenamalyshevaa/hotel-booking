from sqlalchemy import exists, func, select

from app.models import Booking, User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(func.lower(User.email) == email.lower()))

    def has_bookings(self, user_id: int) -> bool:
        return bool(self.db.scalar(select(exists().where(Booking.guest_id == user_id))))

    def list_filtered(self, *, skip: int, limit: int, role: UserRole | None = None) -> list[User]:
        filters = [User.role == role] if role is not None else []
        return self.list(skip=skip, limit=limit, filters=filters)
