from pydantic import BaseModel, Field, field_validator

from telemetry_stream.allowed_classifications import allowed_classifications


def validate_classification(value: str) -> str:
    if value not in allowed_classifications:
        raise ValueError(f"classification must be one of {allowed_classifications}")

    return value


class TelemetryEventCreate(BaseModel):
    timestamp: str
    event_type: str
    source: str
    classification: str
    message: str
    context: str
    flagged: bool = False
    object_id: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    altitude_m: float | None = None
    grid: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("timestamp", "event_type", "source")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be empty")

        return value

    @field_validator("classification")
    @classmethod
    def check_classification(cls, value: str) -> str:
        return validate_classification(value)


class TelemetryEventUpdate(BaseModel):
    timestamp: str | None = None
    event_type: str | None = None
    source: str | None = None
    classification: str | None = None
    message: str | None = None
    context: str | None = None
    flagged: bool | None = None
    object_id: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    altitude_m: float | None = None
    grid: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("classification")
    @classmethod
    def check_classification(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return validate_classification(value)
