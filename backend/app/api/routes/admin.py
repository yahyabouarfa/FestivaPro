import json
from decimal import Decimal
from random import shuffle
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError

from app.api.deps import DbSession, require_admin
from app.core.security import hash_password
from app.models import (
    AuditLog,
    Bar,
    BarStock,
    BartenderSale,
    Event,
    EventSalary,
    EventStock,
    PriceHistory,
    Product,
    ProductCategory,
    User,
)
from app.schemas.common import ApiMessage, MoneySummary
from app.schemas.operations import (
    AssignmentCreate,
    AssignmentRead,
    AuditLogRead,
    BarCreate,
    BarFinancialSummary,
    BarRead,
    BarUpdate,
    BartenderLeaderboardItem,
    BartenderSaleRead,
    EndOfNightInput,
    EndOfNightResult,
    EventComparisonItem,
    EventCreate,
    EventInsight,
    EventRead,
    EventStockRead,
    EventStockUpsert,
    EventUpdate,
    LowStockAlert,
    PriceHistoryRead,
    ProductCategoryCreate,
    ProductCategoryRead,
    ProductCreate,
    ProductRankingItem,
    ProductRead,
    ProductUpdate,
    RandomAssignmentRequest,
    StockRead,
    StockUpsert,
    WasteItem,
)
from app.schemas.users import UserCreate, UserRead, UserUpdate

AdminUser = Annotated[User, Depends(require_admin)]
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def commit_or_409(db: DbSession) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A record with these unique values already exists.") from exc


def get_or_404(db: DbSession, model: type, record_id: int):
    record = db.get(model, record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} not found.")
    return record


def apply_updates(record, payload) -> None:
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "password":
            setattr(record, "hashed_password", hash_password(value))
        else:
            setattr(record, field, value)


def require_employee(db: DbSession, user_id: int) -> User:
    user = get_or_404(db, User, user_id)
    if user.role != "employee":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only employees can be assigned to bars.")
    return user


def log_audit(db: DbSession, user: User, action: str, entity_type: str, entity_id: int | None, details: dict | None = None) -> None:
    db.add(
        AuditLog(
            user_id=user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=json.dumps(details or {}, default=str),
        )
    )


def latest_assignment_ids(db: DbSession, event_id: int | None = None):
    query = db.query(func.max(EventSalary.id).label("id"))
    if event_id:
        query = query.filter(EventSalary.event_id == event_id)
    return query.group_by(EventSalary.event_id, EventSalary.user_id).subquery()


def current_assignment_query(db: DbSession, event_id: int | None = None, user_id: int | None = None):
    latest = latest_assignment_ids(db, event_id)
    query = db.query(EventSalary).join(latest, EventSalary.id == latest.c.id)
    if event_id:
        query = query.filter(EventSalary.event_id == event_id)
    if user_id:
        query = query.filter(EventSalary.user_id == user_id)
    return query


def validate_assignment(db: DbSession, event_id: int, bar_id: int, user_id: int) -> Bar:
    event = get_or_404(db, Event, event_id)
    if event.status == "closed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Closed events cannot be reassigned.")
    bar = get_or_404(db, Bar, bar_id)
    if bar.event_id != event_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Bar does not belong to the selected event.")
    require_employee(db, user_id)
    return bar


def money(value) -> Decimal:
    return Decimal(value or 0)


def bar_financial_rows(db: DbSession, event_id: int) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT
              b.id AS bar_id,
              b.name AS bar_name,
              COALESCE(stock.gross_revenue, 0) AS gross_revenue,
              COALESCE(stock.total_cost, 0) AS total_cost,
              COALESCE(salary.staff_cost, 0) AS staff_cost,
              COALESCE(stock.gross_revenue, 0) - COALESCE(stock.total_cost, 0) - COALESCE(salary.staff_cost, 0) AS profit
            FROM bars b
            LEFT JOIN (
              SELECT
                bs.bar_id,
                SUM(bs.quantity_sold * es.selling_price_per_unit) AS gross_revenue,
                SUM(bs.quantity_sold * es.bought_price_per_unit) AS total_cost
              FROM bar_stock bs
              JOIN bars sb ON sb.id = bs.bar_id
              JOIN event_stock es ON es.event_id = sb.event_id AND es.product_id = bs.product_id
              WHERE sb.event_id = :event_id
              GROUP BY bs.bar_id
            ) stock ON stock.bar_id = b.id
            LEFT JOIN (
              SELECT cur.bar_id, SUM(cur.salary_amount) AS staff_cost
              FROM event_salaries cur
              JOIN (
                SELECT event_id, user_id, MAX(id) AS id
                FROM event_salaries
                WHERE event_id = :event_id
                GROUP BY event_id, user_id
              ) latest ON latest.id = cur.id
              GROUP BY cur.bar_id
            ) salary ON salary.bar_id = b.id
            WHERE b.event_id = :event_id
            ORDER BY profit DESC, gross_revenue DESC
            """
        ),
        {"event_id": event_id},
    ).mappings().all()
    return [dict(row) for row in rows]


def event_money_summary(db: DbSession, event_id: int) -> MoneySummary:
    rows = bar_financial_rows(db, event_id)
    revenue = sum(money(row["gross_revenue"]) for row in rows)
    cost = sum(money(row["total_cost"]) for row in rows)
    salaries = sum(money(row["staff_cost"]) for row in rows)
    return MoneySummary(revenue=revenue, cost=cost, salaries=salaries, profit=revenue - cost - salaries)


@router.get("/users", response_model=list[UserRead])
def list_users(db: DbSession, _: AdminUser, role: str | None = Query(default=None, pattern="^(admin|employee)$")):
    query = db.query(User).order_by(User.full_name)
    if role:
        query = query.filter(User.role == role)
    return query.all()


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: DbSession, _: AdminUser):
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        phone_number=payload.phone_number,
        role=payload.role,
        hashed_password=hash_password(payload.password),
        is_active=payload.is_active,
    )
    db.add(user)
    commit_or_409(db)
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, db: DbSession, _: AdminUser):
    user = get_or_404(db, User, user_id)
    apply_updates(user, payload)
    commit_or_409(db)
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", response_model=ApiMessage)
def delete_user(user_id: int, db: DbSession, current_user: AdminUser):
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admins cannot delete their own account.")
    db.delete(get_or_404(db, User, user_id))
    commit_or_409(db)
    return ApiMessage(message="User deleted.")


@router.get("/events", response_model=list[EventRead])
def list_events(db: DbSession, _: AdminUser):
    return db.query(Event).order_by(Event.event_date.desc(), Event.start_time.desc()).all()


@router.post("/events", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: DbSession, current_user: AdminUser):
    if payload.end_time == payload.start_time:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Event start and end times cannot be identical.")
    event = Event(**payload.model_dump(), created_by=current_user.id)
    db.add(event)
    commit_or_409(db)
    db.refresh(event)
    return event


@router.patch("/events/{event_id}", response_model=EventRead)
def update_event(event_id: int, payload: EventUpdate, db: DbSession, _: AdminUser):
    event = get_or_404(db, Event, event_id)
    apply_updates(event, payload)
    if event.end_time == event.start_time:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Event start and end times cannot be identical.")
    commit_or_409(db)
    db.refresh(event)
    return event


@router.delete("/events/{event_id}", response_model=ApiMessage)
def delete_event(event_id: int, db: DbSession, _: AdminUser):
    db.delete(get_or_404(db, Event, event_id))
    commit_or_409(db)
    return ApiMessage(message="Event deleted.")


@router.get("/bars", response_model=list[BarRead])
def list_bars(db: DbSession, _: AdminUser, event_id: int | None = None):
    query = db.query(Bar).order_by(Bar.name)
    if event_id:
        query = query.filter(Bar.event_id == event_id)
    return query.all()


@router.post("/bars", response_model=BarRead, status_code=status.HTTP_201_CREATED)
def create_bar(payload: BarCreate, db: DbSession, _: AdminUser):
    get_or_404(db, Event, payload.event_id)
    require_employee(db, payload.responsible_user_id)
    bar = Bar(**payload.model_dump())
    db.add(bar)
    commit_or_409(db)
    db.refresh(bar)
    return bar


@router.patch("/bars/{bar_id}", response_model=BarRead)
def update_bar(bar_id: int, payload: BarUpdate, db: DbSession, _: AdminUser):
    bar = get_or_404(db, Bar, bar_id)
    if payload.event_id:
        get_or_404(db, Event, payload.event_id)
    if payload.responsible_user_id:
        require_employee(db, payload.responsible_user_id)
    apply_updates(bar, payload)
    commit_or_409(db)
    db.refresh(bar)
    return bar


@router.delete("/bars/{bar_id}", response_model=ApiMessage)
def delete_bar(bar_id: int, db: DbSession, _: AdminUser):
    db.delete(get_or_404(db, Bar, bar_id))
    commit_or_409(db)
    return ApiMessage(message="Bar deleted.")


@router.get("/product-categories", response_model=list[ProductCategoryRead])
def list_categories(db: DbSession, _: AdminUser):
    return db.query(ProductCategory).order_by(ProductCategory.name).all()


@router.post("/product-categories", response_model=ProductCategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(payload: ProductCategoryCreate, db: DbSession, _: AdminUser):
    category = ProductCategory(**payload.model_dump())
    db.add(category)
    commit_or_409(db)
    db.refresh(category)
    return category


@router.get("/products", response_model=list[ProductRead])
def list_products(db: DbSession, _: AdminUser):
    return db.query(Product).order_by(Product.name).all()


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: DbSession, _: AdminUser):
    get_or_404(db, ProductCategory, payload.category_id)
    product = Product(**payload.model_dump())
    db.add(product)
    commit_or_409(db)
    db.refresh(product)
    return product


@router.patch("/products/{product_id}", response_model=ProductRead)
def update_product(product_id: int, payload: ProductUpdate, db: DbSession, _: AdminUser):
    product = get_or_404(db, Product, product_id)
    if payload.category_id:
        get_or_404(db, ProductCategory, payload.category_id)
    apply_updates(product, payload)
    commit_or_409(db)
    db.refresh(product)
    return product


@router.delete("/products/{product_id}", response_model=ApiMessage)
def delete_product(product_id: int, db: DbSession, _: AdminUser):
    db.delete(get_or_404(db, Product, product_id))
    commit_or_409(db)
    return ApiMessage(message="Product deleted.")


@router.get("/event-stock", response_model=list[EventStockRead])
def list_event_stock(db: DbSession, _: AdminUser, event_id: int | None = None):
    query = db.query(EventStock).order_by(EventStock.event_id.desc(), EventStock.product_id)
    if event_id:
        query = query.filter(EventStock.event_id == event_id)
    return query.all()


@router.post("/event-stock", response_model=EventStockRead)
def upsert_event_stock(payload: EventStockUpsert, db: DbSession, current_user: AdminUser):
    get_or_404(db, Event, payload.event_id)
    get_or_404(db, Product, payload.product_id)
    stock = db.query(EventStock).filter(EventStock.event_id == payload.event_id, EventStock.product_id == payload.product_id).first()
    if not stock:
        stock = EventStock(**payload.model_dump())
        db.add(stock)
        db.flush()
        db.add(
            PriceHistory(
                event_stock_id=stock.id,
                event_id=stock.event_id,
                product_id=stock.product_id,
                old_selling_price=None,
                new_selling_price=stock.selling_price_per_unit,
                changed_by_id=current_user.id,
            )
        )
        log_audit(db, current_user, "create_price", "event_stock", stock.id, payload.model_dump())
    else:
        old_price = stock.selling_price_per_unit
        apply_updates(stock, payload)
        if old_price != payload.selling_price_per_unit:
            db.add(
                PriceHistory(
                    event_stock_id=stock.id,
                    event_id=stock.event_id,
                    product_id=stock.product_id,
                    old_selling_price=old_price,
                    new_selling_price=payload.selling_price_per_unit,
                    changed_by_id=current_user.id,
                )
            )
        log_audit(db, current_user, "update_price", "event_stock", stock.id, {"old_selling_price": old_price, **payload.model_dump()})
    commit_or_409(db)
    db.refresh(stock)
    return stock


@router.get("/price-history", response_model=list[PriceHistoryRead])
def list_price_history(db: DbSession, _: AdminUser, event_id: int | None = None, product_id: int | None = None):
    query = db.query(PriceHistory).order_by(PriceHistory.changed_at.desc())
    if event_id:
        query = query.filter(PriceHistory.event_id == event_id)
    if product_id:
        query = query.filter(PriceHistory.product_id == product_id)
    return query.all()


@router.get("/audit-logs", response_model=list[AuditLogRead])
def list_audit_logs(db: DbSession, _: AdminUser, limit: int = Query(default=50, ge=1, le=500)):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()


@router.get("/assignments", response_model=list[AssignmentRead])
def list_assignments(db: DbSession, _: AdminUser, event_id: int | None = None, user_id: int | None = None):
    return current_assignment_query(db, event_id=event_id, user_id=user_id).order_by(EventSalary.created_at.desc()).all()


@router.post("/assignments", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def create_assignment(payload: AssignmentCreate, db: DbSession, current_user: AdminUser):
    validate_assignment(db, payload.event_id, payload.bar_id, payload.user_id)
    current = current_assignment_query(db, event_id=payload.event_id, user_id=payload.user_id).first()
    if current and current.bar_id == payload.bar_id and current.salary_amount == payload.salary_amount:
        return current
    assignment = EventSalary(**payload.model_dump())
    db.add(assignment)
    db.flush()
    log_audit(db, current_user, "assign_staff", "event_salaries", assignment.id, payload.model_dump())
    commit_or_409(db)
    db.refresh(assignment)
    return assignment


@router.post("/assignments/random", response_model=list[AssignmentRead])
def random_assignments(payload: RandomAssignmentRequest, db: DbSession, current_user: AdminUser):
    event = get_or_404(db, Event, payload.event_id)
    if event.status == "closed":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Closed events cannot be reassigned.")
    bars = db.query(Bar).filter(Bar.event_id == payload.event_id).order_by(Bar.name).all()
    employees = db.query(User).filter(User.role == "employee", User.is_active.is_(True)).order_by(User.full_name).all()
    if not bars:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Create at least one bar before random assignment.")
    if not employees:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Create at least one active employee before random assignment.")
    shuffle(employees)
    saved: list[EventSalary] = []
    for index, employee in enumerate(employees):
        bar = bars[index % len(bars)]
        current = current_assignment_query(db, event_id=payload.event_id, user_id=employee.id).first()
        if current and current.bar_id == bar.id and current.salary_amount == payload.salary_amount:
            saved.append(current)
            continue
        assignment = EventSalary(event_id=payload.event_id, user_id=employee.id, bar_id=bar.id, salary_amount=payload.salary_amount)
        db.add(assignment)
        saved.append(assignment)
    log_audit(db, current_user, "random_assign_staff", "events", payload.event_id, {"employee_count": len(employees), "bar_count": len(bars)})
    commit_or_409(db)
    return saved


@router.get("/stock", response_model=list[StockRead])
def list_stock(db: DbSession, _: AdminUser, bar_id: int | None = None):
    query = db.query(BarStock).order_by(BarStock.bar_id, BarStock.product_id)
    if bar_id:
        query = query.filter(BarStock.bar_id == bar_id)
    return query.all()


@router.post("/stock", response_model=StockRead)
def upsert_stock(payload: StockUpsert, db: DbSession, current_user: AdminUser):
    bar = get_or_404(db, Bar, payload.bar_id)
    get_or_404(db, Product, payload.product_id)
    event_stock = db.query(EventStock).filter(EventStock.event_id == bar.event_id, EventStock.product_id == payload.product_id).first()
    if not event_stock:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Create event stock for this product before assigning it to a bar.")
    if payload.quantity_remaining > payload.quantity_allocated:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Remaining quantity cannot exceed allocated quantity.")
    stock = db.query(BarStock).filter(BarStock.bar_id == payload.bar_id, BarStock.product_id == payload.product_id).first()
    if not stock:
        stock = BarStock(**payload.model_dump())
        db.add(stock)
    else:
        stock.quantity_allocated = payload.quantity_allocated
        stock.quantity_remaining = payload.quantity_remaining
    db.flush()
    log_audit(db, current_user, "edit_stock", "bar_stock", stock.id, payload.model_dump())
    commit_or_409(db)
    db.refresh(stock)
    return stock


@router.get("/bartender-sales", response_model=list[BartenderSaleRead])
def list_bartender_sales(db: DbSession, _: AdminUser, event_id: int | None = None, bar_id: int | None = None):
    query = db.query(BartenderSale).order_by(BartenderSale.recorded_at.desc())
    if event_id:
        query = query.filter(BartenderSale.event_id == event_id)
    if bar_id:
        query = query.filter(BartenderSale.bar_id == bar_id)
    return query.all()


@router.post("/end-of-night", response_model=EndOfNightResult)
def record_end_of_night(payload: EndOfNightInput, db: DbSession, current_user: AdminUser):
    bar = get_or_404(db, Bar, payload.bar_id)
    if bar.event_id != payload.event_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Bar does not belong to the selected event.")

    updated_stock: list[BarStock] = []
    for item in payload.stock_items:
        stock = db.query(BarStock).filter(BarStock.bar_id == payload.bar_id, BarStock.product_id == item.product_id).first()
        if not stock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Stock not found for product {item.product_id}.")
        if item.quantity_remaining > stock.quantity_allocated:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Remaining quantity cannot exceed allocated quantity.")
        stock.quantity_remaining = item.quantity_remaining
        updated_stock.append(stock)
    log_audit(db, current_user, "end_of_night", "bars", payload.bar_id, {"event_id": payload.event_id, "stock_items": len(payload.stock_items), "bartender_sales": len(payload.bartender_sales)})

    db.flush()
    bar_revenue = next((money(row["gross_revenue"]) for row in bar_financial_rows(db, payload.event_id) if row["bar_id"] == payload.bar_id), Decimal(0))
    total_units = sum(money(stock.quantity_sold) for stock in db.query(BarStock).filter(BarStock.bar_id == payload.bar_id).all())
    average_unit_revenue = (bar_revenue / total_units) if total_units else Decimal(0)

    saved_sales: list[BartenderSale] = []
    for item in payload.bartender_sales:
        current = current_assignment_query(db, event_id=payload.event_id, user_id=item.user_id).first()
        if not current or current.bar_id != payload.bar_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Bartender is not assigned to this bar for this event.")
        sales_amount = item.sales_amount
        if sales_amount is None and item.contribution_pct is not None:
            sales_amount = (bar_revenue * item.contribution_pct / Decimal(100)).quantize(Decimal("0.01"))
        if sales_amount is None:
            sales_amount = (item.units_sold * average_unit_revenue).quantize(Decimal("0.01"))
        contribution_pct = item.contribution_pct
        if contribution_pct is None:
            contribution_pct = ((sales_amount / bar_revenue) * Decimal(100)).quantize(Decimal("0.01")) if bar_revenue else Decimal(0)
        sale = (
            db.query(BartenderSale)
            .filter(BartenderSale.event_id == payload.event_id, BartenderSale.bar_id == payload.bar_id, BartenderSale.user_id == item.user_id)
            .first()
        )
        if not sale:
            sale = BartenderSale(event_id=payload.event_id, bar_id=payload.bar_id, user_id=item.user_id)
            db.add(sale)
        sale.units_sold = item.units_sold
        sale.sales_amount = sales_amount
        sale.contribution_pct = contribution_pct
        saved_sales.append(sale)

    commit_or_409(db)
    for stock in updated_stock:
        db.refresh(stock)
    for sale in saved_sales:
        db.refresh(sale)
    return EndOfNightResult(stock=updated_stock, bartender_sales=saved_sales)


@router.get("/reports/summary", response_model=MoneySummary)
def financial_summary(db: DbSession, _: AdminUser, event_id: int):
    return event_money_summary(db, event_id)


@router.get("/reports/bar-financials", response_model=list[BarFinancialSummary])
def bar_financials(db: DbSession, _: AdminUser, event_id: int):
    return [BarFinancialSummary(**row) for row in bar_financial_rows(db, event_id)]


@router.get("/reports/best-sellers", response_model=list[ProductRankingItem])
def best_sellers(db: DbSession, _: AdminUser, event_id: int, bar_id: int | None = None):
    where_bar = "AND b.id = :bar_id" if bar_id else ""
    group_bar = "b.id, b.name," if bar_id else ""
    select_bar = "b.id AS bar_id, b.name AS bar_name," if bar_id else "NULL AS bar_id, NULL AS bar_name,"
    params = {"event_id": event_id}
    if bar_id:
        params["bar_id"] = bar_id
    rows = db.execute(
        text(
            f"""
            SELECT
              p.id AS product_id,
              p.name AS product_name,
              {select_bar}
              SUM(bs.quantity_sold) AS quantity_sold,
              SUM(bs.quantity_sold * es.selling_price_per_unit) AS revenue
            FROM bar_stock bs
            JOIN bars b ON b.id = bs.bar_id
            JOIN products p ON p.id = bs.product_id
            JOIN event_stock es ON es.event_id = b.event_id AND es.product_id = bs.product_id
            WHERE b.event_id = :event_id {where_bar}
            GROUP BY {group_bar} p.id, p.name
            ORDER BY quantity_sold DESC, revenue DESC
            """
        ),
        params,
    ).mappings().all()
    return [ProductRankingItem(**dict(row)) for row in rows]


@router.get("/reports/low-stock", response_model=list[LowStockAlert])
def low_stock_alerts(db: DbSession, _: AdminUser, event_id: int):
    rows = db.execute(
        text(
            """
            SELECT
              b.id AS bar_id,
              b.name AS bar_name,
              p.id AS product_id,
              p.name AS product_name,
              bs.quantity_allocated,
              bs.quantity_remaining,
              CASE WHEN bs.quantity_allocated = 0 THEN 0 ELSE (bs.quantity_remaining / bs.quantity_allocated) * 100 END AS remaining_pct
            FROM bar_stock bs
            JOIN bars b ON b.id = bs.bar_id
            JOIN products p ON p.id = bs.product_id
            WHERE b.event_id = :event_id
              AND bs.quantity_allocated > 0
              AND bs.quantity_remaining < (bs.quantity_allocated * 0.10)
            ORDER BY remaining_pct ASC, b.name, p.name
            """
        ),
        {"event_id": event_id},
    ).mappings().all()
    return [LowStockAlert(**dict(row)) for row in rows]


@router.get("/reports/waste", response_model=list[WasteItem])
def waste_tracker(db: DbSession, _: AdminUser, event_id: int):
    rows = db.execute(
        text(
            """
            SELECT
              b.id AS bar_id,
              b.name AS bar_name,
              p.id AS product_id,
              p.name AS product_name,
              bs.quantity_remaining,
              bs.quantity_remaining * es.bought_price_per_unit AS estimated_cost
            FROM bar_stock bs
            JOIN bars b ON b.id = bs.bar_id
            JOIN products p ON p.id = bs.product_id
            JOIN event_stock es ON es.event_id = b.event_id AND es.product_id = bs.product_id
            WHERE b.event_id = :event_id AND bs.quantity_remaining > 0
            ORDER BY estimated_cost DESC
            """
        ),
        {"event_id": event_id},
    ).mappings().all()
    return [WasteItem(**dict(row)) for row in rows]


@router.get("/reports/bartender-leaderboard", response_model=list[BartenderLeaderboardItem])
def bartender_leaderboard(db: DbSession, _: AdminUser, event_id: int | None = None):
    rows = db.execute(
        text(
            """
            SELECT
              u.id AS user_id,
              u.full_name,
              COUNT(DISTINCT bs.event_id) AS events_worked,
              COALESCE(SUM(bs.units_sold), 0) AS total_units,
              COALESCE(SUM(bs.sales_amount), 0) AS total_sales
            FROM users u
            JOIN bartender_sales bs ON bs.user_id = u.id
            WHERE (:event_id IS NULL OR bs.event_id = :event_id)
            GROUP BY u.id, u.full_name
            ORDER BY total_sales DESC, total_units DESC
            """
        ),
        {"event_id": event_id},
    ).mappings().all()
    return [BartenderLeaderboardItem(**dict(row)) for row in rows]


@router.get("/reports/event-insights", response_model=EventInsight)
def event_insights(db: DbSession, _: AdminUser, event_id: int):
    summary = event_money_summary(db, event_id)
    bar_rows = [BarFinancialSummary(**row) for row in bar_financial_rows(db, event_id)]
    best = best_sellers(db, _, event_id)
    leaderboard = bartender_leaderboard(db, _, event_id)
    return EventInsight(
        event_id=event_id,
        revenue=summary.revenue,
        cost=summary.cost,
        salaries=summary.salaries,
        profit=summary.profit,
        top_performing_bar=bar_rows[0] if bar_rows else None,
        top_selling_product=best[0] if best else None,
        highest_earning_bartender=leaderboard[0] if leaderboard else None,
        low_stock_alerts=low_stock_alerts(db, _, event_id),
        best_sellers=best,
        waste=waste_tracker(db, _, event_id),
    )


@router.get("/reports/event-comparison", response_model=list[EventComparisonItem])
def event_comparison(db: DbSession, _: AdminUser, event_ids: list[int] | None = Query(default=None)):
    query = db.query(Event).order_by(Event.event_date.desc())
    if event_ids:
        query = query.filter(Event.id.in_(event_ids))
    results: list[EventComparisonItem] = []
    for event in query.all():
        summary = event_money_summary(db, event.id)
        revenue_per_attendee = (summary.revenue / Decimal(event.attendance_count)).quantize(Decimal("0.01")) if event.attendance_count else Decimal(0)
        results.append(
            EventComparisonItem(
                event_id=event.id,
                event_name=event.name,
                event_date=event.event_date,
                attendance_count=event.attendance_count,
                revenue=summary.revenue,
                cost=summary.cost,
                salaries=summary.salaries,
                profit=summary.profit,
                revenue_per_attendee=revenue_per_attendee,
            )
        )
    return results
