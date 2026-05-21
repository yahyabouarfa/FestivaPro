from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="manager")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Event(Base, TimestampMixin):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    venue: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(120), default="Casablanca")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="planning")
    expected_guests: Mapped[int] = mapped_column(Integer, default=0)
    budget_mad: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    bars = relationship("Bar", back_populates="event", cascade="all, delete")


class Bar(Base, TimestampMixin):
    __tablename__ = "bars"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255))
    manager_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    opening_cash_mad: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    closing_cash_mad: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    status: Mapped[str] = mapped_column(String(50), default="ready")
    event = relationship("Event", back_populates="bars")


class Employee(Base, TimestampMixin):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    role: Mapped[str] = mapped_column(String(80))
    daily_rate_mad: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    emergency_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)


class StockItem(Base, TimestampMixin):
    __tablename__ = "stock_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True)
    bar_id: Mapped[int | None] = mapped_column(ForeignKey("bars.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(80))
    unit: Mapped[str] = mapped_column(String(40), default="bottle")
    opening_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    current_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    reorder_level: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    unit_cost_mad: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)


class EquipmentItem(Base, TimestampMixin):
    __tablename__ = "equipment_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(80))
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    condition: Mapped[str] = mapped_column(String(80), default="good")
    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Salary(Base, TimestampMixin):
    __tablename__ = "salaries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True)
    amount_mad: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BartenderContribution(Base, TimestampMixin):
    __tablename__ = "bartender_contributions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="CASCADE"), index=True)
    bar_id: Mapped[int] = mapped_column(ForeignKey("bars.id", ondelete="CASCADE"), index=True)
    sales_mad: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    tips_mad: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    transactions_count: Mapped[int] = mapped_column(Integer, default=0)


class ProfitEntry(Base, TimestampMixin):
    __tablename__ = "profit_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(255))
    revenue_mad: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    cost_mad: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class NightLog(Base, TimestampMixin):
    __tablename__ = "night_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    severity: Mapped[str] = mapped_column(String(50), default="info")
    title: Mapped[str] = mapped_column(String(255))
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)


class Report(Base, TimestampMixin):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    report_type: Mapped[str] = mapped_column(String(80))
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(120))
    entity: Mapped[str] = mapped_column(String(120))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String(50), default="info")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
