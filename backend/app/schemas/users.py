from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class UserBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone_number: str | None = Field(default=None, max_length=40)
    role: str = Field(pattern="^(admin|employee)$")
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, max_length=40)
    role: str | None = Field(default=None, pattern="^(admin|employee)$")
    password: str | None = Field(default=None, min_length=8)
    is_active: bool | None = None


class UserRead(ORMModel):
    id: int
    full_name: str
    email: EmailStr
    phone_number: str | None
    role: str
    created_at: datetime
    is_active: bool
