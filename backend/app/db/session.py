"""Engine & session factory SQLAlchemy 2.0 (sinkron).

CATATAN: `create_all()` sengaja TIDAK dipanggil di sini. Skema dimiliki oleh
migrasi Alembic (`backend/migrations/versions/`), supaya PostgreSQL bisa
menjalankan `ENABLE ROW LEVEL SECURITY` dan partial unique index dengan benar.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings


def normalize_database_url(url: str) -> str:
    """Samakan scheme URL dengan driver yang benar-benar terpasang.

    - `postgres://` / `postgresql://` -> `postgresql+psycopg://`
      (tanpa ini SQLAlchemy memakai psycopg2 yang tidak ada di requirements)
    - `mysql://` -> `mysql+pymysql://`
    """
    url = url.strip()
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    if url.startswith("mysql://"):
        return "mysql+pymysql://" + url[len("mysql://") :]
    return url


def build_engine(url: str, *, echo: bool = False) -> Engine:
    normalized = normalize_database_url(url)
    options: dict[str, object] = {
        "echo": echo,
        "pool_pre_ping": True,
        "future": True,
    }
    if normalized.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        # In-memory SQLite harus memakai satu koneksi agar tabel tidak hilang.
        if ":memory:" in normalized or normalized.endswith("sqlite://"):
            options["poolclass"] = StaticPool
    else:
        options["pool_size"] = 5
        options["max_overflow"] = 10
        options["pool_recycle"] = 1800
    return create_engine(normalized, **options)


_settings = get_settings()

engine: Engine = build_engine(_settings.DATABASE_URL, echo=_settings.DB_ECHO)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)
