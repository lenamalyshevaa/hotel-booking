from decimal import Decimal

from sqlalchemy import exists, select

from app.models import Room, RoomType
from app.repositories.base import BaseRepository, search_condition


class RoomTypeRepository(BaseRepository[RoomType]):
    model = RoomType
    sort_fields = frozenset({"id", "name", "capacity", "price_per_night"})

    def get_by_name(self, name: str) -> RoomType | None:
        return self.db.scalar(select(RoomType).where(RoomType.name == name))

    def has_rooms(self, room_type_id: int) -> bool:
        return bool(self.db.scalar(select(exists().where(Room.room_type_id == room_type_id))))

    def list_filtered(
        self,
        *,
        offset: int,
        limit: int,
        sort_by: str,
        sort_order: str,
        min_capacity: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        search: str | None = None,
    ) -> tuple[list[RoomType], int]:
        filters = []
        if min_capacity is not None:
            filters.append(RoomType.capacity >= min_capacity)
        if min_price is not None:
            filters.append(RoomType.price_per_night >= min_price)
        if max_price is not None:
            filters.append(RoomType.price_per_night <= max_price)
        if search:
            filters.append(search_condition(search, RoomType.name, RoomType.description))
        return self.get_many(
            offset=offset, limit=limit, sort_by=sort_by, sort_order=sort_order, filters=filters
        )
