from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class EventCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    location: str = Field(min_length=2, max_length=80)
    event_date: date
    start_time: time
    end_time: time
    status: str = Field(default="upcoming", pattern="^(upcoming|active|closed)$")


class EventUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    location: str | None = Field(default=None, min_length=2, max_length=80)
    event_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    status: str | None = Field(default=None, pattern="^(upcoming|active|closed)$")


class EventRead(ORMModel):
    id: int
    name: str
    location: str
    event_date: date
    start_time: time
    end_time: time
    status: str
    created_by: int
    created_at: datetime


class BarCreate(BaseModel):
    event_id: int
    name: str = Field(min_length=2, max_length=120)
    responsible_user_id: int


class BarUpdate(BaseModel):
    event_id: int | None = None
    name: str | None = Field(default=None, min_length=2, max_length=120)
    responsible_user_id: int | None = None


class BarRead(ORMModel):
    id: int
    event_id: int
    name: str
    responsible_user_id: int
    created_at: datetime


class ProductCategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)


class ProductCategoryRead(ORMModel):
    id: int
    name: str
    created_at: datetime


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=140)
    category_id: int
    unit: str = Field(default="unit", pattern="^(bottle|can|unit)$")


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=140)
    category_id: int | None = None
    unit: str | None = Field(default=None, pattern="^(bottle|can|unit)$")


class ProductRead(ORMModel):
    id: int
    name: str
    category_id: int
    unit: str
    created_at: datetime


class EventStockUpsert(BaseModel):
    event_id: int
    product_id: int
    quantity_total: Decimal = Field(ge=0)
    bought_price_per_unit: Decimal = Field(ge=0)
    selling_price_per_unit: Decimal = Field(ge=0)


class EventStockRead(ORMModel):
    id: int
    event_id: int
    product_id: int
    quantity_total: Decimal
    bought_price_per_unit: Decimal
    selling_price_per_unit: Decimal
    created_at: datetime


class AssignmentCreate(BaseModel):
    bar_id: int
    user_id: int


class AssignmentRead(ORMModel):
    id: int
    bar_id: int
    user_id: int
    assigned_at: datetime


class RandomAssignmentRequest(BaseModel):
    event_id: int


class StockUpsert(BaseModel):
    bar_id: int
    product_id: int
    quantity_allocated: Decimal = Field(default=0, ge=0)
    quantity_remaining: Decimal = Field(default=0, ge=0)


class StockRead(ORMModel):
    id: int
    bar_id: int
    product_id: int
    quantity_allocated: Decimal
    quantity_sold: Decimal
    quantity_remaining: Decimal
    updated_at: datetime


class EmployeePrice(BaseModel):
    product_id: int
    product_name: str
    category_name: str
    unit: str
    price: Decimal


class EmployeeDashboard(BaseModel):
    assignment: AssignmentRead | None
    bar: BarRead | None
    event: EventRead | None
    prices: list[EmployeePrice]
    contribution: Decimal
