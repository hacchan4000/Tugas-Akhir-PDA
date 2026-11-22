from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class LandslideCategory(str, Enum):
    TANAH_LONGSOR = "tanah_longsor"
    MUDFLOW = "mudflow"
    DEBRIS_FLOW = "debris_flow"
    ROCKFALL = "rockfall"


class LandslideTrigger(str, Enum):
    HUJAN = "hujan"
    EARTHQUAKE = "earthquake"
    HUMAN_ACTIVITY = "human_activity"
    EROSION = "erosion"
    VOLCANIC_ACTIVITY = "volcanic_activity"
    FLOOD = "flood"


class LandslideSetting(str, Enum):
    NATURAL_SLOPE = "natural_slope"
    CUT_SLOPE = "cut_slope"
    FILL_SLOPE = "fill_slope"
    ROAD = "road"
    RIVERBANK = "riverbank"
    COASTAL = "coastal"
    MINING_AREA = "mining_area"


class LocationAccuracy(str, Enum):
    EXACT = "exact"
    APPROXIMATE = "approximate"
    LOCAL = "local"
    REGIONAL = "regional"


class RequiredTextModel(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def reject_blank_strings(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            raise ValueError("field tidak boleh kosong")
        return value


class LandslideInputCreate(RequiredTextModel):
    event_date: date
    latitude: float = Field(ge=-90.0, le=90.0, allow_inf_nan=False)
    longitude: float = Field(ge=-180.0, le=180.0, allow_inf_nan=False)
    landslide_category: LandslideCategory
    landslide_trigger: LandslideTrigger
    landslide_setting: LandslideSetting
    location_accuracy: LocationAccuracy
    nama_wilayah: str = Field(min_length=1, max_length=255)

    @field_validator("nama_wilayah")
    @classmethod
    def validate_nama_wilayah(cls, value: str) -> str:
        return value.strip()


class LandslideInputResponse(LandslideInputCreate):
    model_config = ConfigDict(from_attributes=True)

    input_id: int
    user_id: int
    created_at: datetime


class UserCreate(RequiredTextModel):
    username: str = Field(min_length=1, max_length=100)
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=255)

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        return value.strip()


class UserLogin(RequiredTextModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=255)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class ModelMetrics(BaseModel):
    accuracy: float = Field(ge=0.0, le=1.0)
    macro_f1: float = Field(ge=0.0, le=1.0)
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    confusion_matrix: list[list[int]]


class ModelCreate(BaseModel):
    model_name: str = Field(min_length=1, max_length=255)
    model_version: str = Field(min_length=1, max_length=100)
    model_file: str = Field(min_length=1, max_length=500)
    model_status: Literal["active", "inactive"] = "inactive"
    metrics_json: str | None = None


class ModelResponse(ModelCreate):
    model_config = ConfigDict(from_attributes=True)

    model_id: int
    updated_date: datetime


class PredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prediction_id: int
    input_id: int
    model_id: int
    predicted_class: Literal["small", "medium", "large"]
    sar_priority: str
    prediction_date: datetime


class ClassificationHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    history_id: int
    user_id: int
    input_id: int
    classification_date: datetime
    status: str


class HistoryItemResponse(BaseModel):
    history_id: int
    user_id: int
    input_id: int
    classification_date: datetime
    status: str
    nama_wilayah: str
    predicted_class: Literal["small", "medium", "large"] | None


class ModelActiveResponse(BaseModel):
    model_id: int
    algorithm: str
    version: str
    training_date: datetime | None
    accuracy: float | None
    macro_f1: float | None
    precision: float | None
    recall: float | None
    confusion_matrix: list[list[int]]


class PredictionOutputResponse(BaseModel):
    predicted_class: Literal["small", "medium", "large"]
    sar_priority: str
    nama_wilayah: str
    model: dict[str, object]
    prediction_id: int
    input_id: int
    history_id: int
