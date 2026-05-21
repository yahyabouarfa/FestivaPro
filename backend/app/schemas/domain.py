from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from app.schemas.common import ORMModel, Timestamped


class UserRead(Timestamped):
    email: str
    full_name: str
    role: str
    is_active: bool


class EventBase(BaseModel):
    name: str
    slug: str
    venue: str
    city: str = "Casablanca"
    starts_at: datetime
    ends_at: datetime | None = None
    status: str = "planning"
    expected_guests: int = 0
    budget_mad: Decimal = Decimal("0")
    notes: str | None = None


class EventCreate(EventBase): pass
class EventUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    venue: str | None = None
    city: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    status: str | None = None
    expected_guests: int | None = None
    budget_mad: Decimal | None = None
    notes: str | None = None
class EventRead(EventBase, Timestamped): pass


class BarBase(BaseModel):
    event_id: int
    name: str
    location: str
    manager_name: str | None = None
    opening_cash_mad: Decimal = Decimal("0")
    closing_cash_mad: Decimal = Decimal("0")
    status: str = "ready"
class BarCreate(BarBase): pass
class BarUpdate(BaseModel):
    event_id: int | None = None
    name: str | None = None
    location: str | None = None
    manager_name: str | None = None
    opening_cash_mad: Decimal | None = None
    closing_cash_mad: Decimal | None = None
    status: str | None = None
class BarRead(BarBase, Timestamped): pass


class EmployeeBase(BaseModel):
    full_name: str
    phone: str | None = None
    role: str
    daily_rate_mad: Decimal = Decimal("0")
    is_active: bool = True
    emergency_contact: str | None = None
class EmployeeCreate(EmployeeBase): pass
class EmployeeUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    role: str | None = None
    daily_rate_mad: Decimal | None = None
    is_active: bool | None = None
    emergency_contact: str | None = None
class EmployeeRead(EmployeeBase, Timestamped): pass


class StockItemBase(BaseModel):
    event_id: int | None = None
    bar_id: int | None = None
    name: str
    category: str
    unit: str = "bottle"
    opening_quantity: Decimal = Decimal("0")
    current_quantity: Decimal = Decimal("0")
    reorder_level: Decimal = Decimal("0")
    unit_cost_mad: Decimal = Decimal("0")
class StockItemCreate(StockItemBase): pass
class StockItemUpdate(BaseModel):
    event_id: int | None = None
    bar_id: int | None = None
    name: str | None = None
    category: str | None = None
    unit: str | None = None
    opening_quantity: Decimal | None = None
    current_quantity: Decimal | None = None
    reorder_level: Decimal | None = None
    unit_cost_mad: Decimal | None = None
class StockItemRead(StockItemBase, Timestamped): pass


class EquipmentItemBase(BaseModel):
    event_id: int | None = None
    name: str
    category: str
    quantity: int = 0
    condition: str = "good"
    assigned_to: str | None = None
class EquipmentItemCreate(EquipmentItemBase): pass
class EquipmentItemUpdate(BaseModel):
    event_id: int | None = None
    name: str | None = None
    category: str | None = None
    quantity: int | None = None
    condition: str | None = None
    assigned_to: str | None = None
class EquipmentItemRead(EquipmentItemBase, Timestamped): pass


class SalaryBase(BaseModel):
    employee_id: int
    event_id: int | None = None
    amount_mad: Decimal
    status: str = "pending"
    paid_at: datetime | None = None
class SalaryCreate(SalaryBase): pass
class SalaryUpdate(BaseModel):
    employee_id: int | None = None
    event_id: int | None = None
    amount_mad: Decimal | None = None
    status: str | None = None
    paid_at: datetime | None = None
class SalaryRead(SalaryBase, Timestamped): pass


class BartenderContributionBase(BaseModel):
    employee_id: int
    bar_id: int
    sales_mad: Decimal = Decimal("0")
    tips_mad: Decimal = Decimal("0")
    transactions_count: int = 0
class BartenderContributionCreate(BartenderContributionBase): pass
class BartenderContributionUpdate(BaseModel):
    employee_id: int | None = None
    bar_id: int | None = None
    sales_mad: Decimal | None = None
    tips_mad: Decimal | None = None
    transactions_count: int | None = None
class BartenderContributionRead(BartenderContributionBase, Timestamped): pass


class ProfitEntryBase(BaseModel):
    event_id: int
    label: str
    revenue_mad: Decimal = Decimal("0")
    cost_mad: Decimal = Decimal("0")
    notes: str | None = None
class ProfitEntryCreate(ProfitEntryBase): pass
class ProfitEntryUpdate(BaseModel):
    event_id: int | None = None
    label: str | None = None
    revenue_mad: Decimal | None = None
    cost_mad: Decimal | None = None
    notes: str | None = None
class ProfitEntryRead(ProfitEntryBase, Timestamped): pass


class NightLogBase(BaseModel):
    event_id: int
    severity: str = "info"
    title: str
    details: str | None = None
    resolved: bool = False
class NightLogCreate(NightLogBase): pass
class NightLogUpdate(BaseModel):
    event_id: int | None = None
    severity: str | None = None
    title: str | None = None
    details: str | None = None
    resolved: bool | None = None
class NightLogRead(NightLogBase, Timestamped): pass


class ReportBase(BaseModel):
    event_id: int | None = None
    title: str
    report_type: str
    payload_json: dict[str, Any] | None = None
class ReportCreate(ReportBase): pass
class ReportUpdate(BaseModel):
    event_id: int | None = None
    title: str | None = None
    report_type: str | None = None
    payload_json: dict[str, Any] | None = None
class ReportRead(ReportBase, Timestamped): pass


class AuditLogRead(ORMModel):
    id: int
    user_id: int | None = None
    action: str
    entity: str
    entity_id: int | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime


class NotificationBase(BaseModel):
    user_id: int | None = None
    title: str
    message: str
    level: str = "info"
    is_read: bool = False
class NotificationCreate(NotificationBase): pass
class NotificationUpdate(BaseModel):
    title: str | None = None
    message: str | None = None
    level: str | None = None
    is_read: bool | None = None
class NotificationRead(NotificationBase, Timestamped): pass
