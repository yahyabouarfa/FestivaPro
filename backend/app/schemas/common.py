from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Timestamped(ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class DashboardMetric(BaseModel):
    label: str
    value: Decimal | int | float
    trend: float = 0


class DashboardSummary(BaseModel):
    metrics: list[DashboardMetric]
    revenue_by_event: list[dict[str, Any]]
    stock_alerts: list[dict[str, Any]]
    night_activity: list[dict[str, Any]]
