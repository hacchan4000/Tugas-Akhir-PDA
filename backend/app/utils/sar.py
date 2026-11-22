"""Pemetaan kelas prediksi -> prioritas SAR.

Sumber utama: tabel `sar_priorities` (master data, di-seed migrasi 002).
Fallback: konstanta di bawah ini, dipakai kalau tabel belum ter-seed sehingga
API tetap bisa melayani prediksi (bukan 500).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import SarPriority


@dataclass(frozen=True, slots=True)
class SarPriorityInfo:
    predicted_class: str
    level: str
    recommendation: str


FALLBACK_SAR_PRIORITIES: dict[str, tuple[str, str]] = {
    "small": (
        "Rendah",
        "Perkiraan skala kecil; dapat ditangani setelah kejadian berskala lebih besar",
    ),
    "medium": (
        "Sedang",
        "Perkiraan skala menengah; siapkan sumber daya dan pantau perkembangan",
    ),
    "large": (
        "Tinggi",
        "Perkiraan skala besar; prioritaskan penanganan dan verifikasi lapangan",
    ),
}

VALID_CLASSES: frozenset[str] = frozenset(FALLBACK_SAR_PRIORITIES)


def resolve_sar(db: Session, predicted_class: str) -> SarPriorityInfo:
    normalized = str(predicted_class).strip().lower()
    if normalized not in VALID_CLASSES:
        raise ValueError(
            f"kelas prediksi {predicted_class!r} tidak dikenal; "
            f"harus salah satu dari {sorted(VALID_CLASSES)}"
        )

    record = db.scalar(
        select(SarPriority).where(SarPriority.predicted_class == normalized)
    )
    if record is not None:
        return SarPriorityInfo(
            predicted_class=normalized,
            level=record.sar_priority_level,
            recommendation=record.sar_recommendation,
        )

    level, recommendation = FALLBACK_SAR_PRIORITIES[normalized]
    return SarPriorityInfo(
        predicted_class=normalized,
        level=level,
        recommendation=recommendation,
    )


__all__ = [
    "SarPriorityInfo",
    "FALLBACK_SAR_PRIORITIES",
    "VALID_CLASSES",
    "resolve_sar",
]
