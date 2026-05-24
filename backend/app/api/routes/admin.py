from decimal import Decimal
from random import shuffle
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError

from app.api.deps import DbSession, require_admin
from app.core.security import hash_password
from app.models import Bar, BarAssignment, BarStock, Event, EventStock, Product, ProductCategory, User
from app.schemas.common import ApiMessage, MoneySummary
from app.schemas.operations import (
    AssignmentCreate,
    AssignmentRead,
    BarCreate,
    BarRead,
    BarUpdate,
    EventCreate,
    EventRead,
    EventStockRead,
    EventStockUpsert,
    EventUpdate,
    ProductCategoryCreate,
    ProductCategoryRead,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    RandomAssignmentRequest,
    StockRead,
    StockUpsert,
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
def upsert_event_stock(payload: EventStockUpsert, db: DbSession, _: AdminUser):
    get_or_404(db, Event, payload.event_id)
    get_or_404(db, Product, payload.product_id)
    stock = db.query(EventStock).filter(EventStock.event_id == payload.event_id, EventStock.product_id == payload.product_id).first()
    if not stock:
        stock = EventStock(**payload.model_dump())
        db.add(stock)
    else:
        apply_updates(stock, payload)
    commit_or_409(db)
    db.refresh(stock)
    return stock


@router.get("/assignments", response_model=list[AssignmentRead])
def list_assignments(db: DbSession, _: AdminUser, event_id: int | None = None, user_id: int | None = None):
    query = db.query(BarAssignment).join(Bar, Bar.id == BarAssignment.bar_id).order_by(BarAssignment.assigned_at.desc())
    if event_id:
        query = query.filter(Bar.event_id == event_id)
    if user_id:
        query = query.filter(BarAssignment.user_id == user_id)
    return query.all()


@router.post("/assignments", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def create_assignment(payload: AssignmentCreate, db: DbSession, _: AdminUser):
    get_or_404(db, Bar, payload.bar_id)
    require_employee(db, payload.user_id)
    assignment = db.query(BarAssignment).filter(BarAssignment.bar_id == payload.bar_id, BarAssignment.user_id == payload.user_id).first()
    if not assignment:
        assignment = BarAssignment(**payload.model_dump())
        db.add(assignment)
    commit_or_409(db)
    db.refresh(assignment)
    return assignment


@router.post("/assignments/random", response_model=list[AssignmentRead])
def random_assignments(payload: RandomAssignmentRequest, db: DbSession, _: AdminUser):
    get_or_404(db, Event, payload.event_id)
    bars = db.query(Bar).filter(Bar.event_id == payload.event_id).order_by(Bar.name).all()
    employees = db.query(User).filter(User.role == "employee", User.is_active.is_(True)).order_by(User.full_name).all()
    if not bars:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Create at least one bar before random assignment.")
    if not employees:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Create at least one active employee before random assignment.")
    shuffle(employees)
    saved: list[BarAssignment] = []
    for bar_index, bar in enumerate(bars):
        for offset in range(3):
            employee = employees[(bar_index * 3 + offset) % len(employees)]
            assignment = db.query(BarAssignment).filter(BarAssignment.bar_id == bar.id, BarAssignment.user_id == employee.id).first()
            if not assignment:
                assignment = BarAssignment(bar_id=bar.id, user_id=employee.id)
                db.add(assignment)
            saved.append(assignment)
    commit_or_409(db)
    return saved


@router.get("/stock", response_model=list[StockRead])
def list_stock(db: DbSession, _: AdminUser, bar_id: int | None = None):
    query = db.query(BarStock).order_by(BarStock.bar_id, BarStock.product_id)
    if bar_id:
        query = query.filter(BarStock.bar_id == bar_id)
    return query.all()


@router.post("/stock", response_model=StockRead)
def upsert_stock(payload: StockUpsert, db: DbSession, _: AdminUser):
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
    commit_or_409(db)
    db.refresh(stock)
    return stock


@router.get("/reports/summary", response_model=MoneySummary)
def financial_summary(db: DbSession, _: AdminUser, event_id: int):
    row = db.execute(
        text(
            """
            SELECT
              COALESCE(SUM(revenue), 0) AS revenue,
              COALESCE(SUM(cost), 0) AS cost,
              COALESCE(SUM(profit), 0) AS stock_profit
            FROM bar_stock_financials
            WHERE event_id = :event_id
            """
        ),
        {"event_id": event_id},
    ).mappings().one()
    salaries = db.query(func.coalesce(func.count(BarAssignment.id) * 300, 0)).join(Bar, Bar.id == BarAssignment.bar_id).filter(Bar.event_id == event_id).scalar()
    revenue = Decimal(row["revenue"] or 0)
    cost = Decimal(row["cost"] or 0)
    salary_total = Decimal(salaries or 0)
    return MoneySummary(revenue=revenue, cost=cost, salaries=salary_total, profit=Decimal(row["stock_profit"] or 0) - salary_total)
