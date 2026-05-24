from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import Boolean, Computed, Date, DateTime, ForeignKey, Index, Numeric, String, Time, UniqueConstraint, func
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
    created_events: Mapped[list["Event"]] = relationship(back_populates="creator", foreign_keys="Event.created_by")
    responsible_bars: Mapped[list["Bar"]] = relationship(back_populates="responsible_user", foreign_keys="Bar.responsible_user_id")
    bar_assignments: Mapped[list["BarAssignment"]] = relationship(back_populates="user")
    event_salaries: Mapped[list["EventSalary"]] = relationship(back_populates="user")
    bartender_sales: Mapped[list["BartenderSale"]] = relationship(back_populates="user")


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
    location: Mapped[str] = mapped_column(String(80), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(String(20), index=True, nullable=False, default="upcoming")
    attendance_count: Mapped[int] = mapped_column(default=0, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)

    creator: Mapped[User] = relationship(back_populates="created_events", foreign_keys=[created_by])
    bars: Mapped[list["Bar"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    event_stock: Mapped[list["EventStock"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    event_salaries: Mapped[list["EventSalary"]] = relationship(back_populates="event", cascade="all, delete-orphan")
    bartender_sales: Mapped[list["BartenderSale"]] = relationship(back_populates="event", cascade="all, delete-orphan")


class Bar(Base, TimestampMixin):
    __tablename__ = "bars"
    __table_args__ = (UniqueConstraint("event_id", "name", name="uq_bars_event_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    responsible_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    event: Mapped[Event] = relationship(back_populates="bars")
    responsible_user: Mapped[User] = relationship(back_populates="responsible_bars", foreign_keys=[responsible_user_id])
    stock_items: Mapped[list["BarStock"]] = relationship(back_populates="bar", cascade="all, delete-orphan")
    assignments: Mapped[list["BarAssignment"]] = relationship(back_populates="bar", cascade="all, delete-orphan")
    event_salaries: Mapped[list["EventSalary"]] = relationship(back_populates="bar", cascade="all, delete-orphan")
    bartender_sales: Mapped[list["BartenderSale"]] = relationship(back_populates="bar", cascade="all, delete-orphan")


class BarAssignment(Base):
    __tablename__ = "bar_assignments"
    __table_args__ = (
        UniqueConstraint("bar_id", "user_id", name="uq_bar_assignment_user"),
        Index("ix_bar_assignments_user_bar", "user_id", "bar_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    bar_id: Mapped[int] = mapped_column(ForeignKey("bars.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    bar: Mapped[Bar] = relationship(back_populates="assignments")
    user: Mapped[User] = relationship(back_populates="bar_assignments")


class EventSalary(Base):
    __tablename__ = "event_salaries"
    __table_args__ = (
        Index("ix_event_salaries_event_user_created", "event_id", "user_id", "created_at"),
        Index("ix_event_salaries_event_bar", "event_id", "bar_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    bar_id: Mapped[int] = mapped_column(ForeignKey("bars.id", ondelete="CASCADE"), index=True, nullable=False)
    salary_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    event: Mapped[Event] = relationship(back_populates="event_salaries")
    user: Mapped[User] = relationship(back_populates="event_salaries")
    bar: Mapped[Bar] = relationship(back_populates="event_salaries")


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("name", "category_id", name="uq_products_name_category"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("product_categories.id", ondelete="RESTRICT"), index=True, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    category: Mapped[ProductCategory] = relationship(back_populates="products")
    event_stock: Mapped[list["EventStock"]] = relationship(back_populates="product")


class EventStock(Base):
    __tablename__ = "event_stock"
    __table_args__ = (UniqueConstraint("event_id", "product_id", name="uq_event_stock_product"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), index=True, nullable=False)
    quantity_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    bought_price_per_unit: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    selling_price_per_unit: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    event: Mapped[Event] = relationship(back_populates="event_stock")
    product: Mapped[Product] = relationship(back_populates="event_stock")
    price_history: Mapped[list["PriceHistory"]] = relationship(back_populates="event_stock", cascade="all, delete-orphan")


class BarStock(Base):
    __tablename__ = "bar_stock"
    __table_args__ = (UniqueConstraint("bar_id", "product_id", name="uq_bar_stock_product"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    bar_id: Mapped[int] = mapped_column(ForeignKey("bars.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), index=True, nullable=False)
    quantity_allocated: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity_sold: Mapped[Decimal] = mapped_column(Numeric(10, 2), Computed("quantity_allocated - quantity_remaining"), nullable=False)
    quantity_remaining: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    bar: Mapped[Bar] = relationship(back_populates="stock_items")
    product: Mapped[Product] = relationship()


class BartenderSale(Base):
    __tablename__ = "bartender_sales"
    __table_args__ = (
        UniqueConstraint("event_id", "bar_id", "user_id", name="uq_bartender_sales_event_bar_user"),
        Index("ix_bartender_sales_event_user", "event_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True, nullable=False)
    bar_id: Mapped[int] = mapped_column(ForeignKey("bars.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    units_sold: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    sales_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    contribution_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    event: Mapped[Event] = relationship(back_populates="bartender_sales")
    bar: Mapped[Bar] = relationship(back_populates="bartender_sales")
    user: Mapped[User] = relationship(back_populates="bartender_sales")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_stock_id: Mapped[int] = mapped_column(ForeignKey("event_stock.id", ondelete="CASCADE"), index=True, nullable=False)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), index=True, nullable=False)
    old_selling_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    new_selling_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    changed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    event_stock: Mapped[EventStock] = relationship(back_populates="price_history")
    changed_by: Mapped[User | None] = relationship()
