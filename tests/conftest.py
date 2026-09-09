from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from telemetry_stream.database_api import app, get_session, settings


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    SQLModel.metadata.create_all(test_engine)

    def override_get_session() -> Generator[Session, None, None]:
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        token_response = test_client.post(
            "/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": settings.oauth_client_id,
                "client_secret": settings.oauth_client_secret,
            },
        )
        access_token = token_response.json()["access_token"]
        test_client.headers["Authorization"] = f"Bearer {access_token}"

        yield test_client

    app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture
def unauthenticated_client(client: TestClient) -> TestClient:
    del client

    return TestClient(app)


@pytest.fixture
def valid_event_data() -> dict[str, object]:
    return {
        "timestamp": "2026-09-03T10:00:00Z",
        "event_type": "login",
        "source": "server-1",
        "classification": "SECRET",
        "message": "Multiple failed login attempts",
        "context": "authentication",
        "flagged": True,
    }
