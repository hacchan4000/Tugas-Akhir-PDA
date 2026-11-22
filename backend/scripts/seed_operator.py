"""CLI membuat / memperbarui akun operator pertama.

Contoh (dari folder `backend/`):
    python -m scripts.seed_operator --name "Operator BASARNAS" --email ops@basarnas.go.id
    python -m scripts.seed_operator --email ops@basarnas.go.id --update-password

Butuh tabel `users` sudah dibuat: `alembic upgrade head`.
"""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from pydantic import EmailStr, TypeAdapter, ValidationError  # noqa: E402
from sqlalchemy.exc import SQLAlchemyError  # noqa: E402

from app.db.repositories import user_repo  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.utils.security import BCRYPT_MAX_BYTES, hash_password  # noqa: E402

_email_adapter = TypeAdapter(EmailStr)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed akun operator BASARNAS")
    parser.add_argument("--name", help="Nama operator (maks. 100 karakter)")
    parser.add_argument("--email", help="Email login operator")
    parser.add_argument("--password", help="Password (min. 8 karakter); kosong = prompt")
    parser.add_argument(
        "--update-password",
        action="store_true",
        help="Perbarui password bila email sudah terdaftar",
    )
    return parser.parse_args(argv)


def _prompt_name() -> str:
    name = input("Nama operator: ").strip()
    if not name:
        raise ValueError("nama tidak boleh kosong")
    if len(name) > 100:
        raise ValueError("nama maksimal 100 karakter")
    return name


def _prompt_email(raw: str | None) -> str:
    value = raw if raw is not None else input("Email operator: ")
    try:
        return str(_email_adapter.validate_python(value.strip()))
    except ValidationError as exc:
        raise ValueError(f"email tidak valid: {value!r}") from exc


def _resolve_password(raw: str | None) -> str:
    if raw is not None:
        password = raw
    else:
        password = getpass.getpass("Password (min. 8 karakter): ")
        confirmation = getpass.getpass("Ulangi password: ")
        if password != confirmation:
            raise ValueError("konfirmasi password tidak sama")

    if len(password) < 8:
        raise ValueError("password minimal 8 karakter")
    if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        raise ValueError(f"password maksimal {BCRYPT_MAX_BYTES} byte")
    return password


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        email = _prompt_email(args.email)
        password = _resolve_password(args.password)
        name = args.name.strip() if args.name else None
        if name is not None:
            if not name:
                raise ValueError("nama tidak boleh kosong")
            if len(name) > 100:
                raise ValueError("nama maksimal 100 karakter")
        elif not args.update_password:
            name = _prompt_name()
    except ValueError as exc:
        print(f"[gagal] {exc}", file=sys.stderr)
        return 2

    try:
        with SessionLocal() as db:
            existing = user_repo.get_by_email(db, email)

            if existing is not None:
                if not args.update_password:
                    print(
                        f"[info] {email} sudah terdaftar (user_id={existing.user_id}). "
                        "Pakai --update-password untuk mengganti password."
                    )
                    return 1
                user_repo.update_password(db, existing, hash_password(password))
                if name:
                    existing.name = name
                db.commit()
                print(f"[ok] Password diperbarui untuk user_id={existing.user_id} ({email})")
                return 0

            user = user_repo.create(
                db,
                name=name or "Operator",
                email=email,
                password_hash=hash_password(password),
            )
            db.commit()
            print(f"[ok] Operator dibuat: user_id={user.user_id} email={user.email}")
            return 0
    except SQLAlchemyError as exc:
        print(
            "[gagal] Tidak bisa mengakses tabel `users`. "
            "Jalankan `alembic upgrade head` lebih dulu.\n"
            f"Detail: {exc.__class__.__name__}",
            file=sys.stderr,
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
