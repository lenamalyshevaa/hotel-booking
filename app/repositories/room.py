from sqlalchemy import exists, select

from app.models import BookingRoom, Room, RoomStatus
from app.repositories.base import BaseRepository


class RoomRepository(BaseRepository[Room]):
    model = Room

    def get_by_number(self, number: str) -> Room | None:
        return self.db.scalar(select(Room).where(Room.number == number))

    def has_bookings(self, room_id: int) -> bool:
        return bool(self.db.scalar(select(exists().where(BookingRoom.room_id == room_id))))

    def list_filtered(
        self,
        *,
        skip: int,
        limit: int,
        room_type_id: int | None = None,
        status: RoomStatus | None = None,
        floor: int | None = None,
    ) -> list[Room]:
        filters = []
        if room_type_id is not None:
            filters.append(Room.room_type_id == room_type_id)
        if status is not None:
            filters.append(Room.status == status)
        if floor is not None:
            filters.append(Room.floor == floor)
        return self.list(skip=skip, limit=limit, filters=filters, order_by=Room.number)
