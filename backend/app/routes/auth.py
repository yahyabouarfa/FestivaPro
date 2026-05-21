from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.domain import User
from app.schemas.auth import CurrentUser, LoginRequest, TokenResponse
from app.services.auth_service import authenticate_user, build_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=build_token(user))


@router.get("/me", response_model=CurrentUser)
def me(user: User = Depends(get_current_user)) -> CurrentUser:
    return CurrentUser(id=user.id, email=user.email, full_name=user.full_name, role=user.role)
