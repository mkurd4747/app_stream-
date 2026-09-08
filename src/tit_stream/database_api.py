import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from sqlalchemy import text
from sqlmodel import Session, select

from tit_stream.database import create_database, get_session
from tit_stream.database_models import TelemetryEventRecord
from tit_stream.logging_config import configure_logging
from tit_stream.schemas import (
    TelemetryEventCreate,
    TelemetryEventUpdate,
)

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_database()
    yield


app = FastAPI(
    title="Persistent Telemetry Stream API",
    version="2.0.0",
    lifespan=lifespan,
)

SessionDependency = Annotated[Session, Depends(get_session)]


@app.middleware("http")
async def log_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get(
        "X-Request-ID",
        str(uuid4()),
    )
    start_time = perf_counter()

    response = await call_next(request)

    duration_ms = (perf_counter() - start_time) * 1000

    response.headers["X-Request-ID"] = request_id

    logger.info(
        "Request completed method=%s path=%s status_code=%s duration_ms=%.2f request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
    )

    return response


def find_event_or_404(
    event_id: int,
    session: Session,
) -> TelemetryEventRecord:
    event = session.get(TelemetryEventRecord, event_id)

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    return event


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": "Persistent Telemetry API is running",
    }


@app.post(
    "/events",
    response_model=TelemetryEventRecord,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    event_data: TelemetryEventCreate,
    session: SessionDependency,
) -> TelemetryEventRecord:
    event = TelemetryEventRecord(
        **event_data.model_dump(),
    )

    session.add(event)
    session.commit()
    session.refresh(event)
    logger.info(
        "Created event id=%s source=%s",
        event.id,
        event.source,
    )

    return event


@app.get(
    "/events",
    response_model=list[TelemetryEventRecord],
)
def read_events(
    session: SessionDependency,
    source: str | None = None,
    classification: str | None = None,
    flagged: bool | None = None,
    offset: int = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[TelemetryEventRecord]:
    statement = select(TelemetryEventRecord)

    if source is not None:
        statement = statement.where(TelemetryEventRecord.source == source)

    if classification is not None:
        statement = statement.where(TelemetryEventRecord.classification == classification)

    if flagged is not None:
        statement = statement.where(TelemetryEventRecord.flagged == flagged)

    statement = statement.offset(offset).limit(limit)

    return list(session.exec(statement).all())


@app.get(
    "/events/{event_id}",
    response_model=TelemetryEventRecord,
)
def read_event(
    event_id: int,
    session: SessionDependency,
) -> TelemetryEventRecord:
    return find_event_or_404(event_id, session)


@app.patch(
    "/events/{event_id}",
    response_model=TelemetryEventRecord,
)
def update_event(
    event_id: int,
    event_data: TelemetryEventUpdate,
    session: SessionDependency,
) -> TelemetryEventRecord:
    event = find_event_or_404(event_id, session)

    updates = event_data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(event, field, value)

    session.add(event)
    session.commit()
    session.refresh(event)
    logger.info(
        "Updated event id=%s",
        event.id,
    )

    return event


@app.delete("/events/{event_id}")
def delete_event(
    event_id: int,
    session: SessionDependency,
) -> dict[str, str]:
    event = session.get(
        TelemetryEventRecord,
        event_id,
    )

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    session.delete(event)
    session.commit()

    return {
        "message": "Event deleted successfully",
    }


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/ready", tags=["Health"])
def readiness_check(
    session: Session = Depends(get_session),
) -> dict[str, str]:
    try:
        session.connection().execute(text("SELECT 1"))
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from error

    return {
        "status": "ready",
        "database": "connected",
    }
