"""Endpoint meta: opsi dropdown form prediksi."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.dependencies.deps import CurrentUser, ModelServiceDep
from app.schemas.model_info import MetaOptions

router = APIRouter(prefix="/meta", tags=["Meta"])


@router.get("/options", response_model=MetaOptions)
def get_options(_user: CurrentUser, model: ModelServiceDep) -> MetaOptions:
    if not model.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=model.error or "Artefak model belum dimuat",
        )
    return MetaOptions.model_validate(model.options())


__all__ = ["router"]
