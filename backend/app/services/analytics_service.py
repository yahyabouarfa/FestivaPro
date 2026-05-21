from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.domain import BartenderContribution, Employee, Event, NightLog, ProfitEntry, StockItem


def money(value: Decimal | None) -> Decimal:
    return value or Decimal("0")


def get_dashboard_summary(db: Session) -> dict:
    events_count = db.scalar(select(func.count(Event.id))) or 0
    employees_count = db.scalar(select(func.count(Employee.id)).where(Employee.is_active.is_(True))) or 0
    revenue = money(db.scalar(select(func.sum(ProfitEntry.revenue_mad))))
    costs = money(db.scalar(select(func.sum(ProfitEntry.cost_mad))))
    bartender_sales = money(db.scalar(select(func.sum(BartenderContribution.sales_mad))))
    profit = revenue + bartender_sales - costs
    revenue_by_event = db.execute(select(Event.name, func.coalesce(func.sum(ProfitEntry.revenue_mad - ProfitEntry.cost_mad), 0).label("profit")).join(ProfitEntry, ProfitEntry.event_id == Event.id, isouter=True).group_by(Event.id).order_by(Event.starts_at.desc()).limit(8)).all()
    stock_alerts = db.execute(select(StockItem.id, StockItem.name, StockItem.category, StockItem.current_quantity, StockItem.reorder_level).where(StockItem.current_quantity <= StockItem.reorder_level).order_by(StockItem.current_quantity.asc()).limit(10)).all()
    night_activity = db.execute(select(NightLog.title, NightLog.severity, NightLog.resolved, NightLog.created_at).order_by(NightLog.created_at.desc()).limit(10)).all()
    return {
        "metrics": [
            {"label": "Events", "value": events_count, "trend": 0},
            {"label": "Active Employees", "value": employees_count, "trend": 0},
            {"label": "Revenue MAD", "value": revenue + bartender_sales, "trend": 0},
            {"label": "Profit MAD", "value": profit, "trend": 0},
        ],
        "revenue_by_event": [{"name": row.name, "profit": row.profit} for row in revenue_by_event],
        "stock_alerts": [{"id": row.id, "name": row.name, "category": row.category, "current_quantity": row.current_quantity, "reorder_level": row.reorder_level} for row in stock_alerts],
        "night_activity": [{"title": row.title, "severity": row.severity, "resolved": row.resolved, "created_at": row.created_at} for row in night_activity],
    }
