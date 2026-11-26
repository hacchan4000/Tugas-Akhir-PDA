"""Tes ekspor CSV: bentuk berkas dan netralisasi formula injection.

`nama_wilayah` berasal dari Nominatim, yaitu data OpenStreetMap yang bisa
disunting publik. Kalau isinya dimulai `=`, Excel/LibreOffice akan
mengeksekusinya sebagai formula saat berkas dibuka.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterator
from datetime import date, datetime, timezone
from typing import Any

from app.schemas.prediction import PredictionRead
from app.services.export_service import EXPORT_COLUMNS, stream_csv


def _item(**overrides: Any) -> PredictionRead:
    data: dict[str, Any] = {
        "prediction_id": 1,
        "input_id": 1,
        "event_date": date(2024, 1, 1),
        "latitude": -6.2,
        "longitude": 106.8,
        "nama_wilayah": "Jakarta, Indonesia",
        "geocoding_status": "success",
        "landslide_category": "landslide",
        "landslide_trigger": "rain",
        "landslide_setting": "natural_slope",
        "location_accuracy": "exact",
        "predicted_class": "medium",
        "confidence_score": 0.8,
        "probabilities": {"small": 0.1, "medium": 0.8, "large": 0.1},
        "sar_priority_level": "Sedang",
        "sar_recommendation": "Siapkan sumber daya",
        "status": "success",
        "prediction_date": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "model_name": "Random Forest",
        "model_version": "v1",
    }
    data.update(overrides)
    return PredictionRead(**data)


def _rows(*items: PredictionRead) -> list[dict[str, str]]:
    teks = "".join(stream_csv(items))
    parsed = list(csv.reader(io.StringIO(teks)))
    header = parsed[0]
    header[0] = header[0].lstrip("\ufeff")
    return [dict(zip(header, row, strict=True)) for row in parsed[1:]]


def test_header_and_row_shape() -> None:
    rows = _rows(_item())

    assert len(rows) == 1
    assert tuple(rows[0]) == EXPORT_COLUMNS
    assert rows[0]["predicted_class"] == "medium"


def test_neutralizes_formula_prefixes() -> None:
    berbahaya = [
        "=cmd|' /C calc'!A0",
        "+1+1",
        "@SUM(1,1)",
        "\t=1+1",
    ]
    for nilai in berbahaya:
        rows = _rows(_item(nama_wilayah=nilai))
        assert rows[0]["nama_wilayah"].startswith("'"), nilai
        assert rows[0]["nama_wilayah"] == "'" + nilai


def test_neutralizes_dash_string_that_is_not_a_number() -> None:
    rows = _rows(_item(nama_wilayah="-2+3+cmd|' /C calc'!A0"))
    assert rows[0]["nama_wilayah"].startswith("'")

    rows = _rows(_item(nama_wilayah="-Bandung"))
    assert rows[0]["nama_wilayah"].startswith("'")


def test_negative_coordinates_stay_numeric() -> None:
    rows = _rows(_item(latitude=-6.2, longitude=-106.8))

    assert rows[0]["latitude"] == "-6.200000"
    assert rows[0]["longitude"] == "-106.800000"
    assert float(rows[0]["latitude"]) == -6.2


def test_plain_values_untouched() -> None:
    rows = _rows(_item(nama_wilayah="Kota Bandung, Jawa Barat"))

    assert rows[0]["nama_wilayah"] == "Kota Bandung, Jawa Barat"
    assert rows[0]["sar_priority_level"] == "Sedang"


def test_stream_csv_is_lazy() -> None:
    """Generator tidak boleh menarik seluruh riwayat sebelum baris pertama."""
    dikonsumsi: list[int] = []

    def items() -> Iterator[PredictionRead]:
        for i in range(5):
            dikonsumsi.append(i)
            yield _item(prediction_id=i + 1)

    stream = stream_csv(items())
    assert dikonsumsi == [], "belum ada baris yang boleh diambil sebelum iterasi"

    next(stream)  # header
    assert dikonsumsi == []

    next(stream)  # baris pertama
    assert dikonsumsi == [0]

    next(stream)
    assert dikonsumsi == [0, 1]
