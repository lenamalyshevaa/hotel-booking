import argparse
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.database import SessionLocal
from app.models import (
    Booking,
    BookingRoom,
    BookingStatus,
    Payment,
    PaymentMethod,
    Room,
    RoomStatus,
    RoomType,
    User,
    UserRole,
)

DEMO_PASSWORD = "Password123!"

STAFF = [
    ("manager@hotel.ru", "Ирина Петрова", "+7-900-111-00-01", UserRole.manager),
    ("admin@hotel.ru", "Олег Смирнов", "+7-900-111-00-02", UserRole.admin),
    ("admin2@hotel.ru", "Мария Кузнецова", "+7-900-111-00-03", UserRole.admin),
]

GUESTS = [
    ("ivanov@mail.ru", "Иван Иванов", "+7-900-222-00-01"),
    ("petrova@mail.ru", "Анна Петрова", "+7-900-222-00-02"),
    ("sidorov@mail.ru", "Пётр Сидоров", "+7-900-222-00-03"),
    ("volkova@mail.ru", "Елена Волкова", "+7-900-222-00-04"),
    ("morozov@mail.ru", "Дмитрий Морозов", "+7-900-222-00-05"),
    ("lebedeva@mail.ru", "Ольга Лебедева", "+7-900-222-00-06"),
    ("sokolov@mail.ru", "Алексей Соколов", "+7-900-222-00-07"),
    ("novikova@mail.ru", "Татьяна Новикова", "+7-900-222-00-08"),
    ("kozlov@mail.ru", "Сергей Козлов", "+7-900-222-00-09"),
    ("pavlova@mail.ru", "Наталья Павлова", None),
]

ROOM_TYPES = [
    ("Эконом", 1, "2500.00", "Одноместный номер без вида из окна"),
    ("Стандарт", 2, "3500.00", "Двухместный номер с большой или двумя раздельными кроватями"),
    ("Стандарт плюс", 3, "4500.00", "Увеличенный номер с диваном, до 3 гостей"),
    ("Семейный", 4, "6500.00", "Два смежных помещения, до 4 гостей"),
    ("Люкс", 2, "8000.00", "Номер повышенной комфортности с гостиной зоной"),
    ("Президентский люкс", 4, "15000.00", "Двухкомнатный номер на последнем этаже"),
]

ROOMS = [
    ("101", 1, "Эконом", RoomStatus.available),
    ("102", 1, "Эконом", RoomStatus.available),
    ("103", 1, "Стандарт", RoomStatus.available),
    ("104", 1, "Стандарт", RoomStatus.available),
    ("105", 1, "Стандарт", RoomStatus.available),
    ("201", 2, "Стандарт", RoomStatus.available),
    ("202", 2, "Стандарт", RoomStatus.available),
    ("203", 2, "Стандарт плюс", RoomStatus.available),
    ("204", 2, "Стандарт плюс", RoomStatus.available),
    ("205", 2, "Стандарт плюс", RoomStatus.available),
    ("301", 3, "Семейный", RoomStatus.available),
    ("302", 3, "Семейный", RoomStatus.available),
    ("303", 3, "Стандарт", RoomStatus.available),
    ("304", 3, "Стандарт", RoomStatus.available),
    ("305", 3, "Люкс", RoomStatus.maintenance),
    ("401", 4, "Люкс", RoomStatus.available),
    ("402", 4, "Люкс", RoomStatus.available),
    ("403", 4, "Президентский люкс", RoomStatus.maintenance),
    ("404", 4, "Семейный", RoomStatus.available),
    ("405", 4, "Семейный", RoomStatus.available),
]

BOOKINGS = [
    (4, ["304"], -30, 2, BookingStatus.checked_out, [("1", PaymentMethod.card)]),
    (0, ["101"], -20, 3, BookingStatus.checked_out, [("1", PaymentMethod.card)]),
    (1, ["205"], -15, 2, BookingStatus.checked_out, [("1", PaymentMethod.cash)]),
    (2, ["301"], -10, 4, BookingStatus.cancelled, []),
    (3, ["102"], -2, 5, BookingStatus.checked_in, [("1", PaymentMethod.card)]),
    (4, ["303", "304"], -1, 3, BookingStatus.checked_in,
     [("0.5", PaymentMethod.transfer), ("0.5", PaymentMethod.card)]),
    (5, ["105"], 0, 2, BookingStatus.confirmed, [("1", PaymentMethod.transfer)]),
    (5, ["101"], 2, 3, BookingStatus.confirmed, [("0.5", PaymentMethod.transfer)]),
    (6, ["101"], 5, 1, BookingStatus.confirmed, [("1", PaymentMethod.cash)]),
    (1, ["101"], 3, 2, BookingStatus.cancelled, []),
    (7, ["401"], 3, 4, BookingStatus.pending, []),
    (8, ["202"], 7, 2, BookingStatus.pending, []),
    (9, ["203"], 10, 7, BookingStatus.confirmed, [("1", PaymentMethod.card)]),
    (0, ["402"], 14, 3, BookingStatus.pending, []),
    (2, ["103"], 20, 5, BookingStatus.confirmed, [("0.3", PaymentMethod.card)]),
    (3, ["404", "405"], 25, 4, BookingStatus.pending, []),
]

TABLES = ["payments", "booking_rooms", "bookings", "rooms", "room_types", "users"]


def reset(session: Session) -> None:
    session.execute(text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE"))


def seed(session: Session) -> None:
    staff = [
        User(email=e, full_name=n, phone=p, role=r, password_hash=hash_password(DEMO_PASSWORD))
        for e, n, p, r in STAFF
    ]
    guests = [
        User(
            email=e, full_name=n, phone=p, role=UserRole.guest,
            password_hash=hash_password(DEMO_PASSWORD),
        )
        for e, n, p in GUESTS
    ]
    session.add_all(staff + guests)

    room_types = {
        name: RoomType(name=name, capacity=cap, price_per_night=Decimal(price), description=desc)
        for name, cap, price, desc in ROOM_TYPES
    }
    session.add_all(room_types.values())

    rooms = {
        number: Room(number=number, floor=floor, room_type=room_types[type_name], status=status)
        for number, floor, type_name, status in ROOMS
    }
    session.add_all(rooms.values())

    today = date.today()
    for guest_idx, numbers, offset, nights, status, payments in BOOKINGS:
        check_in = today + timedelta(days=offset)
        booked_rooms = [rooms[n] for n in numbers]
        total = sum(r.room_type.price_per_night for r in booked_rooms) * nights

        booking = Booking(
            guest=guests[guest_idx],
            check_in=check_in,
            check_out=check_in + timedelta(days=nights),
            status=status,
            total_price=total,
            items=[
                BookingRoom(room=r, price_per_night=r.room_type.price_per_night)
                for r in booked_rooms
            ],
        )
        booking.payments = [
            Payment(amount=(total * Decimal(share)).quantize(Decimal("0.01")), method=method)
            for share, method in payments
        ]
        session.add(booking)


def main() -> None:
    parser = argparse.ArgumentParser(description="Тестовые данные HotelBooking")
    parser.add_argument("--reset", action="store_true", help="очистить таблицы перед заполнением")
    args = parser.parse_args()

    with SessionLocal() as session, session.begin():
        if args.reset:
            reset(session)
        elif session.scalar(select(func.count()).select_from(User)):
            print("В БД уже есть данные. Для перезаполнения: python -m app.seed --reset")
            return
        seed(session)

    with SessionLocal() as session:
        print("Тестовые данные загружены:")
        for table in TABLES[::-1]:
            count = session.scalar(text(f"SELECT count(*) FROM {table}"))
            print(f"  {table:<14} {count}")
        print(f"Пароль всех пользователей: {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
