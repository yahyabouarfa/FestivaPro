from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class EventCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    location: str = Field(min_length=2, max_length=80)
    start_date: date
    total_nights_planned: int = Field(default=1, ge=1, le=30)
    status: str = Field(default="upcoming", pattern="^(upcoming|active|closed)$")
    attendance_count: int = Field(default=0, ge=0)
    start_time: time = time(18, 0)
    end_time: time = time(2, 0)


class EventUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    location: str | None = Field(default=None, min_length=2, max_length=80)
    start_date: date | None = None
    total_nights_planned: int | None = Field(default=None, ge=1, le=30)
    status: str | None = Field(default=None, pattern="^(upcoming|active|closed)$")
    attendance_count: int | None = Field(default=None, ge=0)
    start_time: time | None = None
    end_time: time | None = None


class EventRead(ORMModel):
    id: int
    name: str
    location: str
    start_date: date
    event_date: date
    start_time: time
    end_time: time
    total_nights: int
    total_nights_planned: int
    status: str
    attendance_count: int
    created_by: int
    created_at: datetime


class BeginNightInput(BaseModel):
    event_id: int
    date: date


class EventNightRead(ORMModel):
    id: int
    event_id: int
    night_number: int
    date: date
    status: str
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
    total_qty_purchased: Decimal = Field(ge=0)
    bought_price: Decimal = Field(ge=0)
    selling_price: Decimal = Field(ge=0)


class EventStockRead(ORMModel):
    id: int
    event_id: int
    product_id: int
    total_qty_purchased: Decimal
    bought_price: Decimal
    selling_price: Decimal
    created_at: datetime


class EventStockBalance(BaseModel):
    event_id: int
    product_id: int
    total_qty_purchased: Decimal
    allocated_to_bars: Decimal
    available: Decimal


class AssignmentCreate(BaseModel):
    event_id: int
    bar_id: int
    user_id: int
    salary_amount: Decimal = Field(default=0, ge=0)


class AssignmentRead(ORMModel):
    id: int
    event_id: int
    bar_id: int
    user_id: int
    salary_amount: Decimal
    created_at: datetime


class RandomAssignmentRequest(BaseModel):
    event_id: int
    salary_amount: Decimal = Field(default=0, ge=0)


class NightAssignmentItem(BaseModel):
    user_id: int
    role: str = Field(pattern="^(responsible|bartender)$")
    salary_amount: Decimal = Field(default=0, ge=0)


class NightAssignmentInput(BaseModel):
    event_night_id: int
    bar_id: int
    assignments: list[NightAssignmentItem]


class RandomBarNightAssignmentRequest(BaseModel):
    event_night_id: int
    bar_id: int
    employee_count: int = Field(ge=1, le=100)
    salary_amount: Decimal = Field(default=0, ge=0)


class NightBarAssignmentRead(ORMModel):
    id: int
    event_night_id: int
    bar_id: int
    user_id: int
    role: str
    salary_amount: Decimal
    assigned_at: datetime


class OpeningStockItem(BaseModel):
    product_id: int
    qty_opening: Decimal = Field(default=0, ge=0)
    qty_top_up: Decimal = Field(default=0, ge=0)
    bought_price: Decimal = Field(default=0, ge=0)
    selling_price: Decimal = Field(default=0, ge=0)


class OpeningStockInput(BaseModel):
    event_night_id: int
    bar_id: int
    items: list[OpeningStockItem]


class BarNightStockRead(ORMModel):
    id: int
    bar_id: int
    event_night_id: int
    product_id: int
    qty_opening: Decimal
    qty_top_up: Decimal
    qty_closing: Decimal | None
    qty_sold: Decimal
    qty_used: Decimal
    bought_price: Decimal
    selling_price: Decimal
    expected_revenue: Decimal
    expected_cost: Decimal
    is_locked: bool
    updated_at: datetime


class EndOfNightStockItem(BaseModel):
    product_id: int
    qty_closing: Decimal = Field(ge=0)


class BartenderCashInput(BaseModel):
    user_id: int
    cash_collected: Decimal = Field(default=0, ge=0)


class BartenderSaleInput(BaseModel):
    user_id: int
    units_sold: Decimal = Field(default=0, ge=0)
    sales_amount: Decimal | None = Field(default=None, ge=0)
    contribution_pct: Decimal | None = Field(default=None, ge=0, le=100)


class EndOfNightInput(BaseModel):
    event_night_id: int
    bar_id: int
    stock_items: list[EndOfNightStockItem]
    bartender_cash: list[BartenderCashInput] = Field(default_factory=list)
    bartender_sales: list[BartenderSaleInput] = Field(default_factory=list)


class BartenderCashRead(ORMModel):
    id: int
    event_night_id: int
    bar_id: int
    user_id: int
    cash_collected: Decimal
    recorded_at: datetime


class BartenderSaleRead(ORMModel):
    id: int
    event_id: int
    bar_id: int
    user_id: int
    units_sold: Decimal
    sales_amount: Decimal
    contribution_pct: Decimal
    recorded_at: datetime


class BarNightSummaryRead(ORMModel):
    id: int
    bar_id: int
    event_night_id: int
    total_cash_collected: Decimal
    expected_cash: Decimal
    cash_discrepancy: Decimal
    stock_cost: Decimal
    staff_cost: Decimal
    gross_profit: Decimal
    net_profit: Decimal
    expected_profit: Decimal
    is_closed: bool
    closed_at: datetime | None


class EndOfNightResult(BaseModel):
    stock: list[BarNightStockRead]
    bartender_cash: list[BartenderCashRead]
    summary: BarNightSummaryRead


class ProfitSnapshotRead(ORMModel):
    id: int
    event_id: int
    event_night_id: int | None
    bar_id: int | None
    expected_revenue: Decimal
    actual_revenue: Decimal
    expected_profit: Decimal
    actual_profit: Decimal
    staff_cost: Decimal
    net_profit: Decimal
    snapshot_level: str
    created_at: datetime


class PdfReportRead(ORMModel):
    id: int
    event_id: int
    event_night_id: int | None
    bar_id: int | None
    report_type: str
    filename: str
    content_type: str
    generated_at: datetime


class BarFinancialSummary(BaseModel):
    bar_id: int
    bar_name: str
    gross_revenue: Decimal
    total_cost: Decimal
    staff_cost: Decimal
    profit: Decimal


class ProductRankingItem(BaseModel):
    product_id: int
    product_name: str
    bar_id: int | None = None
    bar_name: str | None = None
    quantity_sold: Decimal
    revenue: Decimal


class LowStockAlert(BaseModel):
    bar_id: int
    bar_name: str
    product_id: int
    product_name: str
    quantity_allocated: Decimal
    quantity_remaining: Decimal
    remaining_pct: Decimal


class WasteItem(BaseModel):
    bar_id: int
    bar_name: str
    product_id: int
    product_name: str
    quantity_remaining: Decimal
    estimated_cost: Decimal


class BartenderLeaderboardItem(BaseModel):
    user_id: int
    full_name: str
    events_worked: int
    total_units: Decimal
    total_sales: Decimal


class PriceHistoryRead(ORMModel):
    id: int
    event_stock_id: int
    event_id: int
    product_id: int
    old_selling_price: Decimal | None
    new_selling_price: Decimal
    changed_by_id: int | None
    changed_at: datetime


class AuditLogRead(ORMModel):
    id: int
    user_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    details: str | None
    created_at: datetime


class EventInsight(BaseModel):
    event_id: int
    revenue: Decimal
    cost: Decimal
    salaries: Decimal
    profit: Decimal
    top_performing_bar: BarFinancialSummary | None
    top_selling_product: ProductRankingItem | None
    highest_earning_bartender: BartenderLeaderboardItem | None
    low_stock_alerts: list[LowStockAlert]
    best_sellers: list[ProductRankingItem]
    waste: list[WasteItem]


class EventComparisonItem(BaseModel):
    event_id: int
    event_name: str
    event_date: date
    attendance_count: int
    revenue: Decimal
    cost: Decimal
    salaries: Decimal
    profit: Decimal
    revenue_per_attendee: Decimal


class EmployeePrice(BaseModel):
    product_id: int
    product_name: str
    category_name: str
    unit: str
    price: Decimal


class EmployeeDashboard(BaseModel):
    assignment: NightBarAssignmentRead | AssignmentRead | None
    bar: BarRead | None
    event: EventRead | None
    responsible_person: str | None = None
    prices: list[EmployeePrice]
    contribution: Decimal
    units_sold: Decimal = Decimal(0)
    contribution_pct: Decimal = Decimal(0)
    reassignment_notice: str | None = None
