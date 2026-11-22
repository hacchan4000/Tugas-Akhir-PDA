# Frontend Web — Antarmuka Operator Posko BASARNAS

Aplikasi web berbasis **Next.js** untuk menginput laporan kejadian tanah longsor, menampilkan hasil prediksi skala bencana beserta rekomendasi prioritas pengerahan tim SAR, memantau riwayat laporan, dan melihat metrik evaluasi model.

## Prasyarat

* **Node.js** versi 18 atau lebih baru
* **npm** (terinstal otomatis bersama Node.js)
* Server **Backend FastAPI** sudah dalam keadaan berjalan di `http://127.0.0.1:8000`

## Cara Instalasi & Menjalankan Aplikasi

Pastikan terminal berada di dalam direktori `frontend/`:

### 1. Instal Dependensi
```powershell
npm install
```

### 2. Konfigurasi Environment Variable
Buat file bernama `.env.local` di dalam folder `frontend/` dan tambahkan baris berikut:
```env
NEXT_PUBLIC_API_URL=[http://127.0.0.1:8000/api/v1](http://127.0.0.1:8000/api/v1)
```

### 3. Jalankan Server Development
```powershell
npm run dev
```

Buka browser dan akses **`http://localhost:3000`**.

## Daftar Halaman Aplikasi

* **`/` (Halaman Utama):** Formulir input 7 parameter kejadian longsor dan kartu hasil prediksi (skala longsor, *confidence score*, distribusi probabilitas, alamat wilayah, prioritas SAR, serta perbandingan Model Aktif vs Pembanding).
* **`/riwayat` (Riwayat Posko):** Tabel daftar laporan kejadian yang telah diprediksi dan tersimpan di database backend.
* **`/evaluasi` (Evaluasi Model):** Ringkasan hasil pengujian *Macro-F1*, *Balanced Accuracy*, dan *Confusion Matrix* 3×3 antara Random Forest dan K-Nearest Neighbors.

## Script npm Tersedia

* `npm run dev` — Menjalankan aplikasi dalam mode *development*
* `npm run build` — Mem-build aplikasi untuk *production*
* `npm run start` — Menjalankan hasil *build production*
* `npm run lint` — Mengecek kualitas dan standar penulisan kode