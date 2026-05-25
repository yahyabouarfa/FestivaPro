"""make legacy event stock columns compatible

Revision ID: 202605250005
Revises: 202605250004
Create Date: 2026-05-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202605250005"
down_revision: str | None = "202605250004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"]: column for column in inspector.get_columns("event_stock")}

    if "quantity_total" in columns:
        op.alter_column(
            "event_stock",
            "quantity_total",
            existing_type=sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        )
    if "bought_price_per_unit" in columns:
        op.alter_column(
            "event_stock",
            "bought_price_per_unit",
            existing_type=sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        )
    if "selling_price_per_unit" in columns:
        op.alter_column(
            "event_stock",
            "selling_price_per_unit",
            existing_type=sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"]: column for column in inspector.get_columns("event_stock")}

    if "quantity_total" in columns:
        op.alter_column("event_stock", "quantity_total", existing_type=sa.Numeric(10, 2), server_default=None)
    if "bought_price_per_unit" in columns:
        op.alter_column("event_stock", "bought_price_per_unit", existing_type=sa.Numeric(10, 2), server_default=None)
    if "selling_price_per_unit" in columns:
        op.alter_column("event_stock", "selling_price_per_unit", existing_type=sa.Numeric(10, 2), server_default=None)
