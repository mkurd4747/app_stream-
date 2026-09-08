from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from tit_stream.database import get_session
from tit_stream.database_api import app


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

    test_client = TestClient(app)

    yield test_client

    test_client.close()
    app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture
def valid_event_data() -> dict[str, object]:
    return {
        "timestamp": "2026-09-03T10:00:00Z",
        "event_type": "login",
        "source": "server-1",
        "classification": "warning",
        "message": "Multiple failed login attempts",
        "context": "authentication",
        "flagged": True,
    }
