"""drilldown cash accountability reports

Revision ID: 202605250004
Revises: 202605250003
Create Date: 2026-05-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202605250004"
down_revision: str | None = "202605250003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def has_table(name: str) -> bool:
        return name in inspector.get_table_names()

    def has_column(table: str, column: str) -> bool:
        return any(existing["name"] == column for existing in inspector.get_columns(table))

    if not has_column("events", "start_date"):
        op.add_column("events", sa.Column("start_date", sa.Date(), nullable=True))
        op.alter_column("events", "start_date", existing_type=sa.Date(), nullable=False)
    op.execute("UPDATE events SET start_date = event_date WHERE start_date IS NULL")
    if not has_column("events", "total_nights_planned"):
        op.add_column("events", sa.Column("total_nights_planned", sa.Integer(), nullable=False, server_default="1"))
    op.execute("UPDATE events SET total_nights_planned = total_nights WHERE total_nights_planned IS NULL OR total_nights_planned = 0")

    if not has_column("event_nights", "created_at"):
        op.add_column("event_nights", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

    if not has_column("bar_night_stock", "qty_used"):
        op.add_column("bar_night_stock", sa.Column("qty_used", sa.Numeric(10, 2), sa.Computed("qty_opening + qty_top_up - COALESCE(qty_closing, 0)"), nullable=False))
    if not has_column("bar_night_stock", "bought_price"):
        op.add_column("bar_night_stock", sa.Column("bought_price", sa.Numeric(10, 2), nullable=False, server_default="0"))
        op.execute(
            """
            UPDATE bar_night_stock bns
            JOIN bars b ON b.id = bns.bar_id
            JOIN event_stock es ON es.event_id = b.event_id AND es.product_id = bns.product_id
            SET bns.bought_price = es.bought_price
            """
        )
    if not has_column("bar_night_stock", "selling_price"):
        op.add_column("bar_night_stock", sa.Column("selling_price", sa.Numeric(10, 2), nullable=False, server_default="0"))
        op.execute(
            """
            UPDATE bar_night_stock bns
            JOIN bars b ON b.id = bns.bar_id
            JOIN event_stock es ON es.event_id = b.event_id AND es.product_id = bns.product_id
            SET bns.selling_price = es.selling_price
            """
        )
    if not has_column("bar_night_stock", "expected_revenue"):
        op.add_column("bar_night_stock", sa.Column("expected_revenue", sa.Numeric(12, 2), sa.Computed("qty_opening * selling_price"), nullable=False))
    if not has_column("bar_night_stock", "expected_cost"):
        op.add_column("bar_night_stock", sa.Column("expected_cost", sa.Numeric(12, 2), sa.Computed("qty_opening * bought_price"), nullable=False))

    if not has_table("night_bar_assignments"):
        op.create_table(
            "night_bar_assignments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("event_night_id", sa.Integer(), nullable=False),
            sa.Column("bar_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("role", sa.String(20), nullable=False),
            sa.Column("salary_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["bar_id"], ["bars.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["event_night_id"], ["event_nights.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("event_night_id", "bar_id", "user_id", "role", name="uq_night_bar_assignment_user_role"),
        )
        op.create_index(op.f("ix_night_bar_assignments_bar_id"), "night_bar_assignments", ["bar_id"], unique=False)
        op.create_index(op.f("ix_night_bar_assignments_event_night_id"), "night_bar_assignments", ["event_night_id"], unique=False)
        op.create_index(op.f("ix_night_bar_assignments_user_id"), "night_bar_assignments", ["user_id"], unique=False)
        op.create_index("ix_night_bar_assignments_night_bar", "night_bar_assignments", ["event_night_id", "bar_id"], unique=False)

    if not has_table("bartender_cash"):
        op.create_table(
            "bartender_cash",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("event_night_id", sa.Integer(), nullable=False),
            sa.Column("bar_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("cash_collected", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["bar_id"], ["bars.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["event_night_id"], ["event_nights.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("event_night_id", "bar_id", "user_id", name="uq_bartender_cash_night_bar_user"),
        )
        op.create_index(op.f("ix_bartender_cash_bar_id"), "bartender_cash", ["bar_id"], unique=False)
        op.create_index(op.f("ix_bartender_cash_event_night_id"), "bartender_cash", ["event_night_id"], unique=False)
        op.create_index(op.f("ix_bartender_cash_user_id"), "bartender_cash", ["user_id"], unique=False)
        op.create_index("ix_bartender_cash_night_bar", "bartender_cash", ["event_night_id", "bar_id"], unique=False)

    if not has_table("bar_night_summary"):
        op.create_table(
            "bar_night_summary",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("bar_id", sa.Integer(), nullable=False),
            sa.Column("event_night_id", sa.Integer(), nullable=False),
            sa.Column("total_cash_collected", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("expected_cash", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("cash_discrepancy", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("stock_cost", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("staff_cost", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("gross_profit", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("net_profit", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("expected_profit", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("is_closed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["bar_id"], ["bars.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["event_night_id"], ["event_nights.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("event_night_id", "bar_id", name="uq_bar_night_summary_night_bar"),
        )
        op.create_index(op.f("ix_bar_night_summary_bar_id"), "bar_night_summary", ["bar_id"], unique=False)
        op.create_index(op.f("ix_bar_night_summary_event_night_id"), "bar_night_summary", ["event_night_id"], unique=False)
        op.create_index("ix_bar_night_summary_night_bar", "bar_night_summary", ["event_night_id", "bar_id"], unique=False)

    if not has_table("pdf_reports"):
        op.create_table(
            "pdf_reports",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("event_id", sa.Integer(), nullable=False),
            sa.Column("event_night_id", sa.Integer(), nullable=True),
            sa.Column("bar_id", sa.Integer(), nullable=True),
            sa.Column("report_type", sa.String(40), nullable=False),
            sa.Column("filename", sa.String(255), nullable=False),
            sa.Column("content_type", sa.String(100), nullable=False, server_default="application/pdf"),
            sa.Column("data", sa.LargeBinary(length=16777216), nullable=False),
            sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["bar_id"], ["bars.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["event_night_id"], ["event_nights.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_pdf_reports_bar_id"), "pdf_reports", ["bar_id"], unique=False)
        op.create_index(op.f("ix_pdf_reports_event_id"), "pdf_reports", ["event_id"], unique=False)
        op.create_index(op.f("ix_pdf_reports_event_night_id"), "pdf_reports", ["event_night_id"], unique=False)
        op.create_index(op.f("ix_pdf_reports_report_type"), "pdf_reports", ["report_type"], unique=False)
        op.create_index("ix_pdf_reports_event_night_type", "pdf_reports", ["event_id", "event_night_id", "report_type"], unique=False)
        op.create_index("ix_pdf_reports_bar_type", "pdf_reports", ["bar_id", "report_type"], unique=False)


def downgrade() -> None:
    op.drop_table("pdf_reports")
    op.drop_table("bar_night_summary")
    op.drop_table("bartender_cash")
    op.drop_table("night_bar_assignments")
    op.drop_column("bar_night_stock", "expected_cost")
    op.drop_column("bar_night_stock", "expected_revenue")
    op.drop_column("bar_night_stock", "selling_price")
    op.drop_column("bar_night_stock", "bought_price")
    op.drop_column("bar_night_stock", "qty_used")
    op.drop_column("event_nights", "created_at")
    op.drop_column("events", "total_nights_planned")
    op.drop_column("events", "start_date")
