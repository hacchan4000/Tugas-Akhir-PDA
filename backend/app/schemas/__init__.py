"""Schema Pydantic per domain (auth, prediction, history, model info)."""

from app.schemas.auth import LoginRequest, UserResponse
from app.schemas.history import HistoryPage
from app.schemas.model_info import CoordinateBounds, MetaOptions, ModelInfo
from app.schemas.prediction import PredictionCreate, PredictionRead

__all__ = [
    "LoginRequest",
    "UserResponse",
    "HistoryPage",
    "CoordinateBounds",
    "MetaOptions",
    "ModelInfo",
    "PredictionCreate",
    "PredictionRead",
]
