"""Kontrak skema database: migrasi Alembic vs SPEC.md bagian 3.1 & 3.2.

Tes ini menjalankan `alembic upgrade head` sungguhan pada SQLite sementara,
lalu memeriksa tabel, kolom, tipe, nullability, index, foreign key, dan isi
seed `sar_priorities`. Tujuannya: setiap penyimpangan dari SPEC gagal di CI,
bukan ditemukan saat deploy.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config

BACKEND_ROOT = Path(__file__).resolve().parents[1]

# SPEC 3.1: urutan kolom sesuai rancangan entitas-atribut.
EXPECTED_COLUMNS: dict[str, list[tuple[str, str, bool]]] = {
    # (nama, tipe SQLite, notnull)
    "users": [
        ("user_id", "INTEGER", True),
        ("name", "VARCHAR(100)", True),
        ("email", "VARCHAR(255)", True),
        ("password_hash", "VARCHAR(255)", True),
        ("created_at", "DATETIME", True),
    ],
    "models": [
        ("model_id", "INTEGER", True),
        ("model_name", "VARCHAR(50)", True),
        ("best_params", "JSON", True),
        ("model_version", "VARCHAR(50)", True),
        ("model_status", "VARCHAR(20)", True),
        ("trained_date", "DATETIME", True),
    ],
    "sar_priorities": [
        ("sar_id", "INTEGER", True),
        ("predicted_class", "VARCHAR(10)", True),
        ("sar_priority_level", "VARCHAR(20)", True),
        ("sar_recommendation", "TEXT", True),
    ],
    "input_data": [
        ("input_id", "INTEGER", True),
        ("user_id", "INTEGER", True),
        ("event_date", "DATE", True),
        ("latitude", "DOUBLE", True),
        ("longitude", "DOUBLE", True),
        ("landslide_category", "VARCHAR(50)", True),
        ("landslide_trigger", "VARCHAR(50)", True),
        ("landslide_setting", "VARCHAR(50)", True),
        ("location_accuracy", "VARCHAR(50)", True),
        ("nama_wilayah", "VARCHAR(255)", False),
        ("geocoding_status", "VARCHAR(20)", True),
        ("created_at", "DATETIME", True),
    ],
    "predictions": [
        ("prediction_id", "INTEGER", True),
        ("input_id", "INTEGER", True),
        ("model_id", "INTEGER", True),
        ("predicted_class", "VARCHAR(10)", True),
        ("confidence_score", "DOUBLE", True),
        ("probabilities", "JSON", True),
        ("status", "VARCHAR(20)", True),
        ("prediction_date", "DATETIME", True),
    ],
}

EXPECTED_SAR_ROWS: list[tuple[str, str, str]] = [
    (
        "small",
        "Rendah",
        "Perkiraan skala kecil; dapat ditangani setelah kejadian berskala lebih besar",
    ),
    (
        "medium",
        "Sedang",
        "Perkiraan skala menengah; siapkan sumber daya dan pantau perkembangan",
    ),
    (
        "large",
        "Tinggi",
        "Perkiraan skala besar; prioritaskan penanganan dan verifikasi lapangan",
    ),
]


@pytest.fixture(scope="module")
def migrated_db(tmp_path_factory: pytest.TempPathFactory) -> sqlite3.Connection:
    """Jalankan seluruh migrasi pada database SQLite sementara."""
    db_path = tmp_path_factory.mktemp("migration") / "spec.db"
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")

    command.upgrade(config, "head")

    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
    finally:
        connection.close()


def _table_info(conn: sqlite3.Connection, table: str) -> list[tuple[Any, ...]]:
    return list(conn.execute(f"PRAGMA table_info({table})"))


def _schema_sql(conn: sqlite3.Connection, name: str) -> str:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE name = ?", (name,)
    ).fetchone()
    assert row is not None and row[0], f"objek {name!r} tidak ada di database"
    return str(row[0])


def test_all_spec_tables_exist(migrated_db: sqlite3.Connection) -> None:
    tables = {
        row[0]
        for row in migrated_db.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert tables == {"alembic_version", *EXPECTED_COLUMNS}


@pytest.mark.parametrize("table", sorted(EXPECTED_COLUMNS))
def test_columns_match_spec(migrated_db: sqlite3.Connection, table: str) -> None:
    actual = [(row[1], row[2].upper(), bool(row[3])) for row in _table_info(migrated_db, table)]
    expected = [
        (name, type_.upper(), notnull) for name, type_, notnull in EXPECTED_COLUMNS[table]
    ]
    assert actual == expected


def test_predictions_status_has_db_default(migrated_db: sqlite3.Connection) -> None:
    status = next(
        row for row in _table_info(migrated_db, "predictions") if row[1] == "status"
    )
    assert status[4] is not None
    assert "success" in str(status[4])


def test_history_index_uses_descending_created_at(
    migrated_db: sqlite3.Connection,
) -> None:
    sql = " ".join(_schema_sql(migrated_db, "ix_input_data_user_created").upper().split())
    assert "USER_ID" in sql
    assert "CREATED_AT DESC" in sql


def test_region_index_exists(migrated_db: sqlite3.Connection) -> None:
    sql = _schema_sql(migrated_db, "ix_input_data_user_region")
    assert "user_id" in sql
    assert "nama_wilayah" in sql


def test_only_one_active_model_allowed(migrated_db: sqlite3.Connection) -> None:
    sql = _schema_sql(migrated_db, "uq_models_single_active")
    normalized = " ".join(sql.split())
    assert "UNIQUE INDEX" in normalized.upper()
    assert "WHERE model_status = 'active'" in normalized


def test_foreign_keys_and_actions(migrated_db: sqlite3.Connection) -> None:
    def fks(table: str) -> dict[str, tuple[str, str]]:
        return {
            row[3]: (row[2], row[6])
            for row in migrated_db.execute(f"PRAGMA foreign_key_list({table})")
        }

    assert fks("input_data") == {"user_id": ("users", "CASCADE")}
    assert fks("predictions") == {
        "input_id": ("input_data", "CASCADE"),
        "model_id": ("models", "RESTRICT"),
        "predicted_class": ("sar_priorities", "RESTRICT"),
    }


def test_sar_priorities_seeded_exactly(migrated_db: sqlite3.Connection) -> None:
    rows = list(
        migrated_db.execute(
            "SELECT predicted_class, sar_priority_level, sar_recommendation "
            "FROM sar_priorities ORDER BY sar_id"
        )
    )
    assert rows == EXPECTED_SAR_ROWS


def test_seed_migration_is_recorded(migrated_db: sqlite3.Connection) -> None:
    version = migrated_db.execute("SELECT version_num FROM alembic_version").fetchone()
    assert version is not None
    assert version[0] == "002_seed_sar_priorities"
