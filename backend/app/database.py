import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///./basarnas.db").strip()
    if url.startswith("mysql://"):
        url = url.replace("mysql://", "mysql+pymysql://", 1)
    return url


SQLALCHEMY_DATABASE_URL = _database_url()

_engine_options: dict[str, object] = {
    "pool_pre_ping": True,
}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    _engine_options["connect_args"] = {"check_same_thread": False}

engine: Engine = create_engine(SQLALCHEMY_DATABASE_URL, **_engine_options)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
