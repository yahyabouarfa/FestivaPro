from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, TokenPair
from app.schemas.common import ApiMessage
from app.schemas.users import UserRead
from app.services.auth import authenticate_user, issue_token_pair, revoke_refresh_token, rotate_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: DbSession) -> TokenPair:
    user = authenticate_user(db, payload.email, payload.password)
    access_token, refresh_token = issue_token_pair(db, user)
    return TokenPair(access_token=access_token, refresh_token=refresh_token, user=UserRead.model_validate(user))


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: DbSession) -> TokenPair:
    user, access_token, refresh_token = rotate_refresh_token(db, payload.refresh_token)
    return TokenPair(access_token=access_token, refresh_token=refresh_token, user=UserRead.model_validate(user))


@router.post("/logout", response_model=ApiMessage)
def logout(payload: LogoutRequest, db: DbSession) -> ApiMessage:
    revoke_refresh_token(db, payload.refresh_token)
    return ApiMessage(message="Logged out successfully.")


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
