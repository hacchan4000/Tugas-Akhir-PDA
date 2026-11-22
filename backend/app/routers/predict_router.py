from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.ml_service import predict_with_active_model, reverse_geocode
from app.models import (
    ClassificationHistory,
    InputData,
    Prediction,
    User,
)
from app.schemas import LandslideInputCreate, PredictionOutputResponse


router = APIRouter(prefix="/api/predict", tags=["Prediction"])


@router.post("", response_model=PredictionOutputResponse)
def predict_landslide(
    payload: LandslideInputCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PredictionOutputResponse:
    nama_wilayah = reverse_geocode(payload.latitude, payload.longitude)

    input_data = {
        "event_date": payload.event_date,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "landslide_category": payload.landslide_category,
        "landslide_trigger": payload.landslide_trigger,
        "landslide_setting": payload.landslide_setting,
        "location_accuracy": payload.location_accuracy,
        "nama_wilayah": nama_wilayah,
    }

    try:
        predicted_class, sar_priority, model_record = predict_with_active_model(
            db,
            input_data,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    try:
        input_record = InputData(
            user_id=current_user.user_id,
            event_date=payload.event_date,
            latitude=payload.latitude,
            longitude=payload.longitude,
            landslide_category=payload.landslide_category.value,
            landslide_trigger=payload.landslide_trigger.value,
            landslide_setting=payload.landslide_setting.value,
            location_accuracy=payload.location_accuracy.value,
            nama_wilayah=nama_wilayah,
        )
        db.add(input_record)
        db.flush()

        prediction_record = Prediction(
            input_id=input_record.input_id,
            model_id=model_record.model_id,
            predicted_class=predicted_class,
            sar_priority=sar_priority,
        )
        db.add(prediction_record)
        db.flush()

        history_record = ClassificationHistory(
            user_id=current_user.user_id,
            input_id=input_record.input_id,
            status="classified",
        )
        db.add(history_record)
        db.flush()

        db.commit()
        db.refresh(prediction_record)
        db.refresh(history_record)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gagal menyimpan hasil klasifikasi ke database",
        )

    return PredictionOutputResponse(
        predicted_class=predicted_class,
        sar_priority=sar_priority,
        nama_wilayah=nama_wilayah,
        model={
            "model_id": model_record.model_id,
            "model_name": model_record.model_name,
            "model_version": model_record.model_version,
            "model_status": model_record.model_status,
        },
        prediction_id=prediction_record.prediction_id,
        input_id=input_record.input_id,
        history_id=history_record.history_id,
    )
