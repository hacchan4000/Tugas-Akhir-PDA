"""Ekspor riwayat dalam skala nyata: keyset pagination + streaming HTTP.

Keluarga tes ini menjawab satu pertanyaan: apakah "Ekspor CSV" masih benar
ketika riwayat operator berisi ribuan baris, bukan tiga baris seperti di
`test_api.py`. Dua bug yang dijaga di sini:

1. Dulu seluruh riwayat dimuat jadi `list` sebelum dikirim (OOM).
2. Setelah diubah menjadi iterator, salah urut/keyset bisa membuat baris
   hilang atau terduplikasi di batas batch.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterator
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import InputData, Model, Prediction, SarPriority, User
from app.db.repositories import prediction_repo
from app.db.repositories.prediction_repo import HistoryFilters
from app.dependencies.deps import get_db, get_geocoding_service, get_model_service
from app.main import create_app
from app.utils.security import hash_password

PASSWORD = "rahasia-operator-123"
EMAIL = "operator@example.com"
EMAIL_LAIN = "operator-lain@example.com"
JUMLAH_BARIS = 1234
BATCH = 100


@pytest.fixture()
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with factory() as db:
        db.add_all(
            [
                SarPriority(
                    predicted_class="small",
                    sar_priority_level="Rendah",
                    sar_recommendation="Perkiraan skala kecil",
                ),
                SarPriority(
                    predicted_class="medium",
                    sar_priority_level="Sedang",
                    sar_recommendation="Perkiraan skala menengah",
                ),
                SarPriority(
                    predicted_class="large",
                    sar_priority_level="Tinggi",
                    sar_recommendation="Perkiraan skala besar",
                ),
                User(
                    name="Operator",
                    email=EMAIL,
                    password_hash=hash_password(PASSWORD),
                ),
                User(
                    name="Operator Lain",
                    email=EMAIL_LAIN,
                    password_hash=hash_password(PASSWORD),
                ),
                Model(
                    model_name="Random Forest",
                    model_version="v1",
                    best_params={},
                    model_status="active",
                ),
            ]
        )
        db.flush()

        user_id = db.scalar(select(User.user_id).where(User.email == EMAIL))
        user_lain = db.scalar(select(User.user_id).where(User.email == EMAIL_LAIN))
        model_id = db.scalar(select(Model.model_id))
        assert user_id is not None and user_lain is not None and model_id is not None

        # Tiga baris sengaja berbagi `prediction_date` yang sama: inilah yang
        # membuat cursor (tanggal, id) wajib, bukan tanggal saja.
        waktu = datetime(2024, 1, 1, tzinfo=timezone.utc)
        inputs = [
            InputData(
                user_id=user_id,
                event_date=date(2024, 1, 1) + timedelta(days=i % 28),
                latitude=-6.2 + (i % 10) * 0.01,
                longitude=106.8 + (i % 10) * 0.01,
                landslide_category="landslide",
                landslide_trigger="rain",
                landslide_setting="natural_slope",
                location_accuracy="exact",
                nama_wilayah=f"Kecamatan {i % 7}",
                geocoding_status="success",
            )
            for i in range(JUMLAH_BARIS)
        ]
        db.add_all(inputs)
        db.flush()  # satu flush: input_id terisi untuk semua baris sekaligus

        db.add_all(
            [
                Prediction(
                    input_id=row.input_id,
                    model_id=model_id,
                    predicted_class=("small", "medium", "large")[i % 3],
                    confidence_score=0.5 + (i % 50) / 100,
                    probabilities={"small": 0.3, "medium": 0.4, "large": 0.3},
                    status="success",
                    prediction_date=waktu if i < 3 else waktu + timedelta(minutes=i),
                )
                for i, row in enumerate(inputs)
            ]
        )

        # Riwayat milik operator lain; tidak boleh ikut terekspor.
        input_lain = InputData(
            user_id=user_lain,
            event_date=date(2024, 2, 1),
            latitude=-7.0,
            longitude=107.0,
            landslide_category="mudflow",
            landslide_trigger="earthquake",
            landslide_setting="road",
            location_accuracy="approximate",
            nama_wilayah="Milik Orang Lain",
            geocoding_status="success",
        )
        db.add(input_lain)
        db.flush()
        db.add(
            Prediction(
                input_id=input_lain.input_id,
                model_id=model_id,
                predicted_class="large",
                confidence_score=0.9,
                probabilities={"small": 0.05, "medium": 0.05, "large": 0.9},
                status="success",
                prediction_date=waktu,
            )
        )
        db.commit()

    yield factory
    engine.dispose()


@pytest.fixture()
def client(session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    from app.services.model_service import PredictionResult

    class _Model:
        version = "v1"
        is_ready = True
        error = None
        model_type = "random_forest"

        def predict_one(self, payload: dict) -> PredictionResult:  # pragma: no cover
            raise AssertionError("ekspor tidak boleh memanggil model")

    def _override_db() -> Iterator[Session]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_model_service] = _Model
    app.dependency_overrides[get_geocoding_service] = object()

    test_client = TestClient(app)
    login = test_client.post(
        "/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD}
    )
    assert login.status_code == 200, login.text
    yield test_client
    test_client.close()


# ---------------------------------------------------------------------------
# 1. Repositori: keyset pagination
# ---------------------------------------------------------------------------
def test_keyset_pagination_visits_every_row_exactly_once(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as db:
        user_id = db.scalar(select(User.user_id).where(User.email == EMAIL))
        assert user_id is not None

        ids = [
            row[0].prediction_id
            for row in prediction_repo.iter_for_user(
                db, user_id, HistoryFilters(), batch_size=BATCH
            )
        ]

    assert len(ids) == JUMLAH_BARIS
    assert len(set(ids)) == JUMLAH_BARIS, "keyset tidak boleh menduplikasi baris"
    assert ids == sorted(ids), "urutan harus naik agar cursor tidak melewati baris"


def test_keyset_handles_duplicate_timestamps(
    session_factory: sessionmaker[Session],
) -> None:
    """Tiga baris dengan `prediction_date` identik harus tetap terkirim semua."""
    with session_factory() as db:
        user_id = db.scalar(select(User.user_id).where(User.email == EMAIL))
        assert user_id is not None
        ids = [
            row[0].prediction_id
            for row in prediction_repo.iter_for_user(
                db, user_id, HistoryFilters(), batch_size=1
            )
        ]

    assert len(ids) == JUMLAH_BARIS
    assert len(set(ids)) == JUMLAH_BARIS


def test_wildcard_in_query_is_escaped(
    session_factory: sessionmaker[Session],
) -> None:
    """`?q=%` dulu mengembalikan SELURUH riwayat karena `%` jadi wildcard."""
    with session_factory() as db:
        user_id = db.scalar(select(User.user_id).where(User.email == EMAIL))
        assert user_id is not None

        semua = prediction_repo.count_for_user(db, user_id, HistoryFilters())
        liar = prediction_repo.count_for_user(db, user_id, HistoryFilters(q="%"))
        garis_bawah_salah = prediction_repo.count_for_user(
            db, user_id, HistoryFilters(q="Kecamatan_3")
        )
        garis_bawah_benar = prediction_repo.count_for_user(
            db, user_id, HistoryFilters(q="natural_slope")
        )
        nyata = prediction_repo.count_for_user(
            db, user_id, HistoryFilters(q="Kecamatan 3")
        )

    assert semua == JUMLAH_BARIS
    assert liar == 0, "wildcard % harus diperlakukan sebagai karakter literal"
    # Tanpa escape, `_` cocok dengan spasi sehingga "Kecamatan_3" ikut menemukan
    # "Kecamatan 3". Dengan escape, hanya garis bawah sungguhan yang cocok.
    assert garis_bawah_salah == 0
    assert garis_bawah_benar == JUMLAH_BARIS
    assert nyata == JUMLAH_BARIS // 7


# ---------------------------------------------------------------------------
# 2. HTTP: streaming ekspor
# ---------------------------------------------------------------------------
def _rows(text: str) -> list[dict[str, str]]:
    parsed = list(csv.reader(io.StringIO(text)))
    header = parsed[0]
    header[0] = header[0].lstrip("\ufeff")
    return [dict(zip(header, row, strict=True)) for row in parsed[1:]]


def test_export_streams_every_row_of_the_operator(client: TestClient) -> None:
    response = client.get("/api/v1/predictions/export")

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/csv")
    rows = _rows(response.text)

    assert len(rows) == JUMLAH_BARIS
    assert all(row["nama_wilayah"] != "Milik Orang Lain" for row in rows)
    ids = [int(row["prediction_id"]) for row in rows]
    assert ids == sorted(ids)
    assert len(set(ids)) == JUMLAH_BARIS


def test_export_respects_filters(client: TestClient) -> None:
    response = client.get("/api/v1/predictions/export", params={"region": "Kecamatan 3"})

    assert response.status_code == 200, response.text
    rows = _rows(response.text)

    assert rows
    assert all(row["nama_wilayah"] == "Kecamatan 3" for row in rows)
    assert len(rows) == JUMLAH_BARIS // 7


def test_export_reads_in_batches_not_one_giant_query(
    session_factory: sessionmaker[Session],
) -> None:
    """Bukti kuantitatif: 1.234 baris dibaca dalam banyak query, bukan satu."""
    from sqlalchemy import event

    engine = session_factory.kw["bind"]
    jumlah = {"n": 0}

    def _hitung(*_args: object, **_kwargs: object) -> None:
        jumlah["n"] += 1

    event.listen(engine, "before_cursor_execute", _hitung)
    try:
        with session_factory() as db:
            user_id = db.scalar(select(User.user_id).where(User.email == EMAIL))
            assert user_id is not None
            rows = list(
                prediction_repo.iter_for_user(
                    db, user_id, HistoryFilters(), batch_size=BATCH
                )
            )
    finally:
        event.remove(engine, "before_cursor_execute", _hitung)

    assert len(rows) == JUMLAH_BARIS
    # 1.234 baris / 100 per batch = 13 batch. Satu query besar akan menghasilkan
    # 1-2 query saja, jadi ambang ini membedakan keduanya dengan jelas.
    assert jumlah["n"] >= JUMLAH_BARIS // BATCH


def test_export_wildcard_query_is_literal(client: TestClient) -> None:
    response = client.get("/api/v1/predictions/export", params={"q": "%"})

    assert response.status_code == 200, response.text
    assert _rows(response.text) == []
