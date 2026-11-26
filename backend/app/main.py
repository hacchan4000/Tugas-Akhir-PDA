"""Entry point FastAPI: lifespan, CORS, router v1, dan error handler.

Jalankan dari folder `backend/`:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import api_router
from app.config import Settings, get_settings
from app.db.repositories import model_repo
from app.db.session import SessionLocal
from app.services.geocoding_service import GeocodingService
from app.services.model_service import ModelService
from app.utils.errors import ApiValidationError, ModelUnavailableError, PersistenceError
from app.utils.rate_limit import SlidingWindowLimiter

logger = logging.getLogger(__name__)

# Pesan validasi Pydantic (Inggris) -> Indonesia, sesuai SPEC bagian 4.
# Kunci = `error["type"]` Pydantic v2. Yang tidak ada di sini akan bocor sebagai
# teks Inggris, jadi tambahkan kunci baru setiap kali schema berubah
# (`tests/test_error_messages.py` gagal kalau ada yang terlewat).
_ERROR_MESSAGES: dict[str, str] = {
    "missing": "field wajib diisi",
    "extra_forbidden": "field tidak dikenal",
    "model_type": "body harus berupa objek JSON",
    "date_parsing": "format tanggal harus YYYY-MM-DD",
    "date_from_datetime_parsing": "format tanggal harus YYYY-MM-DD",
    "date_from_datetime_inexact": "tanggal tidak boleh memuat jam",
    "datetime_parsing": "format tanggal/waktu tidak valid",
    "time_parsing": "format waktu tidak valid",
    "greater_than": "nilai harus lebih besar dari batas minimum",
    "greater_than_equal": "nilai di bawah batas minimum",
    "less_than": "nilai harus lebih kecil dari batas maksimum",
    "less_than_equal": "nilai di atas batas maksimum",
    "string_too_short": "teks terlalu pendek",
    "string_too_long": "teks terlalu panjang",
    "string_type": "harus berupa teks",
    "string_pattern_mismatch": "format teks tidak sesuai",
    "int_parsing": "harus berupa bilangan bulat",
    "int_type": "harus berupa bilangan bulat",
    "float_parsing": "harus berupa angka",
    "float_type": "harus berupa angka",
    "finite_number": "harus berupa angka hingga (bukan NaN atau Infinity)",
    "decimal_parsing": "harus berupa angka desimal",
    "bool_parsing": "harus berupa boolean",
    "bool_type": "harus berupa boolean",
    "list_type": "harus berupa daftar",
    "dict_type": "harus berupa objek",
    "url_parsing": "format URL tidak valid",
    "json_invalid": "body JSON tidak valid",
    "email_str": "format email tidak valid",
    "value_error": "nilai tidak valid",
}

# Pesan bawaan Pydantic/email-validator yang perlu diterjemahkan walau tipenya
# `value_error` (tipe itu juga dipakai validator kita sendiri yang sudah
# berbahasa Indonesia, jadi tidak boleh ditimpa mentah-mentah).
_VALUE_ERROR_PREFIXES: tuple[tuple[str, str], ...] = (
    ("value is not a valid email address", "format email tidak valid"),
)


def _translate(error: dict[str, Any]) -> str:
    message = str(error.get("msg", "nilai tidak valid"))
    message = message.removeprefix("Value error, ")
    if error.get("type") == "value_error":
        for prefix, terjemahan in _VALUE_ERROR_PREFIXES:
            if message.startswith(prefix):
                return terjemahan
        return message
    return _ERROR_MESSAGES.get(str(error.get("type")), message)


def _field_name(error: dict[str, Any]) -> str:
    location = [
        str(part)
        for part in error.get("loc", ())
        if part not in {"body", "query", "path", "header", "cookie"}
    ]
    return ".".join(location) or "body"


def _validation_response(errors: list[dict[str, str]]) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": errors})


def _sync_model_registry(model_service: ModelService) -> None:
    """Daftarkan artefak yang dimuat sebagai model `active` di tabel `models`."""
    if not model_service.is_ready:
        return

    info = model_service.info()
    trained_date = info["trained_date"] or datetime.now(timezone.utc)

    try:
        with SessionLocal() as db:
            model_repo.upsert_active(
                db,
                model_name=info["model_name"] or model_service.model_type,
                model_version=info["model_version"],
                best_params=info["best_params"],
                trained_date=trained_date,
            )

            comparator = info.get("comparator_info")
            if isinstance(comparator, dict) and comparator.get("model_name"):
                comp_params = comparator.get("best_params")
                model_repo.upsert_comparator(
                    db,
                    model_name=str(comparator["model_name"])[:50],
                    model_version=info["model_version"],
                    best_params=comp_params if isinstance(comp_params, dict) else None,
                    trained_date=trained_date,
                )
            db.commit()
    except SQLAlchemyError as exc:
        logger.warning(
            "Registri model tidak tersinkron (%s). "
            "Pastikan tabel sudah dibuat: `alembic upgrade head`.",
            exc.__class__.__name__,
        )
        logger.debug("Detail sinkronisasi model", exc_info=True)
    except Exception as exc:  # noqa: BLE001 - sinkronisasi registri bukan syarat hidup
        # Registri hanya metadata untuk halaman info model. Kalau artefak
        # menghasilkan nilai aneh (mis. `trained_date` bukan datetime), API tetap
        # harus melayani prediksi daripada mati saat startup.
        logger.warning(
            "Registri model gagal disinkronkan (%s): %s",
            type(exc).__name__,
            exc,
        )
        logger.debug("Detail sinkronisasi model", exc_info=True)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.is_insecure_secret and settings.ENV != "test":
            logger.warning(
                "SECRET_KEY masih nilai contoh/terlalu pendek. "
                "Ganti sebelum deploy (production akan menolak start)."
            )

        model_service = ModelService(settings.artifact_version_dir)
        model_service.load()
        app.state.model_service = model_service
        app.state.geocoding_service = GeocodingService(
            settings.GEOCODING_USER_AGENT,
            timeout=settings.GEOCODING_TIMEOUT,
            min_interval=settings.GEOCODING_MIN_INTERVAL,
        )
        _sync_model_registry(model_service)
        yield

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )
    # Disimpan di app.state supaya dependency membaca settings milik app ini,
    # bukan cache global `get_settings()` (penting saat tes membuat app khusus).
    app.state.settings = settings
    app.state.login_limiter = SlidingWindowLimiter(
        settings.LOGIN_MAX_ATTEMPTS, settings.LOGIN_WINDOW_SECONDS
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def _request_validation_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {"field": _field_name(error), "message": _translate(error)}
            for error in exc.errors()
        ]
        return _validation_response(errors)

    @app.exception_handler(ApiValidationError)
    async def _api_validation_handler(
        _request: Request, exc: ApiValidationError
    ) -> JSONResponse:
        return _validation_response(
            [{"field": e.field, "message": e.message} for e in exc.errors]
        )

    @app.exception_handler(PersistenceError)
    async def _persistence_handler(
        _request: Request, exc: PersistenceError
    ) -> JSONResponse:
        logger.error("PersistenceError: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"detail": "Layanan database sedang bermasalah; coba lagi"},
        )

    @app.exception_handler(ModelUnavailableError)
    async def _model_handler(
        _request: Request, exc: ModelUnavailableError
    ) -> JSONResponse:
        logger.error("ModelUnavailableError: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"detail": str(exc) or "Artefak model belum siap"},
        )

    app.include_router(api_router)

    @app.get("/", tags=["Health"], include_in_schema=False)
    def root() -> dict[str, str]:
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "api": "/api/v1",
        }

    return app


app = create_app()

__all__ = ["app", "create_app"]
