"""Error domain -> dipetakan ke HTTP oleh exception handler di `app.main`."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FieldError:
    field: str
    message: str


class ApiValidationError(ValueError):
    """Validasi yang butuh konteks runtime (mis. `valid_categories` model).

    Sengaja BUKAN dataclass: `@dataclass(slots=True)` membuat ulang class
    sehingga zero-arg `super()` di `__post_init__` gagal dengan
    "obj must be an instance or subtype of type".
    """

    def __init__(self, errors: list[FieldError] | tuple[FieldError, ...]) -> None:
        self.errors: list[FieldError] = list(errors)
        if not self.errors:
            raise ValueError("ApiValidationError butuh minimal satu FieldError")
        super().__init__("; ".join(f"{e.field}: {e.message}" for e in self.errors))

    @classmethod
    def single(cls, field: str, message: str) -> "ApiValidationError":
        return cls([FieldError(field=field, message=message)])



class PersistenceError(RuntimeError):
    """Kegagalan database saat menyimpan/membaca (bukan salah input user)."""


class ModelUnavailableError(RuntimeError):
    """Artefak model belum siap / gagal dimuat."""
