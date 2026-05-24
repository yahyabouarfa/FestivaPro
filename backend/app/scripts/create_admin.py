import getpass

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User


def main() -> None:
    full_name = input("Full name: ").strip()
    email = input("Email: ").strip().lower()
    phone_number = input("Phone number (optional): ").strip() or None
    password = getpass.getpass("Password: ")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise SystemExit("A user with that email already exists.")
        db.add(
            User(
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                role="admin",
                hashed_password=hash_password(password),
                is_active=True,
            )
        )
        db.commit()
        print("Admin user created.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
