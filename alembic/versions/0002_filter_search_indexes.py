"""Индексы для фильтрации, поиска и отчётов.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-26
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TRGM_INDEXES = (
    ("ix_users_full_name_trgm", "users", "full_name"),
    ("ix_users_email_trgm", "users", "email"),
    ("ix_room_types_name_trgm", "room_types", "name"),
)

BTREE_INDEXES = (
    ("ix_rooms_status", "rooms", "status"),
    ("ix_rooms_floor", "rooms", "floor"),
    ("ix_room_types_price_per_night", "room_types", "price_per_night"),
    ("ix_users_role", "users", "role"),
    ("ix_users_created_at", "users", "created_at"),
    ("ix_payments_paid_at", "payments", "paid_at"),
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    for name, table, column in BTREE_INDEXES:
        op.create_index(name, table, [column])
    for name, table, column in TRGM_INDEXES:
        op.create_index(
            name,
            table,
            [column],
            postgresql_using="gin",
            postgresql_ops={column: "gin_trgm_ops"},
        )


def downgrade() -> None:
    for name, table, _ in TRGM_INDEXES + BTREE_INDEXES:
        op.drop_index(name, table_name=table)
