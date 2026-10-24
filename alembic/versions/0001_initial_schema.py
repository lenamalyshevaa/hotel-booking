"""Начальная схема БД HotelBooking.

Revision ID: 0001
Revises:
Create Date: 2026-10-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


user_role = sa.Enum("guest", "admin", "manager", name="user_role", create_type=False)
booking_status = sa.Enum(
    "pending", "confirmed", "checked_in", "checked_out", "cancelled",
    name="booking_status", create_type=False,
)
room_status = sa.Enum("available", "maintenance", name="room_status", create_type=False)
payment_method = sa.Enum("cash", "card", "transfer", name="payment_method", create_type=False)

ENUMS = (user_role, booking_status, room_status, payment_method)


# Триггерная функция синхронизирует даты и «активность» брони в booking_rooms.
#  * BEFORE INSERT/UPDATE на booking_rooms: строка получает даты и статус
#    из своей брони (приложению не нужно их передавать).
#  * AFTER UPDATE на bookings: при смене дат или статуса брони обновляются
#    все её строки, и exclusion constraint проверяет новые значения.
SYNC_FUNCTION = """
CREATE OR REPLACE FUNCTION sync_booking_rooms_dates() RETURNS trigger AS $$
BEGIN
    IF TG_TABLE_NAME = 'booking_rooms' THEN
        SELECT b.check_in, b.check_out,
               b.status IN ('pending', 'confirmed', 'checked_in')
          INTO NEW.check_in, NEW.check_out, NEW.is_active
          FROM bookings b
         WHERE b.id = NEW.booking_id;
        RETURN NEW;
    ELSE
        UPDATE booking_rooms
           SET check_in  = NEW.check_in,
               check_out = NEW.check_out,
               is_active = NEW.status IN ('pending', 'confirmed', 'checked_in')
         WHERE booking_id = NEW.id;
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    # btree_gist позволяет в одном GiST-ограничении сравнивать и целые
    # числа (room_id =), и диапазоны дат (&&). Расширение «доверенное»
    # (trusted), его может включить владелец БД без прав суперпользователя.
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    bind = op.get_bind()
    for enum_type in ENUMS:
        enum_type.create(bind, checkfirst=True)

    # Справочники
    op.create_table(
        "room_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("price_per_night", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.CheckConstraint("capacity > 0", name=op.f("ck_room_types_capacity_positive")),
        sa.CheckConstraint("price_per_night >= 0", name=op.f("ck_room_types_price_non_negative")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_room_types")),
        sa.UniqueConstraint("name", name=op.f("uq_room_types_name")),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("role", user_role, server_default="guest", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )

    # Номерной фонд
    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("number", sa.String(length=10), nullable=False),
        sa.Column("floor", sa.Integer(), nullable=False),
        sa.Column("room_type_id", sa.Integer(), nullable=False),
        sa.Column("status", room_status, server_default="available", nullable=False),
        sa.ForeignKeyConstraint(["room_type_id"], ["room_types.id"], name=op.f("fk_rooms_room_type_id_room_types")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rooms")),
        sa.UniqueConstraint("number", name=op.f("uq_rooms_number")),
    )
    op.create_index(op.f("ix_rooms_room_type_id"), "rooms", ["room_type_id"])

    # Брони
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("guest_id", sa.Integer(), nullable=False),
        sa.Column("check_in", sa.Date(), nullable=False),
        sa.Column("check_out", sa.Date(), nullable=False),
        sa.Column("status", booking_status, server_default="pending", nullable=False),
        sa.Column("total_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("check_out > check_in", name=op.f("ck_bookings_dates_order")),
        sa.CheckConstraint("total_price >= 0", name=op.f("ck_bookings_total_non_negative")),
        sa.ForeignKeyConstraint(["guest_id"], ["users.id"], name=op.f("fk_bookings_guest_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bookings")),
    )
    op.create_index("ix_bookings_check_in_check_out", "bookings", ["check_in", "check_out"])
    op.create_index(op.f("ix_bookings_guest_id"), "bookings", ["guest_id"])
    op.create_index(op.f("ix_bookings_status"), "bookings", ["status"])

    # check_in, check_out, is_active заполняет триггер (см. ниже). NOT NULL
    # проверяется ПОСЛЕ BEFORE-триггера, поэтому приложению их передавать не нужно.
    op.create_table(
        "booking_rooms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("price_per_night", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("check_in", sa.Date(), nullable=False),
        sa.Column("check_out", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.CheckConstraint("price_per_night >= 0", name=op.f("ck_booking_rooms_price_non_negative")),
        sa.ForeignKeyConstraint(
            ["booking_id"], ["bookings.id"],
            name=op.f("fk_booking_rooms_booking_id_bookings"), ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], name=op.f("fk_booking_rooms_room_id_rooms")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_booking_rooms")),
        sa.UniqueConstraint("booking_id", "room_id", name=op.f("uq_booking_rooms_booking_id_room_id")),
    )
    op.create_index(op.f("ix_booking_rooms_booking_id"), "booking_rooms", ["booking_id"])
    op.create_index(op.f("ix_booking_rooms_room_id"), "booking_rooms", ["room_id"])

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("method", payment_method, nullable=False),
        sa.CheckConstraint("amount > 0", name=op.f("ck_payments_amount_positive")),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], name=op.f("fk_payments_booking_id_bookings")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payments")),
    )
    op.create_index(op.f("ix_payments_booking_id"), "payments", ["booking_id"])

    # Защита от двойного бронирования
    op.execute(SYNC_FUNCTION)
    op.execute(
        """
        CREATE TRIGGER trg_booking_rooms_sync
            BEFORE INSERT OR UPDATE ON booking_rooms
            FOR EACH ROW EXECUTE FUNCTION sync_booking_rooms_dates()
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_bookings_sync
            AFTER UPDATE OF check_in, check_out, status ON bookings
            FOR EACH ROW EXECUTE FUNCTION sync_booking_rooms_dates()
        """
    )
    # Для активных строк один и тот же номер (room_id =) не может иметь
    # пересекающиеся (&&) интервалы дат. '[)' — полуоткрытый интервал:
    # [2.11, 5.11) и [5.11, 6.11) не пересекаются, выезд и заезд в один день разрешены.
    op.execute(
        """
        ALTER TABLE booking_rooms
            ADD CONSTRAINT no_overlapping_active_bookings
            EXCLUDE USING gist (
                room_id WITH =,
                daterange(check_in, check_out, '[)') WITH &&
            ) WHERE (is_active)
        """
    )


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("booking_rooms")  # вместе с ограничением и триггером на ней
    op.execute("DROP TRIGGER IF EXISTS trg_bookings_sync ON bookings")
    op.execute("DROP FUNCTION IF EXISTS sync_booking_rooms_dates()")
    op.drop_table("bookings")
    op.drop_table("rooms")
    op.drop_table("users")
    op.drop_table("room_types")

    bind = op.get_bind()
    for enum_type in ENUMS:
        enum_type.drop(bind, checkfirst=True)
