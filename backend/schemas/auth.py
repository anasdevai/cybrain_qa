"""Pydantic v2 schemas for authentication and user management."""

import re
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_]+$")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[@$!%*?&]", v):
            raise ValueError("Password must contain at least one special character (@$!%*?&).")
        return v

    @model_validator(mode="after")
    def check_passwords_match(self) -> "UserCreate":
        if getattr(self, "password", None) != getattr(self, "confirm_password", None):
            raise ValueError("Passwords do not match.")
        return self


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    is_verified: bool
    role: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    user_id: Optional[UUID] = None
    email: Optional[str] = None
