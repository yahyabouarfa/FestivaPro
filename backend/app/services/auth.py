from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token, hash_token, utcnow, verify_password
from app.models import RefreshToken, User


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou mot de passe invalide.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ce compte est inactif.")
    return user


def issue_token_pair(db: Session, user: User) -> tuple[str, str]:
    access_token = create_access_token(str(user.id), user.role)
    refresh_token, expires_at = create_refresh_token(str(user.id))
    db.add(RefreshToken(user_id=user.id, token_hash=hash_token(refresh_token), expires_at=expires_at))
    db.commit()
    return access_token, refresh_token


def rotate_refresh_token(db: Session, refresh_token: str) -> tuple[User, str, str]:
    from app.core.security import decode_token

    try:
        payload = decode_token(refresh_token, "refresh")
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Le jeton de rafraîchissement est invalide ou expiré.")

    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_token(refresh_token)).first()
    if not stored or stored.revoked_at is not None or stored.expires_at < utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Le jeton de rafraîchissement a expiré ou a été révoqué.")

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Le compte utilisateur est inactif ou n’existe plus.")

    stored.revoked_at = utcnow()
    access_token, new_refresh_token = issue_token_pair(db, user)
    db.commit()
    return user, access_token, new_refresh_token


def revoke_refresh_token(db: Session, refresh_token: str) -> None:
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_token(refresh_token)).first()
    if stored and stored.revoked_at is None:
        stored.revoked_at = utcnow()
        db.commit()
