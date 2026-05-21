from sqlalchemy.orm import Session

from app.auth.security import create_access_token, hash_password, verify_password
from app.config import get_settings
from app.models.domain import User


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def build_token(user: User) -> str:
    return create_access_token(user.email, {"role": user.role, "name": user.full_name})


def ensure_default_admin(db: Session) -> None:
    settings = get_settings()
    if db.query(User).filter(User.email == settings.default_admin_email).first():
        return
    db.add(User(email=settings.default_admin_email, full_name="FestivaPro Admin", role="admin", hashed_password=hash_password(settings.default_admin_password)))
    db.commit()
