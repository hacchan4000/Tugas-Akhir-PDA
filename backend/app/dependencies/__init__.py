"""Dependency injection FastAPI (DB, service, current user)."""

from app.dependencies.deps import (
    COOKIE_NAME,
    CurrentUser,
    DbSession,
    GeocodingServiceDep,
    ModelServiceDep,
    get_current_user,
    get_db,
    get_geocoding_service,
    get_model_service,
)

__all__ = [
    "COOKIE_NAME",
    "CurrentUser",
    "DbSession",
    "GeocodingServiceDep",
    "ModelServiceDep",
    "get_current_user",
    "get_db",
    "get_geocoding_service",
    "get_model_service",
]
