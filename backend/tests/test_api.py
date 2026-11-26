"""Tes kontrak API v1 (auth, validasi 422, prediksi, isolasi riwayat, ekspor).

Model & geocoding di-stub lewat dependency override supaya tes tidak butuh
artefak hasil training maupun akses jaringan.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime, timedelta, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import Model, SarPriority, User
from app.dependencies.deps import get_db, get_geocoding_service, get_model_service
from app.main import create_app
from app.services.model_service import PredictionResult
from app.utils.security import hash_password

PASSWORD = "rahasia-operator-123"
EMAIL_SATU = "satu@example.com"
EMAIL_DUA = "dua@example.com"

VALID_CATEGORIES: dict[str, list[str]] = {
    "landslide_category": ["landslide", "mudflow"],
    "landslide_trigger": ["earthquake", "rain"],
    "landslide_setting": ["natural_slope", "road"],
    "location_accuracy": ["approximate", "exact"],
}


class FakeModelService:
    version = "v1"
    is_ready = True
    error = None
    model_type = "random_forest"

    @property
    def valid_categories(self) -> dict[str, list[str]]:
        return {key: list(values) for key, values in VALID_CATEGORIES.items()}

    def predict_one(self, payload: dict[str, Any]) -> PredictionResult:
        return PredictionResult(
            predicted_class="medium",
            confidence=0.8,
            probabilities={"small": 0.1, "medium": 0.8, "large": 0.1},
        )

    def options(self) -> dict[str, Any]:
        return {
            "valid_categories": self.valid_categories,
            "coordinate_bounds": {
                "latitude": [-90.0, 90.0],
                "longitude": [-180.0, 180.0],
            },
            "class_labels": ["small", "medium", "large"],
            "max_event_date": date.today(),
        }

    def info(self) -> dict[str, Any]:
        return {
            "model_name": "Random Forest",
            "model_version": "v1",
            "trained_date": None,
            "best_params": {"max_depth": 10},
            "d_enc": 9,
            "class_labels": ["small", "medium", "large"],
            "evaluation_metrics": {"macro_f1": 0.71},
            "comparator_info": {"model_name": "KNN"},
        }


class FakeGeocodingService:
    def reverse(self, latitude: float, longitude: float) -> tuple[str, str]:
        return "Jakarta, Indonesia", "success"


@pytest.fixture()
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False
    )

    def _override_db() -> Iterator[Session]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_model_service] = FakeModelService
    app.dependency_overrides[get_geocoding_service] = FakeGeocodingService

    with testing_session() as db:
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
                    name="Operator Satu",
                    email=EMAIL_SATU,
                    password_hash=hash_password(PASSWORD),
                ),
                User(
                    name="Operator Dua",
                    email=EMAIL_DUA,
                    password_hash=hash_password(PASSWORD),
                ),
                Model(
                    model_name="Random Forest",
                    model_version="v1",
                    best_params={"max_depth": 10},
                    model_status="active",
                    trained_date=datetime.now(timezone.utc),
                ),
            ]
        )
        db.commit()

    test_client = TestClient(app)
    yield test_client
    test_client.close()


def _login(client: TestClient, email: str = EMAIL_SATU) -> None:
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": PASSWORD}
    )
    assert response.status_code == 200, response.text


def _payload(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "event_date": date.today().isoformat(),
        "latitude": -6.2,
        "longitude": 106.8,
        "landslide_category": "landslide",
        "landslide_trigger": "rain",
        "landslide_setting": "natural_slope",
        "location_accuracy": "exact",
    }
    data.update(overrides)
    return data


def test_health_is_public(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["model_ready"] is True


def test_login_rejects_wrong_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login", json={"email": EMAIL_SATU, "password": "password-salah"}
    )
    assert response.status_code == 401


def test_me_requires_login(client: TestClient) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401


def test_login_sets_cookie_and_logout_clears_it(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login", json={"email": EMAIL_SATU, "password": PASSWORD}
    )
    assert response.status_code == 200
    assert "access_token" in response.cookies

    # Atribut cookie sesuai SPEC 4: httponly, samesite=lax, path="/".
    set_cookie = response.headers.get("set-cookie", "")
    lowered = set_cookie.lower()
    assert "httponly" in lowered
    assert "samesite=lax" in lowered
    assert "path=/" in lowered

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == EMAIL_SATU

    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401


def test_prediction_rejects_out_of_range_coordinate(client: TestClient) -> None:
    _login(client)
    response = client.post("/api/v1/predictions", json=_payload(latitude=200))
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail[0]["field"] == "latitude"
    assert "batas" in detail[0]["message"]


def test_prediction_rejects_unknown_category(client: TestClient) -> None:
    _login(client)
    response = client.post(
        "/api/v1/predictions", json=_payload(landslide_category="banjir")
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail[0]["field"] == "landslide_category"
    assert "tidak valid" in detail[0]["message"]


def test_prediction_rejects_far_future_date(client: TestClient) -> None:
    _login(client)
    future = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()
    response = client.post("/api/v1/predictions", json=_payload(event_date=future))
    assert response.status_code == 422
    assert response.json()["detail"][0]["field"] == "event_date"


def test_prediction_creates_history_and_isolates_users(client: TestClient) -> None:
    _login(client, EMAIL_SATU)
    created = client.post("/api/v1/predictions", json=_payload())
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["predicted_class"] == "medium"
    assert body["confidence_score"] == pytest.approx(0.8)
    assert body["sar_priority_level"] == "Sedang"
    assert body["nama_wilayah"] == "Jakarta, Indonesia"
    assert body["geocoding_status"] == "success"
    prediction_id = body["prediction_id"]

    history = client.get("/api/v1/predictions")
    assert history.status_code == 200
    assert history.json()["total"] == 1
    assert history.json()["items"][0]["prediction_id"] == prediction_id

    # Operator lain tidak boleh melihat riwayat di atas.
    _login(client, EMAIL_DUA)
    assert client.get("/api/v1/predictions").json()["total"] == 0
    assert client.get(f"/api/v1/predictions/{prediction_id}").status_code == 404


def test_history_filters_and_pagination(client: TestClient) -> None:
    _login(client)
    for _ in range(3):
        assert client.post("/api/v1/predictions", json=_payload()).status_code == 201

    page = client.get(
        "/api/v1/predictions",
        params={"page": 2, "page_size": 2, "region": "jakarta"},
    )
    assert page.status_code == 200
    payload = page.json()
    assert payload["total"] == 3
    assert payload["pages"] == 2
    assert len(payload["items"]) == 1

    empty = client.get(
        "/api/v1/predictions", params={"date_from": "2099-01-01"}
    ).json()
    assert empty["total"] == 0

    invalid_range = client.get(
        "/api/v1/predictions",
        params={"date_from": "2026-05-01", "date_to": "2026-04-01"},
    )
    assert invalid_range.status_code == 422


def test_export_csv_returns_attachment(client: TestClient) -> None:
    _login(client)
    assert client.post("/api/v1/predictions", json=_payload()).status_code == 201

    response = client.get("/api/v1/predictions/export")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/csv")
    assert 'filename="riwayat_prediksi.csv"' in response.headers["content-disposition"]
    text = response.text
    assert text.startswith("\ufeffprediction_id,")
    assert "medium" in text


def test_meta_options(client: TestClient) -> None:
    _login(client)
    response = client.get("/api/v1/meta/options")
    assert response.status_code == 200
    body = response.json()
    assert set(body["valid_categories"]) == set(VALID_CATEGORIES)
    assert body["coordinate_bounds"]["latitude"] == [-90.0, 90.0]


def test_model_info_combines_db_and_artifact(client: TestClient) -> None:
    _login(client)
    response = client.get("/api/v1/model/info")
    assert response.status_code == 200
    body = response.json()
    assert body["model_id"] is not None
    assert body["model_version"] == "v1"
    assert body["d_enc"] == 9
    assert body["evaluation_metrics"] == {"macro_f1": 0.71}


# ---------------------------------------------------------------------------
# Rate limit login
# ---------------------------------------------------------------------------
def test_login_is_rate_limited_after_repeated_failures(client: TestClient) -> None:
    salah = {"email": EMAIL_SATU, "password": "password-salah"}
    for _ in range(5):
        assert client.post("/api/v1/auth/login", json=salah).status_code == 401

    blocked = client.post("/api/v1/auth/login", json=salah)
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers
    assert int(blocked.headers["Retry-After"]) >= 1

    # Password benar pun tetap ditolak selama jendela waktu berjalan; kalau
    # tidak, penyerang tinggal menebak sampai benar.
    benar = client.post(
        "/api/v1/auth/login", json={"email": EMAIL_SATU, "password": PASSWORD}
    )
    assert benar.status_code == 429


def test_successful_login_resets_the_counter(client: TestClient) -> None:
    salah = {"email": EMAIL_SATU, "password": "password-salah"}
    for _ in range(4):
        assert client.post("/api/v1/auth/login", json=salah).status_code == 401

    _login(client)  # sukses -> hitungan dikosongkan

    for _ in range(5):
        assert client.post("/api/v1/auth/login", json=salah).status_code == 401


# ---------------------------------------------------------------------------
# CSRF: cookie + request lintas situs
# ---------------------------------------------------------------------------
def test_cookie_post_from_foreign_origin_is_rejected(client: TestClient) -> None:
    _login(client)

    response = client.post(
        "/api/v1/predictions",
        json=_payload(),
        headers={"Origin": "https://evil.example"},
    )

    assert response.status_code == 403
    assert "lintas situs" in response.json()["detail"]


def test_cookie_post_from_same_origin_is_allowed(client: TestClient) -> None:
    _login(client)

    response = client.post(
        "/api/v1/predictions",
        json=_payload(),
        headers={"Origin": "http://testserver"},
    )

    assert response.status_code == 201, response.text


def test_cookie_post_behind_tls_proxy_is_allowed(client: TestClient) -> None:
    """Proxy menghentikan TLS: skema di `request.url` bisa beda dari Origin."""
    _login(client)

    response = client.post(
        "/api/v1/predictions",
        json=_payload(),
        headers={"Origin": "https://testserver"},
    )

    assert response.status_code == 201, response.text


def test_cookie_post_from_configured_frontend_origin_is_allowed(
    client: TestClient,
) -> None:
    """Frontend Next.js di port berbeda tetap boleh (ada di CORS_ORIGINS)."""
    _login(client)

    response = client.post(
        "/api/v1/predictions",
        json=_payload(),
        headers={"Origin": "http://localhost:3000"},
    )

    assert response.status_code == 201, response.text


def test_cookie_post_with_cross_site_fetch_metadata_is_rejected(
    client: TestClient,
) -> None:
    _login(client)

    response = client.post(
        "/api/v1/predictions",
        json=_payload(),
        headers={"Sec-Fetch-Site": "cross-site"},
    )

    assert response.status_code == 403


def test_safe_method_from_foreign_origin_still_works(client: TestClient) -> None:
    """CSRF hanya relevan untuk metode yang mengubah state."""
    _login(client)

    response = client.get(
        "/api/v1/auth/me", headers={"Origin": "https://evil.example"}
    )

    assert response.status_code == 200


def test_bearer_token_is_not_subject_to_csrf_check(client: TestClient) -> None:
    """Klien non-browser mengirim token manual; tidak ada cookie yang dipakai."""
    login = client.post(
        "/api/v1/auth/login", json={"email": EMAIL_SATU, "password": PASSWORD}
    )
    token = login.cookies["access_token"]
    client.cookies.clear()

    response = client.post(
        "/api/v1/predictions",
        json=_payload(),
        headers={
            "Authorization": f"Bearer {token}",
            "Origin": "https://evil.example",
        },
    )

    assert response.status_code == 201, response.text
