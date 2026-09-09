import logging

import pytest
from fastapi.testclient import TestClient

from telemetry_stream.database_api import settings


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
    assert response.json()["classification"] == "SECRET"


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
            "classification": "TOP_SECRET",
            "flagged": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["classification"] == "TOP_SECRET"


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


def test_create_event_with_geospatial_and_confidence_fields(
    client: TestClient,
    valid_event_data: dict[str, object],
) -> None:
    event_data = {
        **valid_event_data,
        "object_id": "3f29a1c4-6b7d-4e2a-9c11-8a4d2f6e9b02",
        "latitude": 34.0522,
        "longitude": -118.2437,
        "altitude_m": 71.5,
        "grid": "11SLT1234567890",
        "confidence": 0.9,
    }

    response = client.post(
        "/events",
        json=event_data,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["object_id"] == "3f29a1c4-6b7d-4e2a-9c11-8a4d2f6e9b02"
    assert body["latitude"] == 34.0522
    assert body["longitude"] == -118.2437
    assert body["altitude_m"] == 71.5
    assert body["grid"] == "11SLT1234567890"
    assert body["confidence"] == 0.9


def test_create_event_without_geospatial_fields_defaults_to_null(
    client: TestClient,
    valid_event_data: dict[str, object],
) -> None:
    response = client.post(
        "/events",
        json=valid_event_data,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["object_id"] is None
    assert body["latitude"] is None
    assert body["confidence"] is None


def test_reject_confidence_above_one(
    client: TestClient,
    valid_event_data: dict[str, object],
) -> None:
    event_data = {**valid_event_data, "confidence": 1.5}

    response = client.post(
        "/events",
        json=event_data,
    )

    assert response.status_code == 422


def test_reject_latitude_out_of_range(
    client: TestClient,
    valid_event_data: dict[str, object],
) -> None:
    event_data = {**valid_event_data, "latitude": 200.0}

    response = client.post(
        "/events",
        json=event_data,
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


def test_creating_top_secret_event_logs_warning(
    client: TestClient,
    valid_event_data: dict[str, object],
    caplog: pytest.LogCaptureFixture,
) -> None:
    event_data = {**valid_event_data, "classification": "TOP_SECRET"}

    with caplog.at_level(logging.INFO):
        response = client.post(
            "/events",
            json=event_data,
        )

    assert response.status_code == 201
    top_secret_records = [
        record for record in caplog.records if "Top secret event recorded" in record.message
    ]
    assert len(top_secret_records) == 1
    assert top_secret_records[0].levelno == logging.WARNING


def test_creating_non_top_secret_event_does_not_log_warning(
    client: TestClient,
    valid_event_data: dict[str, object],
    caplog: pytest.LogCaptureFixture,
) -> None:
    event_data = {**valid_event_data, "classification": "UNCLASSIFIED"}

    with caplog.at_level(logging.INFO):
        response = client.post(
            "/events",
            json=event_data,
        )

    assert response.status_code == 201
    assert "Top secret event recorded" not in caplog.text


def test_updating_event_to_top_secret_logs_warning(
    client: TestClient,
    valid_event_data: dict[str, object],
    caplog: pytest.LogCaptureFixture,
) -> None:
    event_id = create_event(client, valid_event_data)

    with caplog.at_level(logging.INFO):
        response = client.patch(
            f"/events/{event_id}",
            json={"classification": "TOP_SECRET"},
        )

    assert response.status_code == 200
    top_secret_records = [
        record for record in caplog.records if "Top secret event recorded" in record.message
    ]
    assert len(top_secret_records) == 1
    assert top_secret_records[0].levelno == logging.WARNING


def test_issue_token_with_valid_credentials(
    unauthenticated_client: TestClient,
) -> None:

    response = unauthenticated_client.post(
        "/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": settings.oauth_client_id,
            "client_secret": settings.oauth_client_secret,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] > 0


def test_issue_token_with_wrong_client_secret_is_rejected(
    unauthenticated_client: TestClient,
) -> None:

    response = unauthenticated_client.post(
        "/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": settings.oauth_client_id,
            "client_secret": "wrong-secret",
        },
    )

    assert response.status_code == 401


def test_issue_token_with_unsupported_grant_type_is_rejected(
    unauthenticated_client: TestClient,
) -> None:

    response = unauthenticated_client.post(
        "/oauth/token",
        data={
            "grant_type": "password",
            "client_id": settings.oauth_client_id,
            "client_secret": settings.oauth_client_secret,
        },
    )

    assert response.status_code == 400


def test_create_event_without_access_token_is_rejected(
    unauthenticated_client: TestClient,
    valid_event_data: dict[str, object],
) -> None:
    response = unauthenticated_client.post(
        "/events",
        json=valid_event_data,
    )

    assert response.status_code == 401


def test_create_event_with_invalid_access_token_is_rejected(
    unauthenticated_client: TestClient,
    valid_event_data: dict[str, object],
) -> None:
    response = unauthenticated_client.post(
        "/events",
        json=valid_event_data,
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401


def test_read_events_without_access_token_is_rejected(
    unauthenticated_client: TestClient,
) -> None:
    response = unauthenticated_client.get("/events")

    assert response.status_code == 401


def test_read_event_without_access_token_is_rejected(
    client: TestClient,
    unauthenticated_client: TestClient,
    valid_event_data: dict[str, object],
) -> None:
    event_id = create_event(client, valid_event_data)

    response = unauthenticated_client.get(f"/events/{event_id}")

    assert response.status_code == 401


def test_update_event_without_access_token_is_rejected(
    client: TestClient,
    unauthenticated_client: TestClient,
    valid_event_data: dict[str, object],
) -> None:
    event_id = create_event(client, valid_event_data)

    response = unauthenticated_client.patch(
        f"/events/{event_id}",
        json={"flagged": True},
    )

    assert response.status_code == 401


def test_delete_event_without_access_token_is_rejected(
    client: TestClient,
    unauthenticated_client: TestClient,
    valid_event_data: dict[str, object],
) -> None:
    event_id = create_event(client, valid_event_data)

    response = unauthenticated_client.delete(f"/events/{event_id}")

    assert response.status_code == 401


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


def test_failed_request_is_logged_at_warning_level(
    unauthenticated_client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO):
        response = unauthenticated_client.get("/events")

    assert response.status_code == 401
    matching_records = [
        record for record in caplog.records if "Request completed" in record.message
    ]
    assert len(matching_records) == 1
    assert matching_records[0].levelno == logging.WARNING


def test_successful_request_is_logged_at_info_level(
    client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO):
        response = client.get("/health")

    assert response.status_code == 200
    matching_records = [
        record for record in caplog.records if "Request completed" in record.message
    ]
    assert len(matching_records) == 1
    assert matching_records[0].levelno == logging.INFO


def test_metrics_endpoint(
    client: TestClient,
) -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "telemetry_stream_http_requests_total" in response.text
    assert "telemetry_stream_http_request_duration_seconds" in response.text


def test_health_request_is_recorded_in_metrics(
    client: TestClient,
) -> None:
    health_response = client.get("/health")
    metrics_response = client.get("/metrics")

    assert health_response.status_code == 200
    assert metrics_response.status_code == 200
    assert 'path="/health"' in metrics_response.text
    assert 'method="GET"' in metrics_response.text
    assert 'status_code="200"' in metrics_response.text
