"""Router API v1 (prefix `/api/v1`)."""

from fastapi import APIRouter

from app.api.v1 import auth, health, meta, model_info, predictions

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(meta.router)
api_router.include_router(predictions.router)
api_router.include_router(model_info.router)

__all__ = ["api_router"]
