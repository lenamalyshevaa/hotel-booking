from typing import Annotated

from pydantic import ConfigDict, Field

from app.models import RoomStatus
from app.schemas.common import PatchSchema, Schema
from app.schemas.room_type import RoomTypeResponse

Number = Annotated[str, Field(min_length=1, max_length=10, examples=["101"])]
Floor = Annotated[int, Field(ge=0, le=200, examples=[1])]


class RoomCreate(Schema):
    number: Number
    floor: Floor
    room_type_id: int
    status: RoomStatus = RoomStatus.available


class RoomUpdate(PatchSchema):
    number: Number | None = None
    floor: Floor | None = None
    room_type_id: int | None = None
    status: RoomStatus | None = None


class RoomResponse(Schema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: str
    floor: int
    status: RoomStatus
    room_type: RoomTypeResponse
