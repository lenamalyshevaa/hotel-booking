from sqlalchemy import Integer, cast, exists, func, select

from app.models import BookingRoom, Room, RoomStatus
from app.repositories.base import BaseRepository


class RoomRepository(BaseRepository[Room]):
    model = Room
    sort_fields = frozenset({"id", "number", "floor", "status"})

    def sort_columns(self, sort_by: str) -> list:
        if sort_by == "number":
            numeric_part = cast(func.substring(Room.number, "^[0-9]+"), Integer)
            return [numeric_part, Room.number]
        return super().sort_columns(sort_by)

    def get_by_number(self, number: str) -> Room | None:
        return self.db.scalar(select(Room).where(Room.number == number))

    def has_bookings(self, room_id: int) -> bool:
        return bool(self.db.scalar(select(exists().where(BookingRoom.room_id == room_id))))

    def list_filtered(
        self,
        *,
        offset: int,
        limit: int,
        sort_by: str,
        sort_order: str,
        room_type_id: int | None = None,
        status: RoomStatus | None = None,
        floor: int | None = None,
    ) -> tuple[list[Room], int]:
        filters = []
        if room_type_id is not None:
            filters.append(Room.room_type_id == room_type_id)
        if status is not None:
            filters.append(Room.status == status)
        if floor is not None:
            filters.append(Room.floor == floor)
        return self.get_many(
            offset=offset, limit=limit, sort_by=sort_by, sort_order=sort_order, filters=filters
        )
