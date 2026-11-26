"""Kontrak CLI `scripts/seed_operator.py` (dijalankan sebagai subprocess).

Regresi yang dijaga: tanpa `--name`/`--password` pada shell non-interaktif,
CLI harus berhenti dengan pesan jelas (exit 2), bukan traceback `EOFError`.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from app.utils.security import verify_password

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "rahasia-operator-123"


@pytest.fixture()
def cli_env(tmp_path: Path) -> tuple[dict[str, str], Path]:
    db_path = tmp_path / "cli.db"
    url = f"sqlite:///{db_path.as_posix()}"

    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")

    env = {**os.environ, "DATABASE_URL": url, "ENV": "test"}
    return env, db_path


def _run(env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "scripts.seed_operator", *args],
        cwd=BACKEND_ROOT,
        env=env,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        timeout=120,
    )


def _user_row(db_path: Path) -> tuple[str, str] | None:
    with sqlite3.connect(db_path) as conn:
        return conn.execute("SELECT name, password_hash FROM users").fetchone()


def test_create_then_duplicate_then_update_password(cli_env) -> None:
    env, db_path = cli_env

    created = _run(
        env,
        "--name",
        "Operator CLI",
        "--email",
        "cli@example.com",
        "--password",
        PASSWORD,
    )
    assert created.returncode == 0, created.stderr
    assert "Operator dibuat" in created.stdout

    row = _user_row(db_path)
    assert row is not None
    assert row[0] == "Operator CLI"
    assert verify_password(PASSWORD, row[1])

    duplicate = _run(env, "--email", "cli@example.com", "--password", PASSWORD)
    assert duplicate.returncode == 1
    assert "sudah terdaftar" in duplicate.stdout
    assert "Traceback" not in duplicate.stderr

    updated = _run(
        env,
        "--email",
        "cli@example.com",
        "--password",
        "password-baru-456",
        "--update-password",
    )
    assert updated.returncode == 0, updated.stderr

    row = _user_row(db_path)
    assert row is not None
    assert verify_password("password-baru-456", row[1])
    assert not verify_password(PASSWORD, row[1])


def test_missing_name_or_password_fails_cleanly(cli_env) -> None:
    env, db_path = cli_env

    without_name = _run(
        env, "--email", "baru@example.com", "--password", PASSWORD
    )
    assert without_name.returncode == 2
    assert "--name wajib diisi" in without_name.stderr
    assert "Traceback" not in without_name.stderr

    without_password = _run(env, "--name", "Tanpa Password", "--email", "x@example.com")
    assert without_password.returncode == 2
    assert "--password wajib diisi" in without_password.stderr
    assert "Traceback" not in without_password.stderr

    assert _user_row(db_path) is None
