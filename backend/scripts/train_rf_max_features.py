"""Latih Random Forest dengan ``max_features=None`` sebagai eksperimen terpisah.

Kenapa skrip ini ada
--------------------
Grid RF di notebook (SPEC §2.3) menyapu ``n_estimators`` x ``max_depth`` x
``max_features``. Skrip ini mengulang eksperimen itu untuk **hanya**
``max_features=None``, supaya dampaknya terhadap baseline ``"sqrt"`` bisa diukur
tanpa harus menjalankan seluruh grid 24 kombinasi.

Skrip ini **tidak** menulis ke ``artifacts/``. Artefak produksi hanya dihasilkan
oleh ``notebooks/training.ipynb`` (SPEC §2.4); kalau skrip ini ikut menulis
artefak, backend bisa memuat model yang tidak pernah lolos verifikasi notebook.
Hasil di sini murni diagnostik dan disimpan ke ``experiments/``.

Contoh (dari folder ``backend/``)::

    python -m scripts.train_rf_max_features
    python -m scripts.train_rf_max_features --ratios 0.20 --n-jobs 4
    python -m scripts.train_rf_max_features --mode grid --n-jobs 4
    python -m scripts.train_rf_max_features --smoke

Mode ``tunggal`` (default) memakai konfigurasi yang dipilih grid pada rasio 0,20
(``n_estimators=100``, ``max_depth=None``) dan hanya mengubah ``max_features``.
Mode ``grid`` menyapu 12 kombinasi ``n_estimators`` x ``max_depth`` dengan
``max_features=None`` — biayanya berjam-jam, jangan dijalankan tanpa alasan.

Hasil per rasio disimpan ke ``experiments/rf_none_<pct>.pkl``, **bukan**
``random_forest_<pct>.pkl``, supaya cache notebook tidak tertimpa.
"""

from __future__ import annotations

import argparse
import math
import multiprocessing
import pickle
import sys
import time
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pandas as pd  # noqa: E402

from app.core import (  # noqa: E402
    TARGET,
    RandomForest,
    clean_raw,
    engineer_features,
    holdout_grid_search,
)

SEED = 42
N_SPLITS = 5
EXPERIMENTS_DIR = BACKEND_ROOT / "experiments"

# Satu konfigurasi: yang dipilih grid pada rasio 0,20, hanya max_features diubah.
GRID_TUNGGAL: dict[str, list[Any]] = {
    "n_estimators": [100],
    "max_depth": [None],
    "max_features": [None],
}

# 12 kombinasi SPEC §2.3 dengan max_features dikunci ke None.
GRID_PENUH: dict[str, list[Any]] = {
    "n_estimators": [100, 200, 300],
    "max_depth": [None, 10, 20, 30],
    "max_features": [None],
}

# Uji cepat: memastikan pipa (spawn, prefix cache, penyimpanan) hidup.
GRID_SMOKE: dict[str, list[Any]] = {
    "n_estimators": [5, 10],
    "max_depth": [3],
    "max_features": [None],
}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Latih RF dengan max_features=None (diagnostik, tanpa menulis artefak)"
    )
    parser.add_argument(
        "--ratios",
        default="0.10,0.15,0.20",
        help="rasio holdout dipisah koma (default: 0.10,0.15,0.20)",
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=4,
        help="jumlah proses per pohon (default: 4; hasil tidak berubah karena "
        "setiap pohon punya seed sendiri)",
    )
    parser.add_argument(
        "--mode",
        choices=("tunggal", "grid"),
        default="tunggal",
        help="tunggal = 1 konfigurasi; grid = 12 kombinasi n_estimators x max_depth",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="jangan simpan report ke experiments/",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="uji cepat pada 600 baris dengan grid mini; tidak menyimpan apa pun",
    )
    return parser.parse_args(argv)


def _parse_ratios(raw: str) -> tuple[float, ...]:
    hasil: list[float] = []
    for bagian in raw.split(","):
        bagian = bagian.strip()
        if not bagian:
            continue
        try:
            nilai = float(bagian)
        except ValueError:
            raise SystemExit(f"--ratios: {bagian!r} bukan angka") from None
        if not 0.05 <= nilai <= 0.50:
            raise SystemExit(f"--ratios: {nilai} di luar rentang wajar 0,05-0,50")
        hasil.append(round(nilai, 2))
    if not hasil:
        raise SystemExit("--ratios kosong")
    # Buang duplikat sambil mempertahankan urutan.
    return tuple(dict.fromkeys(hasil))


def _load_frame(smoke: bool) -> pd.DataFrame:
    files = sorted((BACKEND_ROOT / "data").glob("*.csv"))
    if len(files) != 1:
        raise SystemExit(
            f"harus ada tepat 1 berkas CSV di {BACKEND_ROOT / 'data'}, "
            f"ditemukan {len(files)}"
        )
    df = engineer_features(clean_raw(pd.read_csv(files[0])))
    if smoke:
        df = df.sample(n=min(600, len(df)), random_state=0).reset_index(drop=True)
    return df


def _baseline(ratio: float) -> dict[str, Any] | None:
    """Report baseline ``max_features="sqrt"`` dari cache notebook, bila ada."""
    path = EXPERIMENTS_DIR / f"random_forest_{int(round(ratio * 100)):02d}.pkl"
    if not path.exists():
        return None
    try:
        with open(path, "rb") as handle:
            saved = pickle.load(handle)
    except (OSError, pickle.UnpicklingError, EOFError):
        return None
    report = saved.get("report") if isinstance(saved, dict) else None
    return report if isinstance(report, dict) else None


def _print_report(
    judul: str,
    report: dict[str, Any],
    durasi_detik: float,
    baseline: dict[str, Any] | None,
) -> None:
    metrik = report["test_metrics"]
    print(f"\n[{judul}] selesai dalam {durasi_detik / 60:.1f} menit")
    print("  best_params  :", report["best_params"])
    print(
        f"  CV macro-F1  : {report['cv_mean_macro_f1']:.4f} "
        f"+- {report['cv_std_macro_f1']:.4f}"
    )
    print(f"  test macro-F1: {metrik['macro_f1']:.4f}")
    print(f"  balanced acc : {metrik['balanced_accuracy']:.4f}")
    print(f"  accuracy     : {metrik['accuracy']:.4f}")
    for label, per_kelas in metrik["per_class"].items():
        print(
            f"    {label:7s} P={per_kelas['precision']:.4f} "
            f"R={per_kelas['recall']:.4f} F1={per_kelas['f1']:.4f}"
        )
    if baseline is None:
        return
    base = baseline["test_metrics"]
    print(
        "  pembanding sqrt (cache): "
        f"CV {baseline['cv_mean_macro_f1']:.4f} | test {base['macro_f1']:.4f} | "
        f"recall_large {base['per_class']['large']['recall']:.3f}"
    )
    print(f"  selisih test macro-F1 : {metrik['macro_f1'] - base['macro_f1']:+.4f}")


def _save(ratio: float, grid: dict[str, list[Any]], report: dict[str, Any]) -> Path:
    EXPERIMENTS_DIR.mkdir(exist_ok=True)
    path = EXPERIMENTS_DIR / f"rf_none_{int(round(ratio * 100)):02d}.pkl"
    payload = {
        "signature": {
            "grid": {k: [str(v) for v in vals] for k, vals in grid.items()},
            "seed": SEED,
            "n_splits": N_SPLITS,
            "ratio": ratio,
            "script": "train_rf_max_features",
        },
        "grid": grid,
        "report": report,
    }
    tmp = path.with_suffix(".tmp")
    with open(tmp, "wb") as handle:
        pickle.dump(payload, handle)
    tmp.replace(path)  # tulis atomik: jangan tinggalkan berkas setengah jadi
    return path


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    ratios = (0.20,) if args.smoke else _parse_ratios(args.ratios)

    if args.smoke:
        grid = GRID_SMOKE
    elif args.mode == "grid":
        grid = GRID_PENUH
    else:
        grid = GRID_TUNGGAL

    # Pagar: skrip ini hanya boleh menguji max_features=None.
    if grid["max_features"] != [None]:
        raise SystemExit("grid harus memakai max_features=[None]")

    n_combo = math.prod(len(v) for v in grid.values())
    df = _load_frame(args.smoke)
    print(f"data       : {df.shape[0]} baris, {df.shape[1]} kolom")
    print(f"grid       : {grid}")
    print(
        f"kombinasi  : {n_combo} x {N_SPLITS} fold x {len(ratios)} rasio = "
        f"{n_combo * N_SPLITS * len(ratios)} evaluasi CV"
    )
    print(f"n_jobs     : {args.n_jobs}")
    if args.mode == "grid" and not args.smoke:
        print("peringatan  : mode grid berjalan berjam-jam; pertimbangkan --ratios 0.20")

    for ratio in ratios:
        mulai = time.time()
        report = holdout_grid_search(
            lambda **p: RandomForest(random_state=SEED, n_jobs=args.n_jobs, **p),
            grid,
            df,
            test_sizes=(ratio,),
            n_splits=N_SPLITS,
            seed=SEED,
        )[0]
        durasi = time.time() - mulai
        _print_report(
            f"rasio {ratio:.0%}",
            report,
            durasi,
            None if args.smoke else _baseline(ratio),
        )
        if args.smoke or args.no_save:
            print("  (tidak disimpan)")
        else:
            print("  disimpan ke:", _save(ratio, grid, report).relative_to(BACKEND_ROOT))
    return 0


if __name__ == "__main__":
    # Wajib di Windows: n_jobs > 1 memakai ProcessPoolExecutor dengan start
    # method "spawn", dan tanpa guard ini proses anak akan mengimpor ulang
    # modul ini lalu menjalankan grid search lagi dari nol.
    multiprocessing.freeze_support()
    raise SystemExit(main())
