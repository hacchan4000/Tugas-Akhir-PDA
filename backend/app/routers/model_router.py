import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Model as ModelRecord
from app.models import User
from app.schemas import ModelActiveResponse, ModelCreate, ModelResponse


router = APIRouter(tags=["Models"])


@router.get("/", response_model=list[ModelResponse])
def list_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ModelRecord]:
    del current_user
    records = db.scalars(
        select(ModelRecord).order_by(ModelRecord.updated_date.desc())
    ).all()
    return list(records)


@router.get("/active", response_model=ModelActiveResponse)
def get_active_model(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelActiveResponse:
    del current_user
    record = db.scalar(
        select(ModelRecord)
        .where(ModelRecord.model_status == "active")
        .order_by(ModelRecord.updated_date.desc())
        .limit(1)
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tidak ada model aktif",
        )

    try:
        metrics: dict[str, Any] = json.loads(record.metrics_json or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Format metrics_json model aktif tidak valid",
        ) from exc
    if not isinstance(metrics, dict):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="metrics_json model aktif harus berupa objek JSON",
        )

    confusion_matrix = metrics.get("confusion_matrix") or []
    has_evaluation_metrics = any(
        metrics.get(name) is not None
        for name in ("accuracy", "macro_f1", "precision", "recall")
    )
    return ModelActiveResponse(
        model_id=record.model_id,
        algorithm=record.model_name,
        version=record.model_version,
        training_date=record.updated_date if has_evaluation_metrics else None,
        accuracy=metrics.get("accuracy"),
        macro_f1=metrics.get("macro_f1"),
        precision=metrics.get("precision"),
        recall=metrics.get("recall"),
        confusion_matrix=confusion_matrix,
    )


@router.post("/", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
def register_model(
    payload: ModelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelRecord:
    del current_user
    record = ModelRecord(
        model_name=payload.model_name,
        model_version=payload.model_version,
        model_file=payload.model_file,
        model_status=payload.model_status,
        metrics_json=payload.metrics_json,
    )

    try:
        if payload.model_status == "active":
            db.execute(
                ModelRecord.__table__.update().values(model_status="inactive")
            )
        db.add(record)
        db.commit()
        db.refresh(record)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gagal menyimpan konfigurasi model",
        ) from exc
    return record


@router.patch("/{model_id}/activate", response_model=ModelResponse)
def activate_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelRecord:
    del current_user
    record = db.get(ModelRecord, model_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model tidak ditemukan",
        )

    try:
        db.execute(ModelRecord.__table__.update().values(model_status="inactive"))
        record.model_status = "active"
        db.commit()
        db.refresh(record)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gagal mengaktifkan model",
        ) from exc
    return record
