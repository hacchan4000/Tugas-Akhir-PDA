import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Model as ModelRecord
from app.routers.auth_router import router as auth_router
from app.routers.history_router import router as history_router
from app.routers.model_router import router as model_router
from app.routers.predict_router import router as predict_router


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(ModelRecord.model_id).limit(1)) is None:
            db.add(
                ModelRecord(
                    model_name="Belum dilatih",
                    model_version="0.0.0",
                    model_file="models/active_model.pkl",
                    model_status="active",
                    updated_date=datetime.now(timezone.utc),
                    metrics_json=json.dumps(
                        {
                            "accuracy": None,
                            "macro_f1": None,
                            "precision": None,
                            "recall": None,
                            "confusion_matrix": [],
                        }
                    ),
                )
            )
            db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Sistem Klasifikasi Ukuran Tanah Longsor BASARNAS",
    version="1.0.0",
    lifespan=lifespan,
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(predict_router)
app.include_router(history_router)
app.include_router(model_router, prefix="/api/model")
app.include_router(model_router, prefix="/api/models", include_in_schema=False)


@app.get("/api/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
