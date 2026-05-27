from datetime import date, time
from decimal import Decimal

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Bar, BarAssignment, BarStock, Event, EventSalary, EventStock, Product, ProductCategory, User


EVENTS = [
    ("Casa Nights Festival", "Casablanca", date(2026, 6, 5), time(18, 0), time(2, 0), 1800),
    ("Marrakech Desert Beats", "Marrakech", date(2026, 6, 12), time(19, 0), time(3, 0), 2300),
    ("Agadir Beach Sessions", "Agadir", date(2026, 6, 19), time(17, 30), time(1, 30), 1500),
    ("Rabat Stage Live", "Rabat", date(2026, 6, 26), time(18, 30), time(2, 30), 1650),
    ("Tanger Harbor Sound", "Tanger", date(2026, 7, 3), time(19, 30), time(3, 30), 2100),
]

PRODUCTS = [
    ("Gold Special", "Beer", "can", Decimal("12"), Decimal("30")),
    ("Casablanca", "Beer", "bottle", Decimal("14"), Decimal("35")),
    ("Gordon's", "Hard Alcohol", "bottle", Decimal("150"), Decimal("350")),
    ("Tanqueray", "Hard Alcohol", "bottle", Decimal("230"), Decimal("520")),
    ("Smirnoff", "Hard Alcohol", "bottle", Decimal("120"), Decimal("320")),
    ("Belvedere", "Hard Alcohol", "bottle", Decimal("360"), Decimal("760")),
    ("Red Label", "Hard Alcohol", "bottle", Decimal("180"), Decimal("420")),
    ("Black Label", "Hard Alcohol", "bottle", Decimal("310"), Decimal("680")),
    ("Jose Cuervo Tequila", "Hard Alcohol", "bottle", Decimal("190"), Decimal("450")),
    ("Coca-Cola", "Soda", "can", Decimal("5"), Decimal("15")),
    ("Sprite", "Soda", "can", Decimal("5"), Decimal("15")),
    ("Water", "Soda", "bottle", Decimal("3"), Decimal("10")),
    ("Tonic", "Soda", "can", Decimal("6"), Decimal("18")),
    ("Goblets", "Consumables", "unit", Decimal("0.60"), Decimal("1")),
    ("Ice", "Consumables", "unit", Decimal("8"), Decimal("12")),
    ("Napkins", "Consumables", "unit", Decimal("0.20"), Decimal("0.50")),
    ("Straws", "Consumables", "unit", Decimal("0.10"), Decimal("0.30")),
]


def get_or_create(db, model, defaults=None, **filters):
    record = db.query(model).filter_by(**filters).first()
    if record:
        return record
    record = model(**filters, **(defaults or {}))
    db.add(record)
    db.flush()
    return record


def main() -> None:
    db = SessionLocal()
    try:
        admin = get_or_create(
            db,
            User,
            email="admin@festivapro.local",
            defaults={
                "full_name": "Festival Admin",
                "phone_number": "+212600000001",
                "role": "admin",
                "hashed_password": hash_password("password"),
                "is_active": True,
            },
        )
        employees = [
            get_or_create(
                db,
                User,
                email=f"employee{index}@festivapro.local",
                defaults={
                    "full_name": name,
                    "phone_number": f"+212600000{index + 10:03d}",
                    "role": "employee",
                    "hashed_password": hash_password("password"),
                    "is_active": True,
                },
            )
            for index, name in enumerate(
                [
                    "Yassine Amrani",
                    "Salma Idrissi",
                    "Omar Benali",
                    "Nadia Berrada",
                    "Mehdi El Fassi",
                    "Imane Tazi",
                    "Hassan Alaoui",
                    "Sara Moutawakil",
                    "Rachid Mansouri",
                    "Lina Sabri",
                    "Karim Lahlou",
                    "Meryem Chraibi",
                ],
                start=1,
            )
        ]
        categories = {name: get_or_create(db, ProductCategory, name=name) for name in ["Beer", "Hard Alcohol", "Soda", "Consumables"]}
        products = []
        for name, category, unit, _, _ in PRODUCTS:
            products.append(get_or_create(db, Product, name=name, category_id=categories[category].id, defaults={"unit": unit}))

        for event_index, (name, city, event_date, start_time, end_time, attendance) in enumerate(EVENTS, start=1):
            event = get_or_create(
                db,
                Event,
                name=name,
                defaults={"location": city, "event_date": event_date, "start_time": start_time, "end_time": end_time, "status": "upcoming", "attendance_count": attendance, "created_by": admin.id},
            )
            bar_count = [3, 4, 3, 2, 3][event_index - 1]
            bars = []
            for offset in range(bar_count):
                employee = employees[(event_index + offset) % len(employees)]
                bar = get_or_create(db, Bar, event_id=event.id, name=["Main Bar", "VIP Bar", "Garden Bar", "Terrace Bar"][offset % 4], defaults={})
                bars.append(bar)
                for assignment_offset in range(3):
                    bartender = employees[(event_index * 3 + offset + assignment_offset) % len(employees)]
                    get_or_create(db, BarAssignment, bar_id=bar.id, user_id=bartender.id)
                    db.add(EventSalary(event_id=event.id, bar_id=bar.id, user_id=bartender.id, salary_amount=Decimal("350.00")))
            for product_index, product in enumerate(products, start=1):
                _, _, _, bought, sold = PRODUCTS[product_index - 1]
                event_stock = get_or_create(
                    db,
                    EventStock,
                    event_id=event.id,
                    product_id=product.id,
                    defaults={"quantity_total": Decimal(120 + event_index * 20 + product_index * 3), "bought_price_per_unit": bought, "selling_price_per_unit": sold},
                )
                for bar in bars:
                    allocated = Decimal(20 + (bar.id % 4) * 4 + (product_index % 5) * 3)
                    remaining = max(Decimal(0), allocated - Decimal(5 + ((bar.id + product_index) % 9)))
                    get_or_create(db, BarStock, bar_id=bar.id, product_id=product.id, defaults={"quantity_allocated": allocated, "quantity_remaining": remaining})
        db.commit()
        print("Seed data ready.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
