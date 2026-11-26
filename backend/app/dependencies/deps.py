"""Dependency FastAPI: DB session, service, dan operator terautentikasi.

Autentikasi memakai cookie `access_token` (httponly, sesuai SPEC). Header
`Authorization: Bearer ...` tetap diterima sebagai fallback agar endpoint bisa
dicoba lewat Swagger UI; cookie selalu diutamakan.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated
from urllib.parse import urlsplit

import jwt
from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import User
from app.db.repositories import user_repo
from app.db.session import SessionLocal
from app.services.geocoding_service import GeocodingService
from app.services.model_service import ModelService
from app.utils.rate_limit import SlidingWindowLimiter
from app.utils.security import decode_access_token

COOKIE_NAME = get_settings().COOKIE_NAME

_bearer = HTTPBearer(
    auto_error=False,
    description="Fallback opsional; frontend memakai cookie access_token.",
)

# Metode yang tidak mengubah state, jadi tidak perlu proteksi CSRF.
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})


def get_app_settings(request: Request) -> Settings:
    """Settings milik app yang menangani request (bukan cache global).

    `create_app(settings)` boleh dipanggil dengan settings khusus (tes), jadi
    membaca `get_settings()` di sini bisa memakai konfigurasi yang salah.
    """
    settings = getattr(request.app.state, "settings", None)
    return settings if isinstance(settings, Settings) else get_settings()


def _check_csrf_origin(request: Request) -> None:
    """Tolak request lintas situs yang membawa cookie sesi.

    `SameSite=lax` sudah menahan POST lintas situs, tapi konfigurasi
    `COOKIE_SAMESITE=none` (frontend beda domain, HTTPS) membukanya kembali.
    Karena token tidak dikirim lewat header pada mode cookie, satu-satunya cara
    membedakan request sah dan CSRF adalah `Origin` / `Sec-Fetch-Site`.

    Perbandingan memakai *host*, bukan skema. Di belakang reverse proxy
    (TLS dihentikan di proxy), `request.url.scheme` bisa `http` padahal browser
    mengirim `https://...`; membandingkan skema akan menolak request sah.
    Penyerang tetap tidak bisa memalsukan host karena `Origin` diisi browser.
    """
    origin = request.headers.get("origin")
    if origin is not None:
        origin = origin.rstrip("/")
        allowed = {o.rstrip("/") for o in get_app_settings(request).cors_origins}
        host_sama = urlsplit(origin).netloc == request.url.netloc
        if origin not in allowed and not host_sama:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permintaan lintas situs ditolak",
            )
        return
    if request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permintaan lintas situs ditolak",
        )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_model_service(request: Request) -> ModelService:
    service: ModelService | None = getattr(request.app.state, "model_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Layanan model belum diinisialisasi",
        )
    return service


def get_geocoding_service(request: Request) -> GeocodingService:
    service: GeocodingService | None = getattr(
        request.app.state, "geocoding_service", None
    )
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Layanan geocoding belum diinisialisasi",
        )
    return service


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    access_token: Annotated[str | None, Cookie(alias=COOKIE_NAME)] = None,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer)
    ] = None,
) -> User:
    token = access_token or (credentials.credentials if credentials else None)
    if not token:
        raise _unauthorized("Sesi tidak ditemukan; silakan login terlebih dahulu")

    # Hanya mode cookie yang rentan CSRF; klien Bearer mengirim token manual.
    if access_token and request.method not in _SAFE_METHODS:
        _check_csrf_origin(request)

    try:
        user_id = decode_access_token(token)
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise _unauthorized("Token tidak valid atau sudah kedaluwarsa") from None

    user = user_repo.get_by_id(db, user_id)
    if user is None:
        raise _unauthorized("Akun operator tidak ditemukan")
    return user


def get_login_limiter(request: Request) -> SlidingWindowLimiter:
    """Pembatas laju login milik app (dibuat di `create_app`)."""
    limiter = getattr(request.app.state, "login_limiter", None)
    if isinstance(limiter, SlidingWindowLimiter):
        return limiter
    settings = get_app_settings(request)
    limiter = SlidingWindowLimiter(
        settings.LOGIN_MAX_ATTEMPTS, settings.LOGIN_WINDOW_SECONDS
    )
    request.app.state.login_limiter = limiter
    return limiter


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]
ModelServiceDep = Annotated[ModelService, Depends(get_model_service)]
GeocodingServiceDep = Annotated[GeocodingService, Depends(get_geocoding_service)]
LoginLimiterDep = Annotated[SlidingWindowLimiter, Depends(get_login_limiter)]
AppSettings = Annotated[Settings, Depends(get_app_settings)]

__all__ = [
    "COOKIE_NAME",
    "get_db",
    "get_model_service",
    "get_geocoding_service",
    "get_current_user",
    "get_login_limiter",
    "get_app_settings",
    "CurrentUser",
    "DbSession",
    "ModelServiceDep",
    "GeocodingServiceDep",
    "LoginLimiterDep",
    "AppSettings",
]
