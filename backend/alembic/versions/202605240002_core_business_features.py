"""core business features

Revision ID: 202605240002
Revises: 202605240001
Create Date: 2026-05-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202605240002"
down_revision: str | None = "202605240001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("events", sa.Column("attendance_count", sa.Integer(), nullable=False, server_default="0"))

    op.create_table(
        "event_salaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("bar_id", sa.Integer(), nullable=False),
        sa.Column("salary_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["bar_id"], ["bars.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_event_salaries_bar_id"), "event_salaries", ["bar_id"], unique=False)
    op.create_index("ix_event_salaries_event_bar", "event_salaries", ["event_id", "bar_id"], unique=False)
    op.create_index("ix_event_salaries_event_user_created", "event_salaries", ["event_id", "user_id", "created_at"], unique=False)
    op.create_index(op.f("ix_event_salaries_event_id"), "event_salaries", ["event_id"], unique=False)
    op.create_index(op.f("ix_event_salaries_user_id"), "event_salaries", ["user_id"], unique=False)

    op.create_table(
        "bartender_sales",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("bar_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("units_sold", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("sales_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("contribution_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["bar_id"], ["bars.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "bar_id", "user_id", name="uq_bartender_sales_event_bar_user"),
    )
    op.create_index(op.f("ix_bartender_sales_bar_id"), "bartender_sales", ["bar_id"], unique=False)
    op.create_index(op.f("ix_bartender_sales_event_id"), "bartender_sales", ["event_id"], unique=False)
    op.create_index("ix_bartender_sales_event_user", "bartender_sales", ["event_id", "user_id"], unique=False)
    op.create_index(op.f("ix_bartender_sales_user_id"), "bartender_sales", ["user_id"], unique=False)

    op.create_table(
        "price_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_stock_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("old_selling_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("new_selling_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("changed_by_id", sa.Integer(), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["changed_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_stock_id"], ["event_stock.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_price_history_changed_by_id"), "price_history", ["changed_by_id"], unique=False)
    op.create_index(op.f("ix_price_history_event_id"), "price_history", ["event_id"], unique=False)
    op.create_index(op.f("ix_price_history_event_stock_id"), "price_history", ["event_stock_id"], unique=False)
    op.create_index(op.f("ix_price_history_product_id"), "price_history", ["product_id"], unique=False)

    op.execute(
        """
        INSERT INTO event_salaries (event_id, user_id, bar_id, salary_amount, created_at)
        SELECT b.event_id, ba.user_id, ba.bar_id, 300.00, ba.assigned_at
        FROM bar_assignments ba
        JOIN bars b ON b.id = ba.bar_id
        """
    )
    op.execute(
        """
        INSERT INTO price_history (event_stock_id, event_id, product_id, old_selling_price, new_selling_price, changed_by_id, changed_at)
        SELECT id, event_id, product_id, NULL, selling_price_per_unit, NULL, created_at
        FROM event_stock
        """
    )


def downgrade() -> None:
    op.drop_table("price_history")
    op.drop_table("bartender_sales")
    op.drop_table("event_salaries")
    op.drop_column("events", "attendance_count")
