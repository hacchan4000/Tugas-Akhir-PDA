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
│   └── utils/                  # security (bcrypt+PyJWT), sar, errors, rate_limit
├── migrations/                 # Alembic: 001_initial_schema, 002_seed_sar_priorities
├── scripts/                    # seed_operator.py, train_rf_max_features.py
├── notebooks/training.ipynb    # Eksperimen + ekspor artefak ke artifacts/v1/
├── artifacts/v1/               # preprocessor.json, model_meta.json, rf_trees.npz & knn_store.npz
├── tests/                      # core/, test_api, test_model_service, test_export_*, test_schema_migration, dll.
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
- `model_meta.json` (`model_type`, `model_name`, `version`, `trained_at`,
  `best_params`, `d_enc`, `class_labels`, `valid_categories`, `evaluation_metrics`,
  `comparator_info`, `artifact_files`)
- `knn_store.npz` **dan** `rf_trees.npz` (model pemenang + pembanding; file mana
  yang dipakai runtime ditunjuk `model_meta.json` → `artifact_files.model`)

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
- `tests/test_api.py` — kontrak API: cookie auth, 422, prediksi, isolasi riwayat,
  ekspor CSV, rate limit login, dan penolakan CSRF.
- `tests/test_model_service.py` — memuat artefak **asli** (bukan tiruan), termasuk
  degradasi ke `model_ready=false` saat berkas `.npz` terpotong/kosong.
- `tests/test_export_service.py` — bentuk CSV + netralisasi formula injection.
- `tests/test_export_streaming.py` — keyset pagination & ekspor 1.234 baris
  (tidak hilang, tidak duplikat, dibaca per batch).
- `tests/test_rate_limit.py` — `SlidingWindowLimiter` dengan waktu dimajukan.
- `tests/test_error_messages.py` — gagal kalau ada tipe error Pydantic baru yang
  belum diterjemahkan ke bahasa Indonesia.
- `tests/test_config_security.py` — `CORS_ORIGINS=*` ditolak, production wajib
  `COOKIE_SECURE=true` + `SECRET_KEY` kuat.
- `tests/test_schema_migration.py` — menjalankan `alembic upgrade head` sungguhan,
  lalu memeriksa 5 tabel, tipe kolom, index (termasuk `created_at DESC`), partial
  unique index `uq_models_single_active`, foreign key, dan isi seed `sar_priorities`.

Untuk meninjau SQL PostgreSQL tanpa menyentuh database (mis. sebelum deploy ke
Supabase):

```powershell
$env:DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/postgres"
alembic upgrade head --sql
```

## Keamanan & Ketahanan

- **Artefak rusak tidak menjatuhkan API.** `ModelService.load()` menangkap semua
  `Exception` (kecuali `KeyboardInterrupt`/`SystemExit`) karena `np.load` melempar
  `zipfile.BadZipFile`/`EOFError` untuk berkas terpotong. Hasilnya API tetap hidup,
  `/health` melaporkan `model_ready=false` beserta `model_error`.
- **Rate limit login.** `LOGIN_MAX_ATTEMPTS` (default 5) percobaan gagal per
  `LOGIN_WINDOW_SECONDS` (default 300) per alamat IP; percobaan berikutnya
  dijawab `429` + header `Retry-After`. Login sukses mengosongkan hitungan.
  Hitungan disimpan di memori proses: **tidak** dibagi antar worker, jadi kalau
  nanti dijalankan dengan banyak worker, ganti dengan penyimpanan bersama.
- **CSRF.** Cookie `access_token` + metode yang mengubah state diverifikasi lewat
  header `Origin`/`Sec-Fetch-Site`; origin yang tidak ada di `CORS_ORIGINS` dan
  bukan host yang sama akan ditolak `403`. Klien `Authorization: Bearer` tidak
  terpengaruh.
- **Formula injection di CSV.** `nama_wilayah` berasal dari Nominatim (OpenStreetMap
  yang bisa disunting publik). Sel yang diawali (termasuk setelah spasi) karakter
  `=`, `+`, `@`, `|`, tab, atau CR diberi prefiks `'` agar Excel/LibreOffice tidak
  mengeksekusinya; koordinat negatif tetap terbaca sebagai angka.
- **Ekspor tidak memuat seluruh riwayat.** `iter_for_user` memakai keyset
  pagination `(prediction_date, prediction_id)` per 500 baris dan mengalirkannya
  lewat `StreamingResponse`, jadi memori tetap datar walau riwayatnya besar.
  Catatan: satu sesi database ditahan selama unduhan berlangsung, jadi jumlah
  ekspor bersamaan dibatasi ukuran pool (default 5 + 10 overflow).
- **Wildcard pencarian di-escape.** `?q=%` dan `?q=_` diperlakukan sebagai
  karakter literal (`ESCAPE '\'`), bukan wildcard SQL `LIKE`.
- **Konfigurasi berbahaya ditolak saat start.** `CORS_ORIGINS=*` ditolak
  (karena cookie dikirim), dan `ENV=production` mewajibkan `COOKIE_SECURE=true`
  serta `SECRET_KEY` yang bukan placeholder.
- **`/health` tidak membocorkan isi server.** Endpoint ini publik; di
  `ENV=production` `model_error` diganti pesan generik supaya path absolut
  artefak tidak terkirim ke luar. Detail asli tetap ada di log.

## Catatan Skema (sesuai SPEC §3.1)

- 5 tabel: `users`, `models`, `sar_priorities`, `input_data`, `predictions`.
- `users` memakai `name` + `email` (login via email), bukan `username`.
- `classification_history` **dihapus**: riwayat = `predictions` ⨝ `input_data`
  (satu prediksi = satu baris riwayat, tanpa duplikasi data).
- `sar_priorities` adalah master data; `predictions.predicted_class` FK ke sana.
- Hanya boleh ada satu baris `models` dengan status `active`
  (partial unique index `uq_models_single_active`).
- `input_data` punya index `(user_id, created_at DESC)` dan `(user_id, nama_wilayah)`,
  sedangkan `predictions` punya index `(prediction_date, prediction_id)` untuk
  menopang pagination dan ekspor CSV berbasis keyset.  Catatan: `alembic check` pada SQLite akan melaporkan index pertama sebagai
  perbedaan palsu karena Alembic belum bisa membandingkan *expression index*
  (DESC) di SQLite. Acuan kebenarannya `tests/test_schema_migration.py`; pada
  PostgreSQL perbandingan ini bekerja normal.
