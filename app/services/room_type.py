from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.models import RoomType
from app.repositories.room_type import RoomTypeRepository
from app.schemas.common import Pagination, Sorting, make_page
from app.schemas.room_type import RoomTypeCreate, RoomTypeUpdate


class RoomTypeService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RoomTypeRepository(db)

    def get_many(self, page: Pagination, sort: Sorting) -> dict:
        items, total = self.repo.get_many(
            offset=page.offset, limit=page.per_page, sort_by=sort.sort_by, sort_order=sort.sort_order
        )
        return make_page(items, total, page)

    def get(self, room_type_id: int) -> RoomType:
        room_type = self.repo.get(room_type_id)
        if room_type is None:
            raise NotFoundError(f"Room type {room_type_id} not found")
        return room_type

    def create(self, data: RoomTypeCreate) -> RoomType:
        self._ensure_name_free(data.name)
        room_type = self.repo.add(RoomType(**data.model_dump()))
        self.db.commit()
        return room_type

    def update(
        self, room_type_id: int, data: RoomTypeCreate | RoomTypeUpdate, *, partial: bool
    ) -> RoomType:
        room_type = self.get(room_type_id)
        values = data.model_dump(exclude_unset=partial)
        if "name" in values and values["name"] != room_type.name:
            self._ensure_name_free(values["name"])
        for field, value in values.items():
            setattr(room_type, field, value)
        self.db.commit()
        return room_type

    def delete(self, room_type_id: int) -> None:
        room_type = self.get(room_type_id)
        if self.repo.has_rooms(room_type_id):
            raise ConflictError(f"Room type {room_type_id} has rooms and cannot be deleted")
        self.repo.delete(room_type)
        self.db.commit()

    def _ensure_name_free(self, name: str) -> None:
        if self.repo.get_by_name(name) is not None:
            raise ConflictError(f"Room type '{name}' already exists", field="name")
