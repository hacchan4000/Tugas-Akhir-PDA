"""Autentikasi operator (bcrypt) dengan verifikasi waktu-konstan."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import User
from app.db.repositories import user_repo
from app.utils.security import verify_dummy_password, verify_password


def authenticate(db: Session, email: str, password: str) -> User | None:
    """Kembalikan `User` bila kredensial valid, `None` bila tidak.

    Saat email tidak terdaftar, bcrypt tetap dijalankan pada hash dummy supaya
    waktu respons tidak membocorkan keberadaan akun.
    """
    user = user_repo.get_by_email(db, email)
    if user is None:
        verify_dummy_password(password)
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


__all__ = ["authenticate"]
