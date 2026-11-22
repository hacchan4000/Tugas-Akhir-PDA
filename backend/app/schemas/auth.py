"""Schema auth: login, profil operator, dan token cookie."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.utils.security import BCRYPT_MAX_BYTES


class LoginRequest(BaseModel):
    # Jangan pakai str_strip_whitespace di sini: spasi bisa jadi bagian password.
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=200)

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("password")
    @classmethod
    def _check_bcrypt_limit(cls, value: str) -> str:
        if len(value.encode("utf-8")) > BCRYPT_MAX_BYTES:
            raise ValueError(f"password maksimal {BCRYPT_MAX_BYTES} byte")
        return value


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    name: str
    email: EmailStr
    created_at: datetime


__all__ = ["LoginRequest", "UserResponse"]
