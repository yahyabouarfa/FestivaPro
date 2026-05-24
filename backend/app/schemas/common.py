from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ApiMessage(BaseModel):
    message: str


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MoneySummary(BaseModel):
    revenue: Decimal
    cost: Decimal
    salaries: Decimal
    profit: Decimal


class DateRange(BaseModel):
    starts_at: datetime
    ends_at: datetime
