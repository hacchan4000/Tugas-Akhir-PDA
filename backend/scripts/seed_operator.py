"""CLI membuat / memperbarui akun operator pertama.

Contoh (dari folder `backend/`):
    python -m scripts.seed_operator --name "Operator BASARNAS" --email ops@basarnas.go.id
    python -m scripts.seed_operator --email ops@basarnas.go.id --update-password

Butuh tabel `users` sudah dibuat: `alembic upgrade head`.

Password sebaiknya diketik lewat prompt (tanpa `--password`) agar tidak tersimpan
di shell history. Pada shell non-interaktif (CI), `--password` wajib diisi.
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

from app.db.models import User  # noqa: E402
from app.db.repositories import user_repo  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.utils.security import BCRYPT_MAX_BYTES, hash_password  # noqa: E402

_email_adapter = TypeAdapter(EmailStr)
_NAME_MAX = 100


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed akun operator BASARNAS")
    parser.add_argument("--name", help="Nama operator (maks. 100 karakter)")
    parser.add_argument("--email", help="Email login operator")
    parser.add_argument(
        "--password",
        help="Password (min. 8 karakter); kosong = prompt interaktif",
    )
    parser.add_argument(
        "--update-password",
        action="store_true",
        help="Perbarui password bila email sudah terdaftar",
    )
    return parser.parse_args(argv)


def _is_interactive() -> bool:
    """True hanya jika prompt benar-benar bisa ditampilkan ke terminal.

    `stdin.isatty()` saja tidak cukup di Windows: device `NUL` juga dilaporkan
    sebagai character device, sehingga `getpass` bisa menggantung menunggu
    keypress pada proses otomatis. Karena itu stdout juga harus TTY.
    """
    try:
        return bool(sys.stdin and sys.stdin.isatty() and sys.stdout.isatty())
    except (AttributeError, ValueError):
        return False


def _clean_name(raw: str) -> str:
    name = raw.strip()
    if not name:
        raise ValueError("nama tidak boleh kosong")
    if len(name) > _NAME_MAX:
        raise ValueError(f"nama maksimal {_NAME_MAX} karakter")
    return name


def _prompt_name() -> str:
    if not _is_interactive():
        raise ValueError("--name wajib diisi pada shell non-interaktif")
    try:
        return _clean_name(input("Nama operator: "))
    except EOFError as exc:  # stdin tertutup walau terdeteksi sebagai TTY
        raise ValueError("--name wajib diisi (stdin tidak tersedia)") from exc


def _prompt_email(raw: str | None) -> str:
    if raw is None:
        if not _is_interactive():
            raise ValueError("--email wajib diisi pada shell non-interaktif")
        try:
            raw = input("Email operator: ")
        except EOFError as exc:
            raise ValueError("--email wajib diisi (stdin tidak tersedia)") from exc
    try:
        return str(_email_adapter.validate_python(raw.strip()))
    except ValidationError as exc:
        raise ValueError(f"email tidak valid: {raw!r}") from exc


def _resolve_password(raw: str | None) -> str:
    if raw is not None:
        password = raw
    elif _is_interactive():
        try:
            password = getpass.getpass("Password (min. 8 karakter): ")
            confirmation = getpass.getpass("Ulangi password: ")
        except EOFError as exc:
            raise ValueError("--password wajib diisi (stdin tidak tersedia)") from exc
        if password != confirmation:
            raise ValueError("konfirmasi password tidak sama")
    else:
        raise ValueError("--password wajib diisi pada shell non-interaktif")

    if len(password) < 8:
        raise ValueError("password minimal 8 karakter")
    if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        raise ValueError(f"password maksimal {BCRYPT_MAX_BYTES} byte")
    return password


def _update_existing(db, user: User, *, name: str | None, password: str) -> None:
    user_repo.update_password(db, user, hash_password(password))
    if name is not None:
        user.name = name
    db.commit()


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        email = _prompt_email(args.email)
        # Nama hanya wajib saat membuat akun baru; untuk update password opsional.
        name = _clean_name(args.name) if args.name is not None else None
    except ValueError as exc:
        print(f"[gagal] {exc}", file=sys.stderr)
        return 2

    try:
        with SessionLocal() as db:
            existing = user_repo.get_by_email(db, email)

            if existing is not None and not args.update_password:
                print(
                    f"[info] {email} sudah terdaftar (user_id={existing.user_id}). "
                    "Pakai --update-password untuk mengganti password."
                )
                return 1

            if existing is None and name is None:
                try:
                    name = _prompt_name()
                except ValueError as exc:
                    print(f"[gagal] {exc}", file=sys.stderr)
                    return 2

            password = _resolve_password(args.password)

            if existing is not None:
                _update_existing(db, existing, name=name, password=password)
                print(
                    f"[ok] Password diperbarui untuk user_id={existing.user_id} ({email})"
                )
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
    except ValueError as exc:
        print(f"[gagal] {exc}", file=sys.stderr)
        return 2
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
