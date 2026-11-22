import csv
import io
import unicodedata
from datetime import date, datetime, time, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fpdf import FPDF
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import ClassificationHistory, InputData, Prediction, User
from app.schemas import HistoryItemResponse


router = APIRouter(prefix="/api/history", tags=["Classification History"])

EXPORT_COLUMNS = (
    "history_id",
    "user_id",
    "input_id",
    "classification_date",
    "status",
    "nama_wilayah",
    "predicted_class",
)


def _filtered_history_query(
    user_id: int,
    start_date: date | None,
    end_date: date | None,
    search: str | None,
):
    statement = (
        select(ClassificationHistory, InputData, Prediction)
        .join(InputData, ClassificationHistory.input_id == InputData.input_id)
        .outerjoin(Prediction, Prediction.input_id == InputData.input_id)
        .where(ClassificationHistory.user_id == user_id)
    )
    if start_date is not None:
        statement = statement.where(
            ClassificationHistory.classification_date
            >= datetime.combine(start_date, time.min)
        )
    if end_date is not None:
        statement = statement.where(
            ClassificationHistory.classification_date
            < datetime.combine(end_date + timedelta(days=1), time.min)
        )
    if search:
        escaped_search = (
            search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        search_pattern = f"%{escaped_search}%"
        statement = statement.where(
            or_(
                InputData.nama_wilayah.ilike(search_pattern, escape="\\"),
                Prediction.predicted_class.ilike(search_pattern, escape="\\"),
            )
        )
    return statement.order_by(
        ClassificationHistory.classification_date.desc(),
        ClassificationHistory.history_id.desc(),
    )


def _get_history_rows(
    db: Session,
    user_id: int,
    start_date: date | None,
    end_date: date | None,
    search: str | None,
) -> list[HistoryItemResponse]:
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date tidak boleh setelah end_date",
        )

    records = db.execute(
        _filtered_history_query(user_id, start_date, end_date, search)
    ).all()
    return [
        HistoryItemResponse(
            history_id=history.history_id,
            user_id=history.user_id,
            input_id=history.input_id,
            classification_date=history.classification_date,
            status=history.status,
            nama_wilayah=input_record.nama_wilayah,
            predicted_class=prediction.predicted_class if prediction else None,
        )
        for history, input_record, prediction in records
    ]


def _pdf_unicode_font_path() -> Path | None:
    candidates = (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    )
    return next((path for path in candidates if path.is_file()), None)


def _pdf_safe_text(value: object, supports_unicode: bool) -> str:
    text = str(value)
    if supports_unicode:
        return text
    return unicodedata.normalize("NFKD", text).encode("latin-1", "replace").decode(
        "latin-1"
    )


def _history_csv(rows: list[HistoryItemResponse]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(EXPORT_COLUMNS)
    for row in rows:
        writer.writerow([getattr(row, column) for column in EXPORT_COLUMNS])
    return output.getvalue().encode("utf-8-sig")


def _history_pdf(rows: list[HistoryItemResponse]) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    font_path = _pdf_unicode_font_path()
    supports_unicode = font_path is not None
    if font_path is not None:
        pdf.add_font("HistoryUnicode", fname=str(font_path))
        font_family = "HistoryUnicode"
    else:
        font_family = "Helvetica"

    pdf.add_page()
    pdf.set_font(font_family, size=14)
    pdf.cell(0, 10, _pdf_safe_text("Riwayat Klasifikasi Longsor", supports_unicode))
    pdf.ln(12)
    pdf.set_font(font_family, size=9)

    for row_number, row in enumerate(rows, start=1):
        if pdf.get_y() > 255:
            pdf.add_page()
            pdf.set_font(font_family, size=9)
        details = (
            f"{row_number}. ID Riwayat: {row.history_id} | Pengguna: {row.user_id} "
            f"| Input: {row.input_id}",
            f"Tanggal klasifikasi: {row.classification_date.isoformat(sep=' ')}",
            f"Wilayah: {row.nama_wilayah}",
            f"Kelas prediksi: {row.predicted_class or '-'} | Status: {row.status}",
        )
        for line in details:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5, _pdf_safe_text(line, supports_unicode))
        pdf.ln(2)

    rendered = pdf.output()
    if isinstance(rendered, (bytes, bytearray)):
        return bytes(rendered)
    return rendered.encode("latin-1")


@router.get("", response_model=list[HistoryItemResponse])
def get_user_history(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=255),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[HistoryItemResponse]:
    return _get_history_rows(
        db,
        current_user.user_id,
        start_date,
        end_date,
        search.strip() if search else None,
    )


@router.get("/export")
def export_user_history(
    format: str = Query(default="csv", pattern="^(csv|pdf)$"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=255),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    rows = _get_history_rows(
        db,
        current_user.user_id,
        start_date,
        end_date,
        search.strip() if search else None,
    )

    if format == "csv":
        content = _history_csv(rows)
        media_type = "text/csv; charset=utf-8"
        filename = "riwayat-klasifikasi.csv"
    else:
        content = _history_pdf(rows)
        media_type = "application/pdf"
        filename = "riwayat-klasifikasi.pdf"

    return StreamingResponse(
        io.BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
