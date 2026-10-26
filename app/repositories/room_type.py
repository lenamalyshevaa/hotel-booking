from sqlalchemy import exists, select

from app.models import Room, RoomType
from app.repositories.base import BaseRepository


class RoomTypeRepository(BaseRepository[RoomType]):
    model = RoomType
    sort_fields = frozenset({"id", "name", "capacity", "price_per_night"})

    def get_by_name(self, name: str) -> RoomType | None:
        return self.db.scalar(select(RoomType).where(RoomType.name == name))

    def has_rooms(self, room_type_id: int) -> bool:
        return bool(self.db.scalar(select(exists().where(Room.room_type_id == room_type_id))))
