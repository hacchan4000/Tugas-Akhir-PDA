"""Pagar konfigurasi keamanan yang tidak boleh bisa dilewati lewat `.env`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import Settings

SECRET_KUAT = "kunci-tes-yang-cukup-panjang-dan-bukan-placeholder-48byte"


def _settings(**overrides: object) -> Settings:
    dasar: dict[str, object] = {
        "ENV": "development",
        "SECRET_KEY": SECRET_KUAT,
        "COOKIE_SECURE": False,
        "COOKIE_SAMESITE": "lax",
        "CORS_ORIGINS": "http://localhost:3000",
    }
    dasar.update(overrides)
    return Settings(**dasar)  # type: ignore[arg-type]


def test_wildcard_cors_is_rejected() -> None:
    """`*` + cookie berarti siapa pun bisa membaca respons atas nama operator."""
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        _settings(CORS_ORIGINS="*")


def test_wildcard_cors_is_rejected_even_in_a_list() -> None:
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        _settings(CORS_ORIGINS="http://localhost:3000,*")


def test_explicit_cors_origins_are_accepted() -> None:
    settings = _settings(CORS_ORIGINS="http://localhost:3000, https://app.example.com/")

    assert settings.cors_origins == [
        "http://localhost:3000",
        "https://app.example.com",
    ]


def test_production_requires_secure_cookie() -> None:
    with pytest.raises(ValidationError, match="COOKIE_SECURE"):
        _settings(ENV="production", COOKIE_SECURE=False)


def test_production_requires_strong_secret() -> None:
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        _settings(
            ENV="production",
            COOKIE_SECURE=True,
            SECRET_KEY="dev-insecure-secret-change-me-32bytes",
        )


def test_production_with_secure_cookie_and_strong_secret_is_accepted() -> None:
    settings = _settings(ENV="production", COOKIE_SECURE=True)

    assert settings.ENV == "production"
    assert settings.is_insecure_secret is False


def test_samesite_none_requires_secure_cookie() -> None:
    with pytest.raises(ValidationError, match="COOKIE_SAMESITE"):
        _settings(COOKIE_SAMESITE="none", COOKIE_SECURE=False)


def test_development_may_use_insecure_secret() -> None:
    """Jangan menghalangi pengembangan lokal; hanya production yang ditolak."""
    settings = _settings(SECRET_KEY="dev-insecure-secret-change-me-32bytes")

    assert settings.is_insecure_secret is True
