"""night based event lifecycle

Revision ID: 202605250003
Revises: 202605240002
Create Date: 2026-05-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202605250003"
down_revision: str | None = "202605240002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def has_table(name: str) -> bool:
        return name in inspector.get_table_names()

    def has_column(table: str, column: str) -> bool:
        return any(existing["name"] == column for existing in inspector.get_columns(table))

    if not has_column("events", "total_nights"):
        op.add_column("events", sa.Column("total_nights", sa.Integer(), nullable=False, server_default="1"))

    if not has_column("event_stock", "total_qty_purchased"):
        op.add_column("event_stock", sa.Column("total_qty_purchased", sa.Numeric(10, 2), nullable=False, server_default="0"))
        if has_column("event_stock", "quantity_total"):
            op.execute("UPDATE event_stock SET total_qty_purchased = quantity_total")
    if not has_column("event_stock", "bought_price"):
        op.add_column("event_stock", sa.Column("bought_price", sa.Numeric(10, 2), nullable=False, server_default="0"))
        if has_column("event_stock", "bought_price_per_unit"):
            op.execute("UPDATE event_stock SET bought_price = bought_price_per_unit")
    if not has_column("event_stock", "selling_price"):
        op.add_column("event_stock", sa.Column("selling_price", sa.Numeric(10, 2), nullable=False, server_default="0"))
        if has_column("event_stock", "selling_price_per_unit"):
            op.execute("UPDATE event_stock SET selling_price = selling_price_per_unit")

    if not has_table("event_nights"):
        op.create_table(
            "event_nights",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("event_id", sa.Integer(), nullable=False),
            sa.Column("night_number", sa.Integer(), nullable=False),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="upcoming"),
            sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("event_id", "night_number", name="uq_event_nights_event_number"),
        )
        op.create_index(op.f("ix_event_nights_event_id"), "event_nights", ["event_id"], unique=False)
        op.create_index(op.f("ix_event_nights_status"), "event_nights", ["status"], unique=False)
        op.create_index("ix_event_nights_event_status", "event_nights", ["event_id", "status"], unique=False)
        op.execute(
            """
            INSERT INTO event_nights (event_id, night_number, date, status)
            SELECT id, 1, event_date, status
            FROM events
            """
        )

    if not has_table("bar_night_stock"):
        op.create_table(
            "bar_night_stock",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("bar_id", sa.Integer(), nullable=False),
            sa.Column("event_night_id", sa.Integer(), nullable=False),
            sa.Column("product_id", sa.Integer(), nullable=False),
            sa.Column("qty_opening", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("qty_top_up", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("qty_closing", sa.Numeric(10, 2), nullable=True),
            sa.Column("qty_sold", sa.Numeric(10, 2), sa.Computed("qty_opening + qty_top_up - COALESCE(qty_closing, 0)"), nullable=False),
            sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["bar_id"], ["bars.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["event_night_id"], ["event_nights.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("bar_id", "event_night_id", "product_id", name="uq_bar_night_stock_product"),
        )
        op.create_index(op.f("ix_bar_night_stock_bar_id"), "bar_night_stock", ["bar_id"], unique=False)
        op.create_index(op.f("ix_bar_night_stock_event_night_id"), "bar_night_stock", ["event_night_id"], unique=False)
        op.create_index(op.f("ix_bar_night_stock_product_id"), "bar_night_stock", ["product_id"], unique=False)
        op.create_index("ix_bar_night_stock_night_bar", "bar_night_stock", ["event_night_id", "bar_id"], unique=False)
        if has_table("bar_stock"):
            op.execute(
                """
                INSERT INTO bar_night_stock (bar_id, event_night_id, product_id, qty_opening, qty_top_up, qty_closing, is_locked, updated_at)
                SELECT bs.bar_id, en.id, bs.product_id, bs.quantity_allocated, 0, bs.quantity_remaining, 0, bs.updated_at
                FROM bar_stock bs
                JOIN bars b ON b.id = bs.bar_id
                JOIN event_nights en ON en.event_id = b.event_id AND en.night_number = 1
                """
            )

    if not has_table("profit_snapshots"):
        op.create_table(
            "profit_snapshots",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("event_id", sa.Integer(), nullable=False),
            sa.Column("event_night_id", sa.Integer(), nullable=True),
            sa.Column("bar_id", sa.Integer(), nullable=True),
            sa.Column("expected_revenue", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("actual_revenue", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("expected_profit", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("actual_profit", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("staff_cost", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("net_profit", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("snapshot_level", sa.String(20), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["bar_id"], ["bars.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["event_night_id"], ["event_nights.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_profit_snapshots_bar_id"), "profit_snapshots", ["bar_id"], unique=False)
        op.create_index(op.f("ix_profit_snapshots_event_id"), "profit_snapshots", ["event_id"], unique=False)
        op.create_index(op.f("ix_profit_snapshots_event_night_id"), "profit_snapshots", ["event_night_id"], unique=False)
        op.create_index(op.f("ix_profit_snapshots_snapshot_level"), "profit_snapshots", ["snapshot_level"], unique=False)
        op.create_index("ix_profit_snapshots_event_level", "profit_snapshots", ["event_id", "snapshot_level"], unique=False)
        op.create_index("ix_profit_snapshots_night_bar", "profit_snapshots", ["event_night_id", "bar_id"], unique=False)


def downgrade() -> None:
    op.drop_table("profit_snapshots")
    op.drop_table("bar_night_stock")
    op.drop_table("event_nights")
    op.drop_column("event_stock", "selling_price")
    op.drop_column("event_stock", "bought_price")
    op.drop_column("event_stock", "total_qty_purchased")
    op.drop_column("events", "total_nights")
