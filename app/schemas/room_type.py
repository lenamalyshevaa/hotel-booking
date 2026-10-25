from decimal import Decimal
from typing import Annotated, ClassVar

from pydantic import ConfigDict, Field

from app.schemas.common import PatchSchema, Schema

Name = Annotated[str, Field(min_length=1, max_length=50, examples=["Стандарт"])]
Capacity = Annotated[int, Field(gt=0, le=20, examples=[2])]
Price = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2, examples=["3500.00"])]


class RoomTypeCreate(Schema):
    name: Name
    capacity: Capacity
    price_per_night: Price
    description: str | None = None


class RoomTypeUpdate(PatchSchema):
    nullable_fields: ClassVar[frozenset[str]] = frozenset({"description"})

    name: Name | None = None
    capacity: Capacity | None = None
    price_per_night: Price | None = None
    description: str | None = None


class RoomTypeResponse(Schema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    capacity: int
    price_per_night: Decimal
    description: str | None
