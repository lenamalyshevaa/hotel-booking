from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.models import BookingStatus, RoomStatus


class RoomStatusCount(BaseModel):
    status: RoomStatus
    count: int


class RoomTypeRooms(BaseModel):
    room_type_id: int
    name: str
    price_per_night: Decimal
    rooms: int


class RoomStats(BaseModel):
    total_rooms: int
    avg_price_per_night: Decimal | None
    by_status: list[RoomStatusCount]
    by_room_type: list[RoomTypeRooms]


class BookingStatusStats(BaseModel):
    status: BookingStatus
    count: int
    total_price: Decimal


class BookingStats(BaseModel):
    total_bookings: int
    revenue: Decimal
    avg_booking_price: Decimal | None
    avg_nights: Decimal | None
    by_status: list[BookingStatusStats]


class MonthRevenue(BaseModel):
    month: str
    payments: int
    amount: Decimal


class RevenueReport(BaseModel):
    date_from: date | None
    date_to: date | None
    total_amount: Decimal
    months: list[MonthRevenue]
