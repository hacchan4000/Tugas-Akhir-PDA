"""Query helper untuk tabel `users`."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import User


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    normalized = email.strip().lower()
    return db.scalar(select(User).where(func.lower(User.email) == normalized))


def create(db: Session, *, name: str, email: str, password_hash: str) -> User:
    user = User(
        name=name.strip(),
        email=email.strip().lower(),
        password_hash=password_hash,
    )
    db.add(user)
    db.flush()
    return user


def update_password(db: Session, user: User, password_hash: str) -> User:
    user.password_hash = password_hash
    db.flush()
    return user


def count(db: Session) -> int:
    return int(db.scalar(select(func.count()).select_from(User)) or 0)
