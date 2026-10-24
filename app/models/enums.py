import enum


class UserRole(enum.StrEnum):
    guest = "guest"
    admin = "admin"
    manager = "manager"


class BookingStatus(enum.StrEnum):
    pending = "pending"
    confirmed = "confirmed"
    checked_in = "checked_in"
    checked_out = "checked_out"
    cancelled = "cancelled"


# Должен совпадать со списком статусов в триггере миграции 0001.
ACTIVE_BOOKING_STATUSES = (
    BookingStatus.pending,
    BookingStatus.confirmed,
    BookingStatus.checked_in,
)


class RoomStatus(enum.StrEnum):
    available = "available"
    maintenance = "maintenance"


class PaymentMethod(enum.StrEnum):
    cash = "cash"
    card = "card"
    transfer = "transfer"
