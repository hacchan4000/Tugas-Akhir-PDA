"""Penjaga terjemahan pesan validasi: tidak boleh ada teks Inggris yang bocor.

`app/main._ERROR_MESSAGES` memetakan `error["type"]` Pydantic v2 ke bahasa
Indonesia. Kalau schema berubah dan memunculkan tipe error baru, tanpa tes ini
pesan Inggris akan lolos diam-diam ke pengguna.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import _ERROR_MESSAGES, _translate
from app.schemas.auth import LoginRequest
from app.schemas.prediction import PredictionCreate

DASAR: dict[str, Any] = {
    "event_date": date.today().isoformat(),
    "latitude": -6.2,
    "longitude": 106.8,
    "landslide_category": "landslide",
    "landslide_trigger": "rain",
    "landslide_setting": "natural_slope",
    "location_accuracy": "exact",
}

KASUS_PREDIKSI: dict[str, Any] = {
    "field hilang": {k: v for k, v in DASAR.items() if k != "latitude"},
    "field asing": {**DASAR, "warna": "merah"},
    "latitude NaN": {**DASAR, "latitude": float("nan")},
    "latitude Infinity": {**DASAR, "latitude": float("inf")},
    "latitude bukan angka": {**DASAR, "latitude": "abc"},
    "latitude terlalu besar": {**DASAR, "latitude": 91.0},
    "latitude tipe salah": {**DASAR, "latitude": [1, 2]},
    "tanggal salah format": {**DASAR, "event_date": "31-12-2024"},
    "tanggal tidak ada": {**DASAR, "event_date": "2024-02-31"},
    "tanggal masa depan": {
        **DASAR,
        "event_date": (date.today() + timedelta(days=30)).isoformat(),
    },
    "kategori kosong": {**DASAR, "landslide_category": ""},
    "kategori bukan string": {**DASAR, "landslide_category": 123},
    "kategori terlalu panjang": {**DASAR, "landslide_category": "x" * 51},
    "body bukan objek": ["bukan", "objek"],
}

KASUS_LOGIN: dict[str, Any] = {
    "email bukan email": {"email": "bukan-email", "password": "rahasia123"},
    "password kosong": {"email": "a@b.co", "password": ""},
    "password bukan string": {"email": "a@b.co", "password": 12345},
    "email hilang": {"password": "rahasia123"},
}


def _types() -> set[tuple[str, str]]:
    hasil: set[tuple[str, str]] = set()
    for label, payload in KASUS_PREDIKSI.items():
        with pytest.raises(ValidationError) as info:
            PredictionCreate.model_validate(payload)
        for error in info.value.errors():
            hasil.add((str(error["type"]), label))
    for label, payload in KASUS_LOGIN.items():
        with pytest.raises(ValidationError) as info:
            LoginRequest.model_validate(payload)
        for error in info.value.errors():
            hasil.add((str(error["type"]), label))
    return hasil


def test_every_produced_error_type_has_an_indonesian_message() -> None:
    belum = sorted(
        {
            tipe
            for tipe, _ in _types()
            if tipe not in _ERROR_MESSAGES and tipe != "value_error"
        }
    )

    assert not belum, (
        "tipe error Pydantic berikut belum punya terjemahan di "
        f"app.main._ERROR_MESSAGES: {belum}"
    )


def test_translation_never_returns_the_english_default() -> None:
    for tipe, label in sorted(_types()):
        if tipe == "value_error":
            # `value_error` sengaja diteruskan apa adanya: pesannya berasal dari
            # validator kita sendiri yang sudah berbahasa Indonesia.
            continue
        pesan = _translate({"type": tipe, "msg": "raw english message"})
        assert pesan != "raw english message", f"{tipe} ({label}) tidak diterjemahkan"


def test_email_error_is_translated() -> None:
    pesan = _translate(
        {
            "type": "value_error",
            "msg": "value is not a valid email address: An email address must have an @-sign.",
        }
    )
    assert pesan == "format email tidak valid"


def test_own_validator_message_is_kept() -> None:
    """Pesan buatan kita sendiri sudah Indonesia; jangan ditimpa."""
    pesan = _translate(
        {"type": "value_error", "msg": "Value error, tanggal tidak boleh di masa depan"}
    )
    assert pesan == "tanggal tidak boleh di masa depan"


def test_http_422_body_is_indonesian() -> None:
    """Lewat HTTP sungguhan, pesan tidak boleh kembali ke bahasa Inggris."""
    from collections.abc import Iterator

    from app.dependencies.deps import get_db
    from app.main import create_app

    def _db_tidak_dipakai() -> Iterator[None]:
        # Validasi body gagal sebelum endpoint berjalan, jadi DB tidak dipakai.
        yield None

    app = create_app()
    app.dependency_overrides[get_db] = _db_tidak_dipakai
    # Tanpa `with`: lifespan (muat artefak + sinkron registri ke DATABASE_URL
    # asli) tidak dijalankan, dan tes ini memang tidak membutuhkannya.
    client = TestClient(app)
    try:
        response = client.post(
            "/api/v1/auth/login", json={"email": "bukan-email", "password": 12345}
        )
    finally:
        client.close()

    assert response.status_code == 422
    messages = {item["message"] for item in response.json()["detail"]}
    assert "format email tidak valid" in messages
    assert "harus berupa teks" in messages
