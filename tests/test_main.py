from pathlib import Path

import pytest

from tit_stream.collector import TelemetryCollector
from tit_stream.models import TelemetryEvent


def test_create_valid_event() -> None:
    event = TelemetryEvent(
        timestamp="2026-08-24T12:00:00Z",
        event_type="INFO",
        source="sensor-1",
        classification="info",
        message="System nominal",
        context="startup",
        flagged=False,
    )
    assert event.timestamp == "2026-08-24T12:00:00Z"
    assert event.source == "sensor-1"
    assert event.classification == "info"
    assert event.flagged is False


def test_empty_timestamp_raises_error() -> None:
    with pytest.raises(ValueError, match="Timestamp cannot be empty"):
        TelemetryEvent(
            timestamp="",
            event_type="INFO",
            source="sensor-1",
            classification="info",
            message="System nominal",
            context="startup",
            flagged=False,
        )


def test_json_persistence(tmp_path: Path) -> None:
    original_collector = TelemetryCollector()

    event = TelemetryEvent(
        timestamp="2026-08-24T12:00:00Z",
        event_type="INFO",
        source="sensor-1",
        classification="info",
        message="System nominal",
        context="startup",
        flagged=False,
    )

    original_collector.add_event(event)

    json_path = tmp_path / "events.json"
    original_collector.save_to_json(json_path)

    loaded_collector = TelemetryCollector()
    loaded_collector.load_from_json(json_path)

    assert loaded_collector.event_count == original_collector.event_count
    assert loaded_collector.events[0].timestamp == event.timestamp
    assert loaded_collector.events[0].event_type == event.event_type
    assert loaded_collector.events[0].source == event.source
    assert loaded_collector.events[0].classification == event.classification
    assert loaded_collector.events[0].message == event.message
    assert loaded_collector.events[0].context == event.context
    assert loaded_collector.events[0].flagged == event.flagged
