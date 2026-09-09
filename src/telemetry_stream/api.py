from typing import Literal

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, field_validator

from telemetry_stream.collector import TelemetryCollector
from telemetry_stream.models import TelemetryEvent

app = FastAPI(
    title="Telemetry Stream API",
    description="API for receiving and reviewing telemetry events",
    version="1.0.0",
)

collector = TelemetryCollector()


class TelemetryEventRequest(BaseModel):
    timestamp: str
    event_type: str
    source: str
    classification: Literal["info", "warning", "critical"]
    message: str
    context: str
    flagged: bool

    @field_validator("timestamp", "event_type", "source")
    @classmethod
    def reject_empty_values(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be empty")

        return value


event_1 = TelemetryEvent(
    timestamp="2026-09-03T09:00:00Z",
    event_type="ping",
    source="sensor-1",
    classification="info",
    message="System responded successfully",
    context="network",
    flagged=False,
)

event_2 = TelemetryEvent(
    timestamp="2026-09-03T09:05:00Z",
    event_type="login",
    source="server-1",
    classification="warning",
    message="Multiple failed login attempts",
    context="authentication",
    flagged=True,
)

event_3 = TelemetryEvent(
    timestamp="2026-09-03T09:10:00Z",
    event_type="syscall",
    source="server-2",
    classification="critical",
    message="Restricted system call detected",
    context="security",
    flagged=True,
)

collector.add_event(event_1)
collector.add_event(event_2)
collector.add_event(event_3)


def event_to_dictionary(
    event: TelemetryEvent,
) -> dict[str, str | bool]:
    return {
        "timestamp": event.timestamp,
        "event_type": event.event_type,
        "source": event.source,
        "classification": event.classification,
        "message": event.message,
        "context": event.context,
        "flagged": event.flagged,
    }


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": "Telemetry Stream API is running",
    }


@app.get("/health")
def read_health() -> dict[str, str]:
    return {
        "status": "healthy",
    }


@app.get("/event-count")
def read_event_count() -> dict[str, int]:
    return {
        "event_count": collector.event_count,
    }


@app.get("/events")
def read_events(
    source: str | None = None,
) -> list[dict[str, str | bool]]:
    if source is None:
        selected_events = collector.events
    else:
        selected_events = collector.get_events_by_source(source)

    return [event_to_dictionary(event) for event in selected_events]


@app.post(
    "/events",
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    event_data: TelemetryEventRequest,
) -> dict[str, str | bool]:
    event = TelemetryEvent(
        timestamp=event_data.timestamp,
        event_type=event_data.event_type,
        source=event_data.source,
        classification=event_data.classification,
        message=event_data.message,
        context=event_data.context,
        flagged=event_data.flagged,
    )

    collector.add_event(event)

    return event_to_dictionary(event)


@app.get("/events/flagged")
def read_flagged_events() -> list[dict[str, str | bool]]:
    flagged_events = collector.get_flagged_events()

    return [event_to_dictionary(event) for event in flagged_events]


@app.get("/sources")
def read_unique_sources() -> list[str]:
    return sorted(collector.get_unique_sources())


@app.get("/classification-counts")
def read_classification_counts() -> dict[str, int]:
    return collector.count_by_classification()


def validate_event_index(event_index: int) -> None:
    if event_index < 0 or event_index >= collector.event_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )


@app.get("/events/{event_index}")
def read_event(
    event_index: int,
) -> dict[str, str | bool]:
    validate_event_index(event_index)

    event = collector.events[event_index]

    return event_to_dictionary(event)


@app.put("/events/{event_index}")
def replace_event(
    event_index: int,
    event_data: TelemetryEventRequest,
) -> dict[str, str | bool]:
    validate_event_index(event_index)

    updated_event = TelemetryEvent(
        timestamp=event_data.timestamp,
        event_type=event_data.event_type,
        source=event_data.source,
        classification=event_data.classification,
        message=event_data.message,
        context=event_data.context,
        flagged=event_data.flagged,
    )

    collector.events[event_index] = updated_event

    return event_to_dictionary(updated_event)


@app.delete("/events/{event_index}")
def delete_event(
    event_index: int,
) -> dict[str, str | int]:
    validate_event_index(event_index)

    deleted_event = collector.events.pop(event_index)

    return {
        "message": "Event deleted successfully",
        "deleted_event_index": event_index,
        "deleted_event_source": deleted_event.source,
    }
