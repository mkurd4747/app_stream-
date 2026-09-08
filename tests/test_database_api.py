import logging

import pytest
from fastapi.testclient import TestClient


def create_event(
    client: TestClient,
    event_data: dict[str, object],
) -> int:
    response = client.post(
        "/events",
        json=event_data,
    )

    assert response.status_code == 201

    event_id: int = response.json()["id"]

    return event_id


def test_create_event(
    client: TestClient,
    valid_event_data: dict[str, object],
) -> None:
    response = client.post(
        "/events",
        json=valid_event_data,
    )

    assert response.status_code == 201
    assert response.json()["source"] == "server-1"
    assert response.json()["id"] is not None


def test_read_event(
    client: TestClient,
    valid_event_data: dict[str, object],
) -> None:
    event_id = create_event(client, valid_event_data)

    response = client.get(f"/events/{event_id}")

    assert response.status_code == 200
    assert response.json()["id"] == event_id
    assert response.json()["classification"] == "warning"


def test_read_missing_event(
    client: TestClient,
) -> None:
    response = client.get("/events/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Event not found",
    }


def test_filter_by_source(
    client: TestClient,
    valid_event_data: dict[str, object],
) -> None:
    create_event(client, valid_event_data)

    response = client.get(
        "/events",
        params={"source": "server-1"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_filter_with_no_match(
    client: TestClient,
    valid_event_data: dict[str, object],
) -> None:
    create_event(client, valid_event_data)

    response = client.get(
        "/events",
        params={"source": "unknown-server"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_update_event(
    client: TestClient,
    valid_event_data: dict[str, object],
) -> None:
    event_id = create_event(client, valid_event_data)

    response = client.patch(
        f"/events/{event_id}",
        json={
            "classification": "critical",
            "flagged": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["classification"] == "critical"


def test_delete_event(
    client: TestClient,
    valid_event_data: dict[str, object],
) -> None:
    event_id = create_event(client, valid_event_data)

    delete_response = client.delete(f"/events/{event_id}")
    read_response = client.get(f"/events/{event_id}")

    assert delete_response.status_code == 200
    assert read_response.status_code == 404


def test_reject_invalid_event(
    client: TestClient,
) -> None:
    response = client.post(
        "/events",
        json={
            "timestamp": "",
            "event_type": "login",
            "source": "server-1",
            "classification": "danger",
            "message": "Invalid event",
            "context": "authentication",
            "flagged": True,
        },
    )

    assert response.status_code == 422


def test_create_event_writes_log(
    client: TestClient,
    valid_event_data: dict[str, object],
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO):
        response = client.post(
            "/events",
            json=valid_event_data,
        )

    assert response.status_code == 201
    assert "Created event" in caplog.text


def test_health_check(
    client: TestClient,
) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_readiness_check(
    client: TestClient,
) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "connected",
    }


def test_response_contains_request_id(
    client: TestClient,
) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"] != ""


def test_existing_request_id_is_preserved(
    client: TestClient,
) -> None:
    request_id = "test-request-123"

    response = client.get(
        "/health",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_request_is_logged(
    client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO):
        response = client.get(
            "/health",
            headers={"X-Request-ID": "logging-test-123"},
        )

    assert response.status_code == 200
    assert "Request completed" in caplog.text
    assert "method=GET" in caplog.text
    assert "path=/health" in caplog.text
    assert "status_code=200" in caplog.text
    assert "request_id=logging-test-123" in caplog.text
