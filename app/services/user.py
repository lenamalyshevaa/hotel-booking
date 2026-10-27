from datetime import date

from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, check_range
from app.core.security import hash_password
from app.models import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.common import Pagination, Sorting, make_page
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def get_many(
        self,
        page: Pagination,
        sort: Sorting,
        *,
        role: UserRole | None = None,
        created_from: date | None = None,
        created_to: date | None = None,
        has_bookings: bool | None = None,
        search: str | None = None,
    ) -> dict:
        check_range(created_from, created_to, "created_from", "created_to")
        items, total = self.repo.list_filtered(
            offset=page.offset,
            limit=page.per_page,
            sort_by=sort.sort_by,
            sort_order=sort.sort_order,
            role=role,
            created_from=created_from,
            created_to=created_to,
            has_bookings=has_bookings,
            search=search,
        )
        return make_page(items, total, page)

    def get(self, user_id: int) -> User:
        user = self.repo.get(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found")
        return user

    def create(self, data: UserCreate) -> User:
        self._ensure_email_free(data.email)
        values = data.model_dump(exclude={"password"})
        user = self.repo.add(User(**values, password_hash=hash_password(data.password)))
        self.db.commit()
        return user

    def update(self, user_id: int, data: UserCreate | UserUpdate, *, partial: bool) -> User:
        user = self.get(user_id)
        values = data.model_dump(exclude_unset=partial)
        if "email" in values and values["email"] != user.email:
            self._ensure_email_free(values["email"])
        if "password" in values:
            values["password_hash"] = hash_password(values.pop("password"))
        for field, value in values.items():
            setattr(user, field, value)
        self.db.commit()
        return user

    def delete(self, user_id: int) -> None:
        user = self.get(user_id)
        if self.repo.has_bookings(user_id):
            raise ConflictError(f"User {user_id} has bookings and cannot be deleted")
        self.repo.delete(user)
        self.db.commit()

    def _ensure_email_free(self, email: str) -> None:
        if self.repo.get_by_email(email) is not None:
            raise ConflictError(f"Email '{email}' is already registered", field="email")
