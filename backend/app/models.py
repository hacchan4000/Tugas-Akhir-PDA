from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    input_data: Mapped[list["InputData"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    classification_history: Mapped[list["ClassificationHistory"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class InputData(Base):
    __tablename__ = "input_data"

    input_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    event_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    landslide_category: Mapped[str] = mapped_column(String(100), nullable=False)
    landslide_trigger: Mapped[str] = mapped_column(String(100), nullable=False)
    landslide_setting: Mapped[str] = mapped_column(String(100), nullable=False)
    location_accuracy: Mapped[str] = mapped_column(String(100), nullable=False)
    nama_wilayah: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    user: Mapped["User"] = relationship(back_populates="input_data")
    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="input_data",
        cascade="all, delete-orphan",
    )
    classification_history: Mapped[list["ClassificationHistory"]] = relationship(
        back_populates="input_data",
        cascade="all, delete-orphan",
    )


class Model(Base):
    __tablename__ = "models"

    model_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    model_file: Mapped[str] = mapped_column(String(500), nullable=False)
    model_status: Mapped[str] = mapped_column(String(50), nullable=False, default="inactive")
    updated_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
    metrics_json: Mapped[str] = mapped_column(Text, nullable=True)

    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="model",
        cascade="all, delete-orphan",
    )


class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    input_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("input_data.input_id", ondelete="CASCADE"),
        nullable=False,
    )
    model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("models.model_id", ondelete="RESTRICT"),
        nullable=False,
    )
    predicted_class: Mapped[str] = mapped_column(String(20), nullable=False)
    sar_priority: Mapped[str] = mapped_column(Text, nullable=False)
    prediction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    input_data: Mapped["InputData"] = relationship(back_populates="predictions")
    model: Mapped["Model"] = relationship(back_populates="predictions")


class ClassificationHistory(Base):
    __tablename__ = "classification_history"

    history_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    input_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("input_data.input_id", ondelete="CASCADE"),
        nullable=False,
    )
    classification_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    status: Mapped[str] = mapped_column(String(100), nullable=False)

    user: Mapped["User"] = relationship(back_populates="classification_history")
    input_data: Mapped["InputData"] = relationship(back_populates="classification_history")
