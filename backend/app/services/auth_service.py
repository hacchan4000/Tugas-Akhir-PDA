"""Autentikasi & registrasi operator (bcrypt) dengan verifikasi waktu-konstan."""

from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.repositories import user_repo
from app.utils.errors import PersistenceError
from app.utils.security import hash_password, verify_dummy_password, verify_password

logger = logging.getLogger(__name__)


class EmailAlreadyRegisteredError(ValueError):
    """Email sudah terdaftar di database."""


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


def register(db: Session, *, name: str, email: str, password: str) -> User:
    """Daftarkan akun operator baru dan simpan ke tabel `users`."""
    if user_repo.get_by_email(db, email) is not None:
        raise EmailAlreadyRegisteredError("Email sudah terdaftar")

    password_hash = hash_password(password)
    try:
        user = user_repo.create(
            db,
            name=name,
            email=email,
            password_hash=password_hash,
        )
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError as exc:
        db.rollback()
        if user_repo.get_by_email(db, email) is not None:
            raise EmailAlreadyRegisteredError("Email sudah terdaftar") from exc
        logger.exception("IntegrityError saat mendaftarkan operator")
        raise PersistenceError("Gagal menyimpan akun operator ke database") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("SQLAlchemyError saat mendaftarkan operator")
        raise PersistenceError("Gagal menyimpan akun operator ke database") from exc


__all__ = ["EmailAlreadyRegisteredError", "authenticate", "register"]
