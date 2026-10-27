from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import BadRequestError, ConflictError, NotFoundError
from app.models import Room, RoomStatus
from app.repositories.room import RoomRepository
from app.repositories.room_type import RoomTypeRepository
from app.schemas.common import Pagination, Sorting, make_page
from app.schemas.room import RoomCreate, RoomUpdate


class RoomService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RoomRepository(db)
        self.room_types = RoomTypeRepository(db)

    def get_many(
        self,
        page: Pagination,
        sort: Sorting,
        *,
        room_type_id: int | None = None,
        status: RoomStatus | None = None,
        floor: int | None = None,
        min_capacity: int | None = None,
        max_price: Decimal | None = None,
        search: str | None = None,
    ) -> dict:
        items, total = self.repo.list_filtered(
            offset=page.offset,
            limit=page.per_page,
            sort_by=sort.sort_by,
            sort_order=sort.sort_order,
            room_type_id=room_type_id,
            status=status,
            floor=floor,
            min_capacity=min_capacity,
            max_price=max_price,
            search=search,
        )
        return make_page(items, total, page)

    def get(self, room_id: int) -> Room:
        room = self.repo.get(room_id)
        if room is None:
            raise NotFoundError(f"Room {room_id} not found")
        return room

    def create(self, data: RoomCreate) -> Room:
        self._ensure_number_free(data.number)
        self._ensure_room_type_exists(data.room_type_id)
        room = self.repo.add(Room(**data.model_dump()))
        self.db.commit()
        return room

    def update(self, room_id: int, data: RoomCreate | RoomUpdate, *, partial: bool) -> Room:
        room = self.get(room_id)
        values = data.model_dump(exclude_unset=partial)
        if "number" in values and values["number"] != room.number:
            self._ensure_number_free(values["number"])
        if "room_type_id" in values:
            self._ensure_room_type_exists(values["room_type_id"])
        for field, value in values.items():
            setattr(room, field, value)
        self.db.commit()
        self.db.refresh(room)
        return room

    def delete(self, room_id: int) -> None:
        room = self.get(room_id)
        if self.repo.has_bookings(room_id):
            raise ConflictError(
                f"Room {room_id} has bookings and cannot be deleted; "
                "set status 'maintenance' to take it out of service"
            )
        self.repo.delete(room)
        self.db.commit()

    def _ensure_number_free(self, number: str) -> None:
        if self.repo.get_by_number(number) is not None:
            raise ConflictError(f"Room number '{number}' already exists", field="number")

    def _ensure_room_type_exists(self, room_type_id: int) -> None:
        if self.room_types.get(room_type_id) is None:
            raise BadRequestError(f"Room type {room_type_id} does not exist", field="room_type_id")
