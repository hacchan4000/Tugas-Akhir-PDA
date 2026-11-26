"""Konfigurasi aplikasi dari environment / `.env` (pydantic-settings).

Semua path default dihitung relatif terhadap root `backend/`, bukan terhadap
current working directory, supaya `uvicorn app.main:app` tetap benar walau
dijalankan dari mana saja.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent

# Nilai contoh yang TIDAK boleh dipakai di production.
PLACEHOLDER_SECRETS = frozenset(
    {
        "",
        "ganti-dengan-string-acak-panjang",
        "dev-insecure-secret-change-me",
        "dev-insecure-secret-change-me-32bytes",
        "ubah-secret-key-pada-production",
        "secret",
        "changeme",
    }
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_NAME: str = "Sistem Klasifikasi Ukuran Tanah Longsor BASARNAS"
    APP_VERSION: str = "1.0.0"
    ENV: Literal["development", "production", "test"] = "development"

    # --- Database ---------------------------------------------------------
    # PostgreSQL: postgresql+psycopg://user:pass@host:5432/db?sslmode=require
    # Lokal tanpa Supabase: sqlite:///./basarnas.db
    DATABASE_URL: str = f"sqlite:///{(BACKEND_ROOT / 'basarnas.db').as_posix()}"
    DB_ECHO: bool = False

    # --- Auth -------------------------------------------------------------
    SECRET_KEY: str = "dev-insecure-secret-change-me-32bytes"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=1, le=60 * 24 * 7)
    COOKIE_NAME: str = "access_token"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"

    # --- Rate limit login -------------------------------------------------
    # Dihitung per alamat IP klien dan disimpan di memori proses (lihat
    # app/utils/rate_limit.py untuk batasannya).
    LOGIN_MAX_ATTEMPTS: int = Field(default=5, ge=1, le=100)
    LOGIN_WINDOW_SECONDS: int = Field(default=300, ge=1, le=24 * 60 * 60)

    # --- CORS -------------------------------------------------------------
    CORS_ORIGINS: str = "http://localhost:3000"

    # --- Artefak model ----------------------------------------------------
    # ARTIFACT_DIR adalah folder induk; versi aktif = ARTIFACT_DIR / MODEL_VERSION
    ARTIFACT_DIR: Path = BACKEND_ROOT / "artifacts"
    MODEL_VERSION: str = "v1"

    # --- Geocoding (Nominatim) -------------------------------------------
    GEOCODING_USER_AGENT: str = "basarnas-landslide-classifier"
    GEOCODING_TIMEOUT: float = Field(default=2.0, gt=0, le=30)
    GEOCODING_MIN_INTERVAL: float = Field(default=1.0, ge=0, le=10)

    @field_validator("SECRET_KEY")
    @classmethod
    def _strip_secret(cls, value: str) -> str:
        return value.strip()

    @field_validator("ARTIFACT_DIR")
    @classmethod
    def _resolve_artifact_dir(cls, value: Path) -> Path:
        return value if value.is_absolute() else (BACKEND_ROOT / value)

    @model_validator(mode="after")
    def _validate_security(self) -> "Settings":
        if self.COOKIE_SAMESITE == "none" and not self.COOKIE_SECURE:
            raise ValueError(
                "COOKIE_SAMESITE='none' mewajibkan COOKIE_SECURE=true "
                "(browser menolak cookie SameSite=None tanpa Secure)"
            )
        if "*" in self.cors_origins:
            # CORS dengan wildcard + cookie = siapa pun bisa membaca respons
            # atas nama operator yang sedang login. Starlette bahkan memantulkan
            # origin pemanggil, jadi tidak ada perlindungan sama sekali.
            raise ValueError(
                "CORS_ORIGINS tidak boleh '*' karena cookie sesi dikirim "
                "(allow_credentials=true). Sebutkan origin frontend secara eksplisit."
            )
        if self.ENV == "production" and not self.COOKIE_SECURE:
            raise ValueError(
                "ENV=production mewajibkan COOKIE_SECURE=true supaya cookie sesi "
                "tidak terkirim lewat HTTP."
            )
        if self.ENV == "production" and self.is_insecure_secret:
            raise ValueError(
                "SECRET_KEY masih nilai contoh/terlalu pendek. "
                'Buat dengan: python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )
        return self

    @property
    def is_insecure_secret(self) -> bool:
        return self.SECRET_KEY in PLACEHOLDER_SECRETS or len(self.SECRET_KEY) < 32

    @property
    def cors_origins(self) -> list[str]:
        """Origin tanpa spasi dan tanpa slash di akhir (wajib untuk CORS)."""
        return [
            origin.strip().rstrip("/")
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def artifact_version_dir(self) -> Path:
        return self.ARTIFACT_DIR / self.MODEL_VERSION

    @property
    def access_token_max_age(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES * 60


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cache supaya `.env` hanya dibaca sekali per proses."""
    return Settings()
