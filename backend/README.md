# Backend API — Klasifikasi Ukuran Tanah Longsor & Prioritas SAR

FastAPI + SQLAlchemy 2.0 + Alembic. Seluruh algoritma ML (preprocessing, KNN,
Random Forest, model selection, metrik) diimplementasikan manual di
`app/core/` (NumPy/pandas murni, tanpa scikit-learn saat runtime).

## Struktur Folder

```text
backend/
├── app/
│   ├── main.py                 # FastAPI app: lifespan, CORS, error handler, router v1
│   ├── config.py               # Settings (.env) via pydantic-settings
│   ├── api/
│   │   ├── router.py           # Agregator prefix /api/v1
│   │   └── v1/
│   │       ├── auth.py         # POST /login, POST /logout, GET /me
│   │       ├── meta.py         # GET /meta/options
│   │       ├── predictions.py  # POST /, GET /export, GET /, GET /{id}
│   │       ├── model_info.py   # GET /model/info
│   │       └── health.py       # GET /health
│   ├── core/                   # ML manual (tidak diubah oleh lapisan API)
│   ├── db/
│   │   ├── base.py             # DeclarativeBase + naming convention
│   │   ├── session.py          # Engine & SessionLocal (SQLAlchemy 2.0 sinkron)
│   │   ├── models/             # user, model, sar_priority, input_data, prediction
│   │   └── repositories/       # user_repo, model_repo, prediction_repo
│   ├── dependencies/deps.py    # get_db, get_current_user, get_model_service
│   ├── schemas/                # auth, prediction, history, model_info
│   ├── services/               # auth, model, prediction, geocoding, history, export
│   └── utils/                  # security (bcrypt+PyJWT), sar, errors
├── migrations/                 # Alembic: 001_initial_schema, 002_seed_sar_priorities
├── scripts/seed_operator.py    # CLI akun operator pertama
├── notebooks/training.ipynb    # Eksperimen + ekspor artefak ke artifacts/v1/
├── artifacts/v1/               # preprocessor.json, model_meta.json, rf_trees.npz / knn_store.npz
├── tests/                      # test_core (tests/core/) + test_api.py
├── alembic.ini
├── requirements.txt
└── .env.example
```

## Prasyarat

- Python 3.11+
- PostgreSQL (Supabase Session Pooler) **atau** SQLite untuk pengembangan lokal

## Setup

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # lalu isi DATABASE_URL & SECRET_KEY
```

> Jika aktivasi venv diblokir ExecutionPolicy:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

## Migrasi Database

Skema **tidak** dibuat lewat `create_all()`; semuanya lewat Alembic.

```powershell
alembic upgrade head      # 001 buat 5 tabel + index + RLS, 002 seed sar_priorities
alembic current
```

Untuk SQLite lokal: set `DATABASE_URL=sqlite:///./basarnas.db` di `.env`.
RLS hanya dijalankan pada PostgreSQL (dilewati otomatis di SQLite).

## Akun Operator Pertama

```powershell
python -m scripts.seed_operator --name "Operator BASARNAS" --email ops@basarnas.go.id
# ganti password akun yang sudah ada:
python -m scripts.seed_operator --email ops@basarnas.go.id --update-password
```

## Artefak Model

Jalankan `notebooks/training.ipynb` (kernel = venv backend). Notebook menulis ke
`artifacts/v1/`:

- `preprocessor.json`
- `model_meta.json`
- `rf_trees.npz` **atau** `knn_store.npz` (sesuai model pemenang)

Saat startup, `app/main.py` memuat artefak lalu menyinkronkan tabel `models`
(model aktif lama diarsipkan, versi baru menjadi `active`). Jika artefak belum
ada, API tetap hidup dan `GET /api/v1/health` melaporkan `model_ready=false`.

## Menjalankan Server

```powershell
uvicorn app.main:app --reload
```

- Docs: <http://127.0.0.1:8000/docs>
- Health: <http://127.0.0.1:8000/api/v1/health>

## Endpoint (prefix `/api/v1`)

| Method | Path | Auth | Keterangan |
| --- | --- | --- | --- |
| GET | `/health` | publik | status API + kesiapan artefak |
| POST | `/auth/login` | publik | set cookie `access_token` (httponly) |
| POST | `/auth/logout` | ya | hapus cookie |
| GET | `/auth/me` | ya | profil operator |
| GET | `/meta/options` | ya | opsi dropdown + batas koordinat dari `model_meta.json` |
| POST | `/predictions` | ya | prediksi + simpan `input_data` & `predictions` |
| GET | `/predictions` | ya | riwayat terpaginasi (`page`, `page_size`, filter tanggal/wilayah/`q`) |
| GET | `/predictions/export` | ya | CSV seluruh hasil filter (`riwayat_prediksi.csv`) |
| GET | `/predictions/{id}` | ya | detail 1 prediksi milik operator |
| GET | `/model/info` | ya | metadata model aktif (`best_params`, `d_enc`, dll.) |

Error validasi selalu `422` dengan bentuk:

```json
{"detail": [{"field": "latitude", "message": "nilai di atas batas maksimum"}]}
```

## Tes

```powershell
pytest -q
```

- `tests/core/` — verifikasi matematis modul manual vs scikit-learn (hanya di tes).
- `tests/test_api.py` — kontrak API: cookie auth, 422, prediksi, isolasi riwayat, ekspor CSV.

## Catatan Skema (sesuai SPEC §3.1)

- 5 tabel: `users`, `models`, `sar_priorities`, `input_data`, `predictions`.
- `users` memakai `name` + `email` (login via email), bukan `username`.
- `classification_history` **dihapus**: riwayat = `predictions` ⨝ `input_data`
  (satu prediksi = satu baris riwayat, tanpa duplikasi data).
- `sar_priorities` adalah master data; `predictions.predicted_class` FK ke sana.
- Hanya boleh ada satu baris `models` dengan status `active`
  (partial unique index `uq_models_single_active`).
