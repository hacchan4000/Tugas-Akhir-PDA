"""Endpoint auth: login (cookie), registrasi akun, logout, profil operator."""

from __future__ import annotations

import math
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.config import Settings
from app.dependencies.deps import AppSettings, CurrentUser, DbSession, LoginLimiterDep
from app.schemas.auth import LoginRequest, RegisterRequest, UserResponse
from app.services import auth_service
from app.services.auth_service import EmailAlreadyRegisteredError
from app.utils.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


def _client_key(request: Request) -> str:
    """Kunci pembatas laju: alamat klien, bukan email.

    Memakai email akan membuat penyerang bisa mengunci akun operator tertentu
    hanya dengan salah password berulang kali. Konsekuensinya, beberapa operator
    di balik satu NAT berbagi kuota — trade-off yang disengaja.
    """
    client = request.client
    return client.host if client is not None else "unknown"


def _set_auth_cookie(response: Response, user_id: int, settings: Settings) -> None:
    token = create_access_token(
        user_id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        max_age=settings.access_token_max_age,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        path="/",
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    response: Response,
    db: DbSession,
    settings: AppSettings,
) -> UserResponse:
    try:
        user = auth_service.register(
            db,
            name=payload.name,
            email=payload.email,
            password=payload.password,
        )
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from None

    _set_auth_cookie(response, user.user_id, settings)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=UserResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: DbSession,
    limiter: LoginLimiterDep,
    settings: AppSettings,
) -> UserResponse:
    key = _client_key(request)
    retry_after = limiter.retry_after(key)
    if retry_after > 0:
        detik = max(1, math.ceil(retry_after))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Terlalu banyak percobaan login gagal. "
                f"Coba lagi dalam {detik} detik."
            ),
            headers={"Retry-After": str(detik)},
        )

    user = auth_service.authenticate(db, payload.email, payload.password)
    if user is None:
        limiter.record(key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau password salah",
        )

    # Login berhasil mengosongkan hitungan: operator sah yang sempat salah
    # password tidak perlu menunggu jendela waktu habis.
    limiter.reset(key)
    _set_auth_cookie(response, user.user_id, settings)
    return UserResponse.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    _user: CurrentUser,
    settings: AppSettings,
) -> None:
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        path="/",
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


__all__ = ["router"]
