"""Keamanan: hashing password (bcrypt) dan JWT (PyJWT).

Catatan penting:
- `bcrypt` hanya memakai 72 byte pertama password. Alih-alih membiarkan
  password panjang terpotong diam-diam, kita menolaknya secara eksplisit.
- Modul ini memakai `PyJWT`, bukan `python-jose` (lihat requirements.txt).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import get_settings

BCRYPT_MAX_BYTES = 72
_ALLOWED_ALGORITHMS = frozenset({"HS256", "HS384", "HS512"})

# Hash dummy: dipakai agar verifikasi tetap memakan waktu yang sama ketika
# email tidak ditemukan (mencegah user enumeration lewat timing).
_DUMMY_HASH = "$2b$12$jpUhdzohRWqlTIlS8Fi6RecmMNFf/55B.YrAQXMPTLceKY9D4xTxu"


def _encode_password(password: str) -> bytes:
    if not isinstance(password, str):
        raise TypeError("password harus berupa string")
    raw = password.encode("utf-8")
    if len(raw) > BCRYPT_MAX_BYTES:
        raise ValueError(
            f"password terlalu panjang: {len(raw)} byte (maksimal {BCRYPT_MAX_BYTES} byte)"
        )
    return raw


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_encode_password(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_encode_password(password), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # Hash korup / password kebanyakan byte -> anggap gagal, jangan 500.
        return False


def verify_dummy_password(password: str) -> None:
    """Jalankan bcrypt pada hash dummy (penyeimbang waktu saat email tidak ada)."""
    verify_password(password, _DUMMY_HASH)


def _algorithm() -> str:
    algorithm = get_settings().JWT_ALGORITHM.upper()
    if algorithm not in _ALLOWED_ALGORITHMS:
        raise RuntimeError(
            f"JWT_ALGORITHM={algorithm!r} tidak diizinkan; pakai {sorted(_ALLOWED_ALGORITHMS)}"
        )
    return algorithm


def create_access_token(
    user_id: int, expires_delta: timedelta | None = None
) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": str(int(user_id)),
        "iat": datetime.now(timezone.utc),
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=_algorithm())


def decode_access_token(token: str) -> int:
    """Kembalikan `user_id`. Melempar `jwt.InvalidTokenError` bila tidak valid."""
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[_algorithm()],
        options={"require": ["exp", "sub"]},
    )
    subject = payload.get("sub")
    if subject is None:
        raise jwt.InvalidTokenError("token tidak memiliki subject")
    return int(subject)


__all__ = [
    "BCRYPT_MAX_BYTES",
    "hash_password",
    "verify_password",
    "verify_dummy_password",
    "create_access_token",
    "decode_access_token",
]
