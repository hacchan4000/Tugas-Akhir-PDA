"""Tes jalur artefak: pemuatan nyata, degradasi saat rusak, dan pagar keamanan.

Berbeda dari `test_api.py` (yang memakai `FakeModelService`), tes ini memakai
artefak hasil notebook yang sesungguhnya — jalur yang paling sering berubah
setiap kali model dilatih ulang, dan satu-satunya yang belum punya tes.

Semua tes bekerja pada salinan `artifacts/v1` di folder temp.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.core import CLASS_LABELS
from app.db.base import Base
from app.services.model_service import ModelService

BACKEND_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_V1 = BACKEND_ROOT / "artifacts" / "v1"

pytestmark = pytest.mark.skipif(
    not (ARTIFACT_V1 / "model_meta.json").is_file(),
    reason="artefak v1 belum ada; jalankan notebooks/training.ipynb",
)


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def artifact_copy(tmp_path_factory: pytest.TempPathFactory) -> Path:
    tujuan = tmp_path_factory.mktemp("artifacts") / "v1"
    shutil.copytree(ARTIFACT_V1, tujuan)
    return tujuan


@pytest.fixture(scope="module")
def meta(artifact_copy: Path) -> dict[str, Any]:
    return json.loads((artifact_copy / "model_meta.json").read_text(encoding="utf-8"))


@pytest.fixture()
def salinan(artifact_copy: Path, tmp_path: Path) -> Path:
    """Salinan segar per tes supaya kerusakan tidak bocor antar tes."""
    tujuan = tmp_path / "v1"
    shutil.copytree(artifact_copy, tujuan)
    return tujuan


def active_model_file(meta: dict[str, Any]) -> str:
    berkas = (meta.get("artifact_files") or {}).get("model")
    if berkas:
        return str(berkas)
    return "rf_trees.npz" if meta.get("model_type") == "random_forest" else "knn_store.npz"


def payload_valid(meta: dict[str, Any]) -> dict[str, Any]:
    kategori = meta["valid_categories"]
    return {
        "event_date": "2024-01-01",
        "latitude": -6.2,
        "longitude": 106.8,
        "landslide_category": kategori["landslide_category"][0],
        "landslide_trigger": kategori["landslide_trigger"][0],
        "landslide_setting": kategori["landslide_setting"][0],
        "location_accuracy": kategori["location_accuracy"][0],
    }


@pytest.fixture()
def db_factory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[sessionmaker[Session]]:
    """SQLite lokal, dan `app.main.SessionLocal` diarahkan ke sini."""
    import app.db.models  # noqa: F401  pastikan metadata Base terisi

    engine = create_engine(
        f"sqlite:///{(tmp_path / 'audit.db').as_posix()}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr("app.main.SessionLocal", factory)
    yield factory
    engine.dispose()


def _settings(version_dir: Path, factory: sessionmaker[Session]) -> Settings:
    return Settings(
        ARTIFACT_DIR=version_dir.parent,
        MODEL_VERSION=version_dir.name,
        DATABASE_URL=str(factory.kw["bind"].url),
        ENV="test",
        SECRET_KEY="tes-secret-key-yang-cukup-panjang-untuk-lulus-validasi",
    )


# ---------------------------------------------------------------------------
# 1. Artefak asli
# ---------------------------------------------------------------------------
def test_real_artifacts_load(artifact_copy: Path, meta: dict[str, Any]) -> None:
    service = ModelService(artifact_copy)

    assert service.load() is True, service.error
    assert service.is_ready is True
    assert service.model_type == meta["model_type"]
    assert service.version == meta["version"]
    assert service.class_labels == CLASS_LABELS
    assert service.d_enc == meta["d_enc"]
    assert set(service.valid_categories) == set(meta["valid_categories"])


def test_predict_one_returns_normalized_probabilities(
    artifact_copy: Path, meta: dict[str, Any]
) -> None:
    service = ModelService(artifact_copy)
    assert service.load() is True, service.error

    hasil = service.predict_one(payload_valid(meta))

    assert hasil.predicted_class in CLASS_LABELS
    assert set(hasil.probabilities) == set(CLASS_LABELS)
    assert sum(hasil.probabilities.values()) == pytest.approx(1.0, abs=1e-6)
    assert hasil.confidence == pytest.approx(
        hasil.probabilities[hasil.predicted_class], abs=1e-9
    )
    assert hasil.confidence == pytest.approx(
        max(hasil.probabilities.values()), abs=1e-9
    )


# ---------------------------------------------------------------------------
# 2. Degradasi saat artefak rusak (regresi: dulu BadZipFile/EOFError lolos)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("kerusakan", ["terpotong", "kosong"])
def test_corrupt_model_binary_degrades_instead_of_raising(
    salinan: Path, meta: dict[str, Any], kerusakan: str
) -> None:
    berkas = salinan / active_model_file(meta)
    isi = berkas.read_bytes()
    berkas.write_bytes(isi[: len(isi) // 3] if kerusakan == "terpotong" else b"")

    service = ModelService(salinan)

    assert service.load() is False
    assert service.is_ready is False
    assert service.error, "error harus diisi supaya /health bisa didiagnosis"


def test_app_starts_when_model_binary_is_corrupt(
    salinan: Path, meta: dict[str, Any], db_factory: sessionmaker[Session]
) -> None:
    """Kontrak README: artefak rusak tidak boleh menjatuhkan API."""
    from app.main import create_app

    berkas = salinan / active_model_file(meta)
    berkas.write_bytes(berkas.read_bytes()[:512])

    app = create_app(_settings(salinan, db_factory))
    with TestClient(app) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["model_ready"] is False
    assert body["model_error"]


def test_health_hides_filesystem_details_in_production(salinan: Path) -> None:
    """`/health` publik: path absolut server tidak boleh ikut terkirim."""
    from app.main import create_app

    (salinan / "preprocessor.json").unlink()

    def _body(**overrides: Any) -> dict[str, Any]:
        settings = Settings(
            ARTIFACT_DIR=salinan.parent,
            MODEL_VERSION=salinan.name,
            DATABASE_URL="sqlite://",
            SECRET_KEY="kunci-produksi-palsu-yang-cukup-panjang-48byte-aman",
            **overrides,
        )
        app = create_app(settings)
        with TestClient(app) as client:
            return client.get("/api/v1/health").json()

    mode_tes = _body(ENV="test")
    assert mode_tes["model_ready"] is False
    assert str(salinan) in mode_tes["model_error"], "detail dibutuhkan saat debug"

    produksi = _body(ENV="production", COOKIE_SECURE=True)
    assert produksi["model_ready"] is False
    assert produksi["model_error"] == "Artefak model gagal dimuat; periksa log server"
    assert str(salinan) not in produksi["model_error"]


def test_app_syncs_model_registry_on_startup(
    salinan: Path, db_factory: sessionmaker[Session]
) -> None:
    from app.db.models import Model
    from app.main import create_app

    app = create_app(_settings(salinan, db_factory))
    with TestClient(app) as client:
        health = client.get("/api/v1/health")

    assert health.status_code == 200
    assert health.json()["model_ready"] is True

    with db_factory() as db:
        aktif = db.scalar(select(func.count()).select_from(Model).where(
            Model.model_status == "active"
        ))
    assert aktif == 1


# ---------------------------------------------------------------------------
# 3. Pagar terhadap metadata yang menyesatkan
# ---------------------------------------------------------------------------
def test_rejects_path_traversal_in_artifact_files(salinan: Path) -> None:
    path = salinan / "model_meta.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta["artifact_files"] = {"model": "../evil.npz"}
    path.write_text(json.dumps(meta), encoding="utf-8")

    service = ModelService(salinan)

    assert service.load() is False
    assert "keluar dari folder versi" in (service.error or "")


def test_rejects_class_labels_in_wrong_order(salinan: Path) -> None:
    path = salinan / "model_meta.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta["class_labels"] = list(reversed(CLASS_LABELS))
    path.write_text(json.dumps(meta), encoding="utf-8")

    service = ModelService(salinan)

    assert service.load() is False
    assert "class_labels" in (service.error or "")


def test_rejects_d_enc_mismatch(salinan: Path) -> None:
    path = salinan / "model_meta.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    meta["d_enc"] = int(meta["d_enc"]) + 1
    path.write_text(json.dumps(meta), encoding="utf-8")

    service = ModelService(salinan)

    assert service.load() is False
    assert "d_enc" in (service.error or "")


# ---------------------------------------------------------------------------
# 4. Estimator yang mengembalikan indeks kelas di luar rentang
# ---------------------------------------------------------------------------
class _EstimatorNakal:
    """Meniru artefak yang rusak: `predict()` mengembalikan indeks tak valid."""

    def __init__(self, index: int) -> None:
        self._index = index
        self.n_features_in_ = 0

    def predict_proba(self, vector):  # noqa: ANN001, ANN201 - tiruan
        import numpy as np

        return np.full((1, 3), 1.0 / 3.0)

    def predict(self, vector):  # noqa: ANN001, ANN201 - tiruan
        import numpy as np

        return np.array([self._index])


@pytest.mark.parametrize("index", [3, -1, 99])
def test_out_of_range_class_index_raises_model_error(
    artifact_copy: Path, meta: dict[str, Any], index: int
) -> None:
    """Indeks negatif berbahaya: `labels[-1]` diam-diam jadi kelas terakhir."""
    from app.utils.errors import ModelUnavailableError

    service = ModelService(artifact_copy)
    assert service.load() is True, service.error
    service._estimator = _EstimatorNakal(index)  # type: ignore[assignment]

    with pytest.raises(ModelUnavailableError, match="di luar rentang"):
        service.predict_one(payload_valid(meta))
