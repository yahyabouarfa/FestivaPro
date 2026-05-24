from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class EventCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    location: str | None = Field(default=None, max_length=255)
    starts_at: datetime
    ends_at: datetime
    is_active: bool = True


class EventUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    location: str | None = Field(default=None, max_length=255)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    is_active: bool | None = None


class EventRead(ORMModel):
    id: int
    name: str
    location: str | None
    starts_at: datetime
    ends_at: datetime
    is_active: bool
    created_at: datetime


class BarCreate(BaseModel):
    event_id: int
    name: str = Field(min_length=2, max_length=120)
    location: str | None = Field(default=None, max_length=255)
    starting_cash: Decimal = Field(default=0, ge=0)


class BarUpdate(BaseModel):
    event_id: int | None = None
    name: str | None = Field(default=None, min_length=2, max_length=120)
    location: str | None = Field(default=None, max_length=255)
    starting_cash: Decimal | None = Field(default=None, ge=0)


class BarRead(ORMModel):
    id: int
    event_id: int
    name: str
    location: str | None
    starting_cash: Decimal
    created_at: datetime


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=140)
    sku: str = Field(min_length=2, max_length=80)
    unit: str = Field(default="unit", max_length=40)
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=140)
    sku: str | None = Field(default=None, min_length=2, max_length=80)
    unit: str | None = Field(default=None, max_length=40)
    is_active: bool | None = None


class ProductRead(ORMModel):
    id: int
    name: str
    sku: str
    unit: str
    is_active: bool
    created_at: datetime


class PriceUpsert(BaseModel):
    event_id: int
    product_id: int
    price: Decimal = Field(ge=0)
    cost_price: Decimal = Field(default=0, ge=0)


class PriceRead(ORMModel):
    id: int
    event_id: int
    product_id: int
    price: Decimal
    cost_price: Decimal
    created_at: datetime


class AssignmentCreate(BaseModel):
    event_id: int
    bar_id: int
    user_id: int
    shift_salary: Decimal = Field(default=0, ge=0)


class AssignmentRead(ORMModel):
    id: int
    event_id: int
    bar_id: int
    user_id: int
    shift_salary: Decimal
    created_at: datetime


class RandomAssignmentRequest(BaseModel):
    event_id: int
    shift_salary: Decimal = Field(default=0, ge=0)


class StockUpsert(BaseModel):
    bar_id: int
    product_id: int
    opening_quantity: Decimal = Field(default=0, ge=0)
    current_quantity: Decimal = Field(default=0, ge=0)


class StockRead(ORMModel):
    id: int
    bar_id: int
    product_id: int
    opening_quantity: Decimal
    current_quantity: Decimal
    created_at: datetime


class StockMovementCreate(BaseModel):
    bar_id: int
    product_id: int
    quantity_change: Decimal
    reason: str = Field(max_length=60)
    note: str | None = None


class StockMovementRead(ORMModel):
    id: int
    bar_id: int
    product_id: int
    created_by_id: int | None
    quantity_change: Decimal
    reason: str
    note: str | None
    created_at: datetime


class SaleCreate(BaseModel):
    event_id: int
    bar_id: int
    product_id: int
    employee_id: int
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class SaleRead(ORMModel):
    id: int
    event_id: int
    bar_id: int
    product_id: int
    employee_id: int
    quantity: Decimal
    unit_price: Decimal
    created_at: datetime


class EmployeePrice(BaseModel):
    product_id: int
    product_name: str
    sku: str
    unit: str
    price: Decimal


class EmployeeDashboard(BaseModel):
    assignment: AssignmentRead | None
    bar: BarRead | None
    event: EventRead | None
    prices: list[EmployeePrice]
    contribution: Decimal
