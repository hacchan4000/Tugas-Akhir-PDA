"""Reverse geocoding via Geopy Nominatim.

Aturan SPEC:
- timeout 2 detik,
- rate limit 1 request/detik (global, dijaga `threading.Lock`),
- bahasa "id",
- fallback `nama_wilayah=None` bila gagal / di laut.
"""

from __future__ import annotations

import logging
import threading
import time

from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim

logger = logging.getLogger(__name__)

GEOCODING_SUCCESS = "success"
GEOCODING_NOT_FOUND = "not_found"
GEOCODING_ERROR = "error"

# Urutan prioritas komponen alamat yang ditampilkan ke operator.
_ADDRESS_KEYS = (
    "state",
    "province",
    "region",
    "city",
    "town",
    "municipality",
    "county",
    "district",
    "suburb",
    "village",
    "hamlet",
)

_MAX_REGION_LENGTH = 255  # sinkron dengan kolom input_data.nama_wilayah


class GeocodingService:
    def __init__(
        self,
        user_agent: str,
        *,
        timeout: float = 2.0,
        min_interval: float = 1.0,
        language: str = "id",
    ) -> None:
        self._geolocator = Nominatim(user_agent=user_agent, timeout=timeout)
        self._language = language
        self._min_interval = max(0.0, float(min_interval))
        self._lock = threading.Lock()
        self._last_call = 0.0

    def _throttle(self) -> None:
        """Serialisasi pemanggilan: lock dipegang selama menunggu jeda."""
        with self._lock:
            elapsed = time.monotonic() - self._last_call
            remaining = self._min_interval - elapsed
            if remaining > 0:
                time.sleep(remaining)
            self._last_call = time.monotonic()

    def reverse(self, latitude: float, longitude: float) -> tuple[str | None, str]:
        """Kembalikan `(nama_wilayah, geocoding_status)`; tidak pernah melempar."""
        self._throttle()
        try:
            location = self._geolocator.reverse(
                (float(latitude), float(longitude)),
                language=self._language,
                exactly_one=True,
                addressdetails=True,
            )
        except (GeocoderTimedOut, GeocoderServiceError, TimeoutError):
            logger.warning("Reverse geocoding gagal (timeout/layanan) untuk %s,%s", latitude, longitude)
            return None, GEOCODING_ERROR
        except Exception:  # noqa: BLE001 - geopy bisa melempar error transport lain
            logger.exception("Reverse geocoding error tak terduga untuk %s,%s", latitude, longitude)
            return None, GEOCODING_ERROR

        if location is None:
            # Koordinat di laut / tidak ada data alamat.
            return None, GEOCODING_NOT_FOUND

        region = self._format_region(getattr(location, "raw", None))
        if not region:
            return None, GEOCODING_NOT_FOUND
        return region, GEOCODING_SUCCESS

    @staticmethod
    def _format_region(raw: object) -> str | None:
        if not isinstance(raw, dict):
            return None
        address = raw.get("address")
        if not isinstance(address, dict):
            return None

        parts: list[str] = []
        for key in _ADDRESS_KEYS:
            value = address.get(key)
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned and cleaned not in parts:
                    parts.append(cleaned)
        if not parts:
            return None
        return ", ".join(parts)[:_MAX_REGION_LENGTH]


__all__ = [
    "GeocodingService",
    "GEOCODING_SUCCESS",
    "GEOCODING_NOT_FOUND",
    "GEOCODING_ERROR",
]
