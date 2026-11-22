"""Endpoint info model aktif (gabungan registri DB + artefak)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.db.repositories import model_repo
from app.dependencies.deps import CurrentUser, DbSession, ModelServiceDep
from app.schemas.model_info import ModelInfo

router = APIRouter(prefix="/model", tags=["Model"])


@router.get("/info", response_model=ModelInfo)
def get_model_info(
    _user: CurrentUser,
    db: DbSession,
    model: ModelServiceDep,
) -> ModelInfo:
    if not model.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=model.error or "Artefak model belum dimuat",
        )

    record = model_repo.get_active(db)
    info = model.info()
    return ModelInfo(
        model_id=record.model_id if record is not None else None,
        model_name=str(info["model_name"] or (record.model_name if record else "")),
        model_version=str(info["model_version"]),
        trained_date=record.trained_date if record is not None else info["trained_date"],
        best_params=info["best_params"],
        d_enc=int(info["d_enc"]),
        class_labels=list(info["class_labels"]),
        evaluation_metrics=info["evaluation_metrics"],
        comparator_info=info["comparator_info"],
    )


__all__ = ["router"]
