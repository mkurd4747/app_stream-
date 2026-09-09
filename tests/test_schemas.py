import pytest
from pydantic import ValidationError

from telemetry_stream.schemas import (
    TelemetryEventCreate,
    TelemetryEventUpdate,
)


def test_create_valid_schema() -> None:
    event = TelemetryEventCreate(
        timestamp="2026-09-03T10:00:00Z",
        event_type="login",
        source="server-1",
        classification="warning",
        message="Failed login",
        context="authentication",
        flagged=True,
    )

    assert event.source == "server-1"
    assert event.classification == "warning"
    assert event.flagged is True


def test_reject_empty_timestamp() -> None:
    with pytest.raises(ValidationError):
        TelemetryEventCreate(
            timestamp="",
            event_type="login",
            source="server-1",
            classification="warning",
            message="Failed login",
            context="authentication",
            flagged=True,
        )


def test_reject_blank_source() -> None:
    with pytest.raises(ValidationError):
        TelemetryEventCreate(
            timestamp="2026-09-03T10:00:00Z",
            event_type="login",
            source="   ",
            classification="warning",
            message="Failed login",
            context="authentication",
            flagged=True,
        )


def test_reject_invalid_classification() -> None:
    with pytest.raises(ValidationError):
        TelemetryEventCreate(
            timestamp="2026-09-03T10:00:00Z",
            event_type="login",
            source="server-1",
            classification="danger",  # type: ignore[arg-type]
            message="Failed login",
            context="authentication",
            flagged=True,
        )


def test_update_allows_partial_data() -> None:
    update = TelemetryEventUpdate(
        classification="critical",
    )

    changes = update.model_dump(exclude_unset=True)

    assert changes == {
        "classification": "critical",
    }
