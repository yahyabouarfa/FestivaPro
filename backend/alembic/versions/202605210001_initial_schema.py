"""initial FestivaPro schema

Revision ID: 202605210001
Revises:
Create Date: 2026-05-21
"""

from alembic import op
import sqlalchemy as sa

revision = "202605210001"
down_revision = None
branch_labels = None
depends_on = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(255), nullable=False, unique=True, index=True), sa.Column("full_name", sa.String(255), nullable=False), sa.Column("hashed_password", sa.String(255), nullable=False), sa.Column("role", sa.String(50), nullable=False, server_default="manager"), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), *timestamps())
    op.create_table("events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(255), nullable=False, index=True), sa.Column("slug", sa.String(255), nullable=False, unique=True), sa.Column("venue", sa.String(255), nullable=False), sa.Column("city", sa.String(120), nullable=False, server_default="Casablanca"), sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False), sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True), sa.Column("status", sa.String(50), nullable=False, server_default="planning"), sa.Column("expected_guests", sa.Integer(), nullable=False, server_default="0"), sa.Column("budget_mad", sa.Numeric(12, 2), nullable=False, server_default="0"), sa.Column("notes", sa.Text(), nullable=True), *timestamps())
    op.create_table("bars", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True), sa.Column("name", sa.String(255), nullable=False), sa.Column("location", sa.String(255), nullable=False), sa.Column("manager_name", sa.String(255), nullable=True), sa.Column("opening_cash_mad", sa.Numeric(12, 2), nullable=False, server_default="0"), sa.Column("closing_cash_mad", sa.Numeric(12, 2), nullable=False, server_default="0"), sa.Column("status", sa.String(50), nullable=False, server_default="ready"), *timestamps())
    op.create_table("employees", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("full_name", sa.String(255), nullable=False, index=True), sa.Column("phone", sa.String(80), nullable=True), sa.Column("role", sa.String(80), nullable=False), sa.Column("daily_rate_mad", sa.Numeric(12, 2), nullable=False, server_default="0"), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("emergency_contact", sa.String(255), nullable=True), *timestamps())
    op.create_table("stock_items", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True), sa.Column("bar_id", sa.Integer(), sa.ForeignKey("bars.id", ondelete="SET NULL"), nullable=True, index=True), sa.Column("name", sa.String(255), nullable=False, index=True), sa.Column("category", sa.String(80), nullable=False), sa.Column("unit", sa.String(40), nullable=False, server_default="bottle"), sa.Column("opening_quantity", sa.Numeric(12, 2), nullable=False, server_default="0"), sa.Column("current_quantity", sa.Numeric(12, 2), nullable=False, server_default="0"), sa.Column("reorder_level", sa.Numeric(12, 2), nullable=False, server_default="0"), sa.Column("unit_cost_mad", sa.Numeric(12, 2), nullable=False, server_default="0"), *timestamps())
    op.create_table("equipment_items", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True), sa.Column("name", sa.String(255), nullable=False), sa.Column("category", sa.String(80), nullable=False), sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"), sa.Column("condition", sa.String(80), nullable=False, server_default="good"), sa.Column("assigned_to", sa.String(255), nullable=True), *timestamps())
    op.create_table("salaries", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True), sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True), sa.Column("amount_mad", sa.Numeric(12, 2), nullable=False), sa.Column("status", sa.String(50), nullable=False, server_default="pending"), sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True), *timestamps())
    op.create_table("bartender_contributions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True), sa.Column("bar_id", sa.Integer(), sa.ForeignKey("bars.id", ondelete="CASCADE"), nullable=False, index=True), sa.Column("sales_mad", sa.Numeric(12, 2), nullable=False, server_default="0"), sa.Column("tips_mad", sa.Numeric(12, 2), nullable=False, server_default="0"), sa.Column("transactions_count", sa.Integer(), nullable=False, server_default="0"), *timestamps())
    op.create_table("profit_entries", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True), sa.Column("label", sa.String(255), nullable=False), sa.Column("revenue_mad", sa.Numeric(12, 2), nullable=False, server_default="0"), sa.Column("cost_mad", sa.Numeric(12, 2), nullable=False, server_default="0"), sa.Column("notes", sa.Text(), nullable=True), *timestamps())
    op.create_table("night_logs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True), sa.Column("severity", sa.String(50), nullable=False, server_default="info"), sa.Column("title", sa.String(255), nullable=False), sa.Column("details", sa.Text(), nullable=True), sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.false()), *timestamps())
    op.create_table("reports", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True), sa.Column("title", sa.String(255), nullable=False), sa.Column("report_type", sa.String(80), nullable=False), sa.Column("payload_json", sa.JSON(), nullable=True), *timestamps())
    op.create_table("audit_logs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True), sa.Column("action", sa.String(120), nullable=False), sa.Column("entity", sa.String(120), nullable=False), sa.Column("entity_id", sa.Integer(), nullable=True), sa.Column("metadata_json", sa.JSON(), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("notifications", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True), sa.Column("title", sa.String(255), nullable=False), sa.Column("message", sa.Text(), nullable=False), sa.Column("level", sa.String(50), nullable=False, server_default="info"), sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()), *timestamps())


def downgrade() -> None:
    for table in ("notifications", "audit_logs", "reports", "night_logs", "profit_entries", "bartender_contributions", "salaries", "equipment_items", "stock_items", "employees", "bars", "events", "users"):
        op.drop_table(table)
