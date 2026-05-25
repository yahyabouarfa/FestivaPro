import json
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from app.api.routes.admin import generate_bar_pdf, generate_event_pdf, generate_night_pdf, snapshot_bar, snapshot_event
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import (
    AuditLog,
    Bar,
    BarAssignment,
    BarNightStock,
    BarNightSummary,
    BartenderCash,
    BartenderSale,
    Event,
    EventNight,
    EventSalary,
    EventStock,
    NightBarAssignment,
    PdfReport,
    PriceHistory,
    Product,
    ProductCategory,
    User,
)


SEED_PASSWORD = "password"
SEED_EVENT_NAMES = [
    "Mawazine Lounge 2025",
    "Casa Beach Festival 2025",
    "Atlas Night Market 2024",
]

EMPLOYEES = [
    ("Yassine Amrani", "seed.yassine@festivapro.local", "+212 661 100 101"),
    ("Sara Benali", "seed.sara@festivapro.local", "+212 662 100 102"),
    ("Mehdi El Fassi", "seed.mehdi@festivapro.local", "+212 663 100 103"),
    ("Nora Berrada", "seed.nora@festivapro.local", "+212 664 100 104"),
    ("Omar Idrissi", "seed.omar@festivapro.local", "+212 665 100 105"),
    ("Imane Alaoui", "seed.imane@festivapro.local", "+212 666 100 106"),
    ("Karim Tazi", "seed.karim@festivapro.local", "+212 667 100 107"),
    ("Lina Chraibi", "seed.lina@festivapro.local", "+212 668 100 108"),
    ("Hicham Saidi", "seed.hicham@festivapro.local", "+212 669 100 109"),
    ("Meryem Raji", "seed.meryem@festivapro.local", "+212 670 100 110"),
    ("Anas Bennani", "seed.anas@festivapro.local", "+212 671 100 111"),
    ("Salma Zeroual", "seed.salma@festivapro.local", "+212 672 100 112"),
]

PRODUCTS = [
    ("Boissons gazeuses", "Coca-Cola", "can", Decimal("5.00"), Decimal("15.00"), Decimal("95")),
    ("Boissons gazeuses", "Sprite", "can", Decimal("5.00"), Decimal("15.00"), Decimal("82")),
    ("Eau", "Eau minerale", "bottle", Decimal("2.50"), Decimal("10.00"), Decimal("120")),
    ("Energie", "Red Bull", "can", Decimal("13.00"), Decimal("30.00"), Decimal("44")),
    ("Bieres", "Heineken", "bottle", Decimal("14.00"), Decimal("35.00"), Decimal("76")),
    ("Bieres", "Corona", "bottle", Decimal("16.00"), Decimal("40.00"), Decimal("55")),
    ("Spiritueux", "Vodka", "bottle", Decimal("160.00"), Decimal("420.00"), Decimal("18")),
    ("Spiritueux", "Whisky", "bottle", Decimal("190.00"), Decimal("480.00"), Decimal("16")),
    ("Snacks", "Chips", "unit", Decimal("4.00"), Decimal("12.00"), Decimal("50")),
]

EVENTS = [
    {
        "name": "Mawazine Lounge 2025",
        "location": "Rabat",
        "start": date(2025, 6, 20),
        "nights": 3,
        "attendance": 8400,
        "bars": ["Bar Nord", "Bar VIP", "Bar Terrasse", "Bar Scene"],
    },
    {
        "name": "Casa Beach Festival 2025",
        "location": "Casablanca",
        "start": date(2025, 8, 8),
        "nights": 2,
        "attendance": 5200,
        "bars": ["Bar Plage", "Bar Sunset", "Bar Premium"],
    },
    {
        "name": "Atlas Night Market 2024",
        "location": "Marrakech",
        "start": date(2024, 11, 15),
        "nights": 2,
        "attendance": 3600,
        "bars": ["Bar Medina", "Bar Jardin", "Bar Rooftop"],
    },
]


def d(value) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"))


def get_or_create_admin(db) -> User:
    admin = db.query(User).filter(User.email == "admin@festivapro.local").first()
    if admin:
        return admin
    admin = User(
        full_name="Admin FestivaPro",
        email="admin@festivapro.local",
        phone_number="+212 600 000 000",
        role="admin",
        hashed_password=hash_password(SEED_PASSWORD),
        is_active=True,
    )
    db.add(admin)
    db.flush()
    return admin


def get_or_create_employees(db) -> list[User]:
    employees = []
    for full_name, email, phone in EMPLOYEES:
        employee = db.query(User).filter(User.email == email).first()
        if not employee:
            employee = User(
                full_name=full_name,
                email=email,
                phone_number=phone,
                role="employee",
                hashed_password=hash_password(SEED_PASSWORD),
                is_active=True,
            )
            db.add(employee)
            db.flush()
        else:
            employee.phone_number = phone
            employee.is_active = True
        employees.append(employee)
    return employees


def get_or_create_products(db) -> list[Product]:
    categories = {}
    products = []
    for category_name, product_name, unit, _, _, _ in PRODUCTS:
        category = categories.get(category_name) or db.query(ProductCategory).filter(ProductCategory.name == category_name).first()
        if not category:
            category = ProductCategory(name=category_name)
            db.add(category)
            db.flush()
        categories[category_name] = category

        product = (
            db.query(Product)
            .filter(Product.name == product_name, Product.category_id == category.id)
            .first()
        )
        if not product:
            product = Product(name=product_name, category_id=category.id, unit=unit)
            db.add(product)
            db.flush()
        products.append(product)
    return products


def clear_seed_events(db) -> None:
    for event in db.query(Event).filter(Event.name.in_(SEED_EVENT_NAMES)).all():
        db.delete(event)
    db.flush()


def add_audit(db, admin: User, action: str, entity_type: str, entity_id: int | None, details: dict) -> None:
    db.add(
        AuditLog(
            user_id=admin.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=json.dumps(details, default=str),
        )
    )


def choose_staff(employees: list[User], bar_index: int, night_number: int) -> tuple[User, list[User]]:
    responsible = employees[(bar_index + night_number) % len(employees)]
    bartenders = []
    cursor = bar_index * 3 + night_number
    while len(bartenders) < 3:
        candidate = employees[cursor % len(employees)]
        cursor += 1
        if candidate.id != responsible.id and candidate not in bartenders:
            bartenders.append(candidate)
    return responsible, bartenders


def distribute_cash(total: Decimal, staff: list[User]) -> list[tuple[User, Decimal]]:
    if not staff:
        return []
    remaining = total
    rows = []
    for index, user in enumerate(staff):
        if index == len(staff) - 1:
            amount = remaining
        else:
            weight = Decimal("0.30") + (Decimal(index) * Decimal("0.04"))
            amount = (total * weight).quantize(Decimal("0.01"))
            remaining -= amount
        rows.append((user, amount))
    return rows


def seed_event(db, admin: User, employees: list[User], products: list[Product], config: dict) -> Event:
    event = Event(
        name=config["name"],
        location=config["location"],
        event_date=config["start"],
        start_date=config["start"],
        start_time=time(18, 0),
        end_time=time(3, 0),
        total_nights=config["nights"],
        total_nights_planned=config["nights"],
        status="active",
        attendance_count=config["attendance"],
        created_by=admin.id,
    )
    db.add(event)
    db.flush()
    add_audit(db, admin, "seed_create_event", "events", event.id, {"name": event.name, "status": "complete"})

    bars = []
    for index, bar_name in enumerate(config["bars"]):
        bar = Bar(
            event_id=event.id,
            name=bar_name,
            responsible_user_id=employees[index % len(employees)].id,
        )
        db.add(bar)
        db.flush()
        bars.append(bar)
        add_audit(db, admin, "seed_create_bar", "bars", bar.id, {"event_id": event.id, "name": bar.name})

    event_stock_by_product = {}
    for product, product_config in zip(products, PRODUCTS):
        _, _, _, bought_price, selling_price, base_qty = product_config
        total_qty = (base_qty * Decimal(len(bars)) * Decimal(config["nights"]) * Decimal("1.75")).quantize(Decimal("0.01"))
        event_stock = EventStock(
            event_id=event.id,
            product_id=product.id,
            total_qty_purchased=total_qty,
            bought_price=bought_price,
            selling_price=selling_price,
        )
        db.add(event_stock)
        db.flush()
        db.add(
            PriceHistory(
                event_stock_id=event_stock.id,
                event_id=event.id,
                product_id=product.id,
                old_selling_price=None,
                new_selling_price=selling_price,
                changed_by_id=admin.id,
            )
        )
        event_stock_by_product[product.id] = event_stock
    add_audit(db, admin, "seed_event_stock", "events", event.id, {"products": len(products)})

    carried = {bar.id: {product.id: Decimal("0.00") for product in products} for bar in bars}
    sales_by_employee: dict[tuple[int, int, int], dict[str, Decimal]] = {}
    bar_cash_totals: dict[tuple[int, int], Decimal] = {}

    for night_number in range(1, config["nights"] + 1):
        night = EventNight(
            event_id=event.id,
            night_number=night_number,
            date=config["start"] + timedelta(days=night_number - 1),
            status="active",
        )
        db.add(night)
        db.flush()
        add_audit(db, admin, "seed_open_night", "event_nights", night.id, {"night_number": night_number})

        for bar_index, bar in enumerate(bars):
            responsible, bartenders = choose_staff(employees, bar_index, night_number)
            assignments = [(responsible, "responsible", Decimal("350.00"))] + [(user, "bartender", Decimal("250.00") + Decimal(25 * (bar_index % 2))) for user in bartenders]
            staff_cost = Decimal("0.00")
            for user, role, salary in assignments:
                db.add(NightBarAssignment(event_night_id=night.id, bar_id=bar.id, user_id=user.id, role=role, salary_amount=salary))
                db.add(EventSalary(event_id=event.id, bar_id=bar.id, user_id=user.id, salary_amount=salary))
                if not db.query(BarAssignment).filter(BarAssignment.bar_id == bar.id, BarAssignment.user_id == user.id).first():
                    db.add(BarAssignment(bar_id=bar.id, user_id=user.id))
                staff_cost += salary

            expected_cash = Decimal("0.00")
            stock_cost = Decimal("0.00")
            total_units = Decimal("0.00")
            for product_index, (product, product_config) in enumerate(zip(products, PRODUCTS)):
                _, _, _, bought_price, selling_price, base_qty = product_config
                if night_number == 1:
                    opening = base_qty + Decimal(bar_index * 4) + Decimal(product_index % 3)
                    top_up = Decimal("0.00")
                else:
                    opening = carried[bar.id][product.id]
                    top_up = (base_qty * Decimal("0.32") + Decimal(bar_index + product_index % 2)).quantize(Decimal("0.00"))
                available = opening + top_up
                closing_rate = Decimal("0.12") + Decimal((bar_index + product_index + night_number) % 4) * Decimal("0.04")
                closing = (available * closing_rate).quantize(Decimal("0.00"))
                used = available - closing
                db.add(
                    BarNightStock(
                        bar_id=bar.id,
                        event_night_id=night.id,
                        product_id=product.id,
                        qty_opening=opening,
                        qty_top_up=top_up,
                        qty_closing=closing,
                        bought_price=bought_price,
                        selling_price=selling_price,
                        is_locked=True,
                    )
                )
                carried[bar.id][product.id] = closing
                expected_cash += used * selling_price
                stock_cost += used * bought_price
                total_units += used

            discrepancy_options = [Decimal("0.00"), Decimal("60.00"), Decimal("-40.00"), Decimal("25.00")]
            discrepancy = discrepancy_options[(bar_index + night_number) % len(discrepancy_options)]
            total_cash = expected_cash - discrepancy
            for user, amount in distribute_cash(total_cash, bartenders):
                db.add(BartenderCash(event_night_id=night.id, bar_id=bar.id, user_id=user.id, cash_collected=amount))
                key = (event.id, bar.id, user.id)
                sales_by_employee.setdefault(key, {"sales": Decimal("0.00"), "units": Decimal("0.00")})
                share = amount / total_cash if total_cash else Decimal("0.00")
                sales_by_employee[key]["sales"] += amount
                sales_by_employee[key]["units"] += (total_units * share).quantize(Decimal("0.01"))
            bar_cash_totals[(event.id, bar.id)] = bar_cash_totals.get((event.id, bar.id), Decimal("0.00")) + total_cash

            summary = BarNightSummary(
                event_night_id=night.id,
                bar_id=bar.id,
                total_cash_collected=total_cash,
                expected_cash=expected_cash,
                cash_discrepancy=discrepancy,
                stock_cost=stock_cost,
                staff_cost=staff_cost,
                gross_profit=total_cash - stock_cost,
                net_profit=total_cash - stock_cost - staff_cost,
                expected_profit=expected_cash - stock_cost - staff_cost,
                is_closed=True,
                closed_at=datetime.now(UTC),
            )
            db.add(summary)
            add_audit(db, admin, "seed_close_bar", "bars", bar.id, {"event_night_id": night.id, "cash_discrepancy": discrepancy})

        db.flush()
        for bar in bars:
            snapshot_bar(db, event.id, night.id, bar.id)
            db.add(generate_bar_pdf(db, event, night, bar))
        snapshot_event(db, event.id, night.id)
        db.add(generate_night_pdf(db, event, night))
        night.status = "closed"
        add_audit(db, admin, "seed_close_night", "event_nights", night.id, {"reports": len(bars) + 1})

    for (event_id, bar_id, user_id), values in sales_by_employee.items():
        bar_total = bar_cash_totals.get((event_id, bar_id), Decimal("0.00"))
        contribution_pct = ((values["sales"] / bar_total) * Decimal("100")).quantize(Decimal("0.01")) if bar_total else Decimal("0.00")
        db.add(
            BartenderSale(
                event_id=event_id,
                bar_id=bar_id,
                user_id=user_id,
                units_sold=values["units"],
                sales_amount=values["sales"],
                contribution_pct=contribution_pct,
            )
        )

    event.status = "closed"
    db.add(generate_event_pdf(db, event))
    add_audit(db, admin, "seed_close_event", "events", event.id, {"status": "closed", "reports": "complete"})
    return event


def main() -> None:
    db = SessionLocal()
    try:
        admin = get_or_create_admin(db)
        employees = get_or_create_employees(db)
        products = get_or_create_products(db)
        clear_seed_events(db)
        db.flush()

        events = [seed_event(db, admin, employees, products, config) for config in EVENTS]
        db.commit()
        print(f"Seeded {len(events)} complete past events with nights, bars, stock, cash, snapshots, audit logs, and PDFs.")
        print("Admin login: admin@festivapro.local / password")
        print("Employee login example: seed.yassine@festivapro.local / password")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
