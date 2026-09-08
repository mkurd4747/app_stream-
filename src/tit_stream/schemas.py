from typing import Literal

from pydantic import BaseModel, field_validator


class TelemetryEventCreate(BaseModel):
    timestamp: str
    event_type: str
    source: str
    classification: Literal["info", "warning", "critical"]
    message: str
    context: str
    flagged: bool = False

    @field_validator("timestamp", "event_type", "source")
    @classmethod
    def reject_blank_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be empty")

        return value


class TelemetryEventUpdate(BaseModel):
    timestamp: str | None = None
    event_type: str | None = None
    source: str | None = None
    classification: Literal["info", "warning", "critical"] | None = None
    message: str | None = None
    context: str | None = None
    flagged: bool | None = None
