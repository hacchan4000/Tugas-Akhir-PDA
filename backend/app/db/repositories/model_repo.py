"""Query helper untuk tabel `models`."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Model


def get_active(db: Session) -> Model | None:
    return db.scalar(
        select(Model).where(Model.model_status == "active").limit(1)
    )


def get_by_version(db: Session, model_version: str) -> Model | None:
    return db.scalar(
        select(Model)
        .where(Model.model_version == model_version)
        .order_by(Model.trained_date.desc())
        .limit(1)
    )


def list_all(db: Session) -> list[Model]:
    return list(db.scalars(select(Model).order_by(Model.trained_date.desc())).all())


def upsert_active(
    db: Session,
    *,
    model_name: str,
    model_version: str,
    best_params: dict[str, Any] | None,
    trained_date: datetime,
) -> Model:
    """Jadikan satu model sebagai `active`, arsipkan model aktif sebelumnya.

    `flush()` di antara langkah penting: partial unique index
    `uq_models_single_active` menolak dua baris `active` sekaligus.
    """
    current = get_active(db)

    if current is not None and current.model_version == model_version:
        current.model_name = model_name
        current.best_params = best_params or {}
        current.trained_date = trained_date
        db.flush()
        return current

    if current is not None:
        current.model_status = "archived"
        db.flush()

    record = Model(
        model_name=model_name,
        model_version=model_version,
        best_params=best_params or {},
        model_status="active",
        trained_date=trained_date,
    )
    db.add(record)
    db.flush()
    return record


def get_comparator(db: Session, model_version: str) -> Model | None:
    return db.scalar(
        select(Model)
        .where(
            Model.model_status == "comparator",
            Model.model_version == model_version,
        )
        .limit(1)
    )


def upsert_comparator(
    db: Session,
    *,
    model_name: str,
    model_version: str,
    best_params: dict[str, Any] | None,
    trained_date: datetime,
) -> Model:
    """Catat model pembanding (runner-up) untuk versi artefak yang sama."""
    current = get_comparator(db, model_version)

    if current is not None:
        current.model_name = model_name
        current.best_params = best_params or {}
        current.trained_date = trained_date
        db.flush()
        return current

    record = Model(
        model_name=model_name,
        model_version=model_version,
        best_params=best_params or {},
        model_status="comparator",
        trained_date=trained_date,
    )
    db.add(record)
    db.flush()
    return record
