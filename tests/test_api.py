from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from telemetry_stream.api import (
    app,
    collector,
    event_1,
    event_2,
    event_3,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_collector() -> Iterator[None]:
    collector.events.clear()

    collector.add_event(event_1)
    collector.add_event(event_2)
    collector.add_event(event_3)

    yield

    collector.events.clear()


def test_read_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Telemetry Stream API is running",
    }


def test_read_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
    }


def test_read_event_count() -> None:
    response = client.get("/event-count")

    assert response.status_code == 200
    assert response.json() == {
        "event_count": 3,
    }


def test_read_all_events() -> None:
    response = client.get("/events")

    assert response.status_code == 200

    events = response.json()

    assert len(events) == 3
    assert events[0]["source"] == "sensor-1"
    assert events[1]["source"] == "server-1"
    assert events[2]["source"] == "server-2"


def test_filter_events_by_source() -> None:
    response = client.get(
        "/events",
        params={"source": "server-1"},
    )

    assert response.status_code == 200

    events = response.json()

    assert len(events) == 1
    assert events[0]["source"] == "server-1"


def test_filter_events_with_no_match() -> None:
    response = client.get(
        "/events",
        params={"source": "unknown-server"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_read_flagged_events() -> None:
    response = client.get("/events/flagged")

    assert response.status_code == 200

    events = response.json()

    assert len(events) == 2
    assert all(event["flagged"] is True for event in events)


def test_create_event_successfully() -> None:
    new_event = {
        "timestamp": "2026-09-03T10:00:00Z",
        "event_type": "login",
        "source": "server-3",
        "classification": "warning",
        "message": "Failed login detected",
        "context": "authentication",
        "flagged": True,
    }

    response = client.post(
        "/events",
        json=new_event,
    )

    assert response.status_code == 201
    assert response.json()["source"] == "server-3"
    assert collector.event_count == 4


def test_create_event_with_invalid_classification() -> None:
    invalid_event = {
        "timestamp": "2026-09-03T10:00:00Z",
        "event_type": "login",
        "source": "server-3",
        "classification": "danger",
        "message": "Invalid event",
        "context": "authentication",
        "flagged": True,
    }

    response = client.post(
        "/events",
        json=invalid_event,
    )

    assert response.status_code == 422
    assert collector.event_count == 3


def test_create_event_with_empty_source() -> None:
    invalid_event = {
        "timestamp": "2026-09-03T10:00:00Z",
        "event_type": "login",
        "source": "",
        "classification": "warning",
        "message": "Invalid event",
        "context": "authentication",
        "flagged": True,
    }

    response = client.post(
        "/events",
        json=invalid_event,
    )

    assert response.status_code == 422
    assert collector.event_count == 3


def test_read_one_event() -> None:
    response = client.get("/events/0")

    assert response.status_code == 200
    assert response.json()["source"] == "sensor-1"


def test_read_missing_event() -> None:
    response = client.get("/events/99")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Event not found",
    }


def test_replace_event() -> None:
    replacement_event = {
        "timestamp": "2026-09-03T11:00:00Z",
        "event_type": "recovery",
        "source": "sensor-primary",
        "classification": "info",
        "message": "Sensor recovered successfully",
        "context": "network",
        "flagged": False,
    }

    response = client.put(
        "/events/0",
        json=replacement_event,
    )

    assert response.status_code == 200
    assert response.json()["source"] == "sensor-primary"
    assert collector.events[0].source == "sensor-primary"
    assert collector.event_count == 3


def test_replace_missing_event() -> None:
    replacement_event = {
        "timestamp": "2026-09-03T11:00:00Z",
        "event_type": "recovery",
        "source": "sensor-primary",
        "classification": "info",
        "message": "Sensor recovered successfully",
        "context": "network",
        "flagged": False,
    }

    response = client.put(
        "/events/99",
        json=replacement_event,
    )

    assert response.status_code == 404


def test_delete_event() -> None:
    response = client.delete("/events/0")

    assert response.status_code == 200
    assert response.json()["message"] == "Event deleted successfully"
    assert collector.event_count == 2


def test_delete_missing_event() -> None:
    response = client.delete("/events/99")

    assert response.status_code == 404
    assert collector.event_count == 3
