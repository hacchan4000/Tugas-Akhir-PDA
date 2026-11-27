"""Schema auth: login, registrasi, profil operator, dan token cookie."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.utils.security import BCRYPT_MAX_BYTES


def _normalize_email_value(value: object) -> object:
    return value.strip().lower() if isinstance(value, str) else value


def _validate_bcrypt_password(value: str) -> str:
    if len(value.encode("utf-8")) > BCRYPT_MAX_BYTES:
        raise ValueError(f"password maksimal {BCRYPT_MAX_BYTES} byte")
    return value


class LoginRequest(BaseModel):
    # Jangan pakai str_strip_whitespace di sini: spasi bisa jadi bagian password.
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=200)

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value: object) -> object:
        return _normalize_email_value(value)

    @field_validator("password")
    @classmethod
    def _check_bcrypt_limit(cls, value: str) -> str:
        return _validate_bcrypt_password(value)


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=100)
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=200)

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email", mode="before")
    @classmethod
    def _normalize_email(cls, value: object) -> object:
        return _normalize_email_value(value)

    @field_validator("password")
    @classmethod
    def _check_bcrypt_limit(cls, value: str) -> str:
        return _validate_bcrypt_password(value)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    name: str
    email: EmailStr
    created_at: datetime


__all__ = ["LoginRequest", "RegisterRequest", "UserResponse"]
