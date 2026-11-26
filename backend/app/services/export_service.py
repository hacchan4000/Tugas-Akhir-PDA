"""Ekspor CSV riwayat prediksi (ditulis per baris agar respons cepat)."""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable, Iterator

from app.schemas.prediction import PredictionRead

EXPORT_FILENAME = "riwayat_prediksi.csv"

EXPORT_COLUMNS: tuple[str, ...] = (
    "prediction_id",
    "event_date",
    "latitude",
    "longitude",
    "nama_wilayah",
    "geocoding_status",
    "landslide_category",
    "landslide_trigger",
    "landslide_setting",
    "location_accuracy",
    "predicted_class",
    "confidence_score",
    "sar_priority_level",
    "sar_recommendation",
    "status",
    "prediction_date",
    "model_name",
    "model_version",
)

# Karakter pertama yang membuat Excel/LibreOffice mengeksekusi sel sebagai formula.
_FORMULA_PREFIXES = frozenset({"=", "+", "@", "\t", "\r", "\n"})


def _neutralize(value: object) -> object:
    """Cegah CSV formula injection saat berkas dibuka di Excel/LibreOffice.

    `nama_wilayah` berasal dari Nominatim (data OpenStreetMap yang bisa disunting
    publik), jadi isinya tidak boleh dipercaya. Sel yang dimulai `=`, `+`, `@`,
    tab, atau CR akan dieksekusi sebagai formula oleh Excel.

    `-` hanya dinetralkan bila isinya bukan angka, supaya koordinat negatif
    seperti ``-6.200000`` tetap terbaca sebagai angka.
    """
    if not isinstance(value, str) or not value:
        return value
    stripped = value.lstrip(" ")
    if not stripped:
        return value
    if stripped[0] in _FORMULA_PREFIXES:
        return "'" + value
    if stripped[0] == "-":
        try:
            float(stripped)
        except ValueError:
            return "'" + value
    return value


def _row_values(item: PredictionRead) -> list[object]:
    values: list[object] = [
        item.prediction_id,
        item.event_date.isoformat(),
        f"{item.latitude:.6f}",
        f"{item.longitude:.6f}",
        item.nama_wilayah or "",
        item.geocoding_status,
        item.landslide_category,
        item.landslide_trigger,
        item.landslide_setting,
        item.location_accuracy,
        item.predicted_class,
        f"{item.confidence_score:.6f}",
        item.sar_priority_level,
        item.sar_recommendation,
        item.status,
        item.prediction_date.isoformat(),
        item.model_name,
        item.model_version,
    ]
    return [_neutralize(value) for value in values]


def stream_csv(items: Iterable[PredictionRead]) -> Iterator[str]:
    """Yield potongan CSV. BOM UTF-8 di awal agar Excel membaca non-ASCII."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(EXPORT_COLUMNS)
    yield "\ufeff" + buffer.getvalue()

    for item in items:
        buffer.seek(0)
        buffer.truncate(0)
        writer.writerow(_row_values(item))
        yield buffer.getvalue()


__all__ = ["EXPORT_COLUMNS", "EXPORT_FILENAME", "stream_csv"]
