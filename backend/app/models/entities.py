from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(40))
    role: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    assignments: Mapped[list["StaffAssignment"]] = relationship(back_populates="user")


class RefreshToken(Base, TimestampMixin):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class Event(Base, TimestampMixin):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    bars: Mapped[list["Bar"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    prices: Mapped[list["EventProductPrice"]] = relationship(back_populates="event", cascade="all, delete-orphan")


class Bar(Base, TimestampMixin):
    __tablename__ = "bars"
    __table_args__ = (UniqueConstraint("event_id", "name", name="uq_bars_event_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    starting_cash: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)

    event: Mapped[Event] = relationship(back_populates="bars")
    stock_items: Mapped[list["BarStock"]] = relationship(back_populates="bar", cascade="all, delete-orphan")
    assignments: Mapped[list["StaffAssignment"]] = relationship(back_populates="bar")


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    sku: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    unit: Mapped[str] = mapped_column(String(40), default="unit", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    prices: Mapped[list["EventProductPrice"]] = relationship(back_populates="product")


class EventProductPrice(Base, TimestampMixin):
    __tablename__ = "event_product_prices"
    __table_args__ = (UniqueConstraint("event_id", "product_id", name="uq_event_product_price"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)

    event: Mapped[Event] = relationship(back_populates="prices")
    product: Mapped[Product] = relationship(back_populates="prices")


class StaffAssignment(Base, TimestampMixin):
    __tablename__ = "staff_assignments"
    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_assignment_event_user"),
        Index("ix_assignment_user_bar", "user_id", "bar_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True, nullable=False)
    bar_id: Mapped[int] = mapped_column(ForeignKey("bars.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    shift_salary: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)

    event: Mapped[Event] = relationship()
    bar: Mapped[Bar] = relationship(back_populates="assignments")
    user: Mapped[User] = relationship(back_populates="assignments")


class BarStock(Base, TimestampMixin):
    __tablename__ = "bar_stock"
    __table_args__ = (UniqueConstraint("bar_id", "product_id", name="uq_bar_stock_product"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    bar_id: Mapped[int] = mapped_column(ForeignKey("bars.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False)
    opening_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    current_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)

    bar: Mapped[Bar] = relationship(back_populates="stock_items")
    product: Mapped[Product] = relationship()


class StockMovement(Base, TimestampMixin):
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    bar_id: Mapped[int] = mapped_column(ForeignKey("bars.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    quantity_change: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    reason: Mapped[str] = mapped_column(String(60), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)

    bar: Mapped[Bar] = relationship()
    product: Mapped[Product] = relationship()
    created_by: Mapped[User | None] = relationship()


class Sale(Base, TimestampMixin):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True, nullable=False)
    bar_id: Mapped[int] = mapped_column(ForeignKey("bars.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), index=True, nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    event: Mapped[Event] = relationship()
    bar: Mapped[Bar] = relationship()
    product: Mapped[Product] = relationship()
    employee: Mapped[User] = relationship()
