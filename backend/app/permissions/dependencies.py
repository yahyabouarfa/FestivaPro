from fastapi import HTTPException, status

from app.models.domain import User


def require_roles(user: User, allowed_roles: set[str]) -> None:
    if user.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
