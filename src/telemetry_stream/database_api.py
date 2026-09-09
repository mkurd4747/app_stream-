import logging
import secrets
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from time import perf_counter
from typing import Annotated
from uuid import uuid4

import jwt
from fastapi import (
    Depends,
    FastAPI,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel
from sqlalchemy import text
from sqlmodel import Session, select

from telemetry_stream.allowed_classifications import allowed_classifications
from telemetry_stream.config import get_settings
from telemetry_stream.database import create_database, get_session
from telemetry_stream.database_models import TelemetryEventRecord
from telemetry_stream.logging_config import configure_logging
from telemetry_stream.schemas import (
    TelemetryEventCreate,
    TelemetryEventUpdate,
)

configure_logging()

logger = logging.getLogger(__name__)

REQUEST_COUNT = Counter(
    "telemetry_stream_http_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status_code"],
)

REQUEST_DURATION = Histogram(
    "telemetry_stream_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_database()
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

SessionDependency = Annotated[Session, Depends(get_session)]

bearer_scheme = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]

TOKEN_ALGORITHM = "HS256"
PROTECTED_CLASSIFICATIONS = set(allowed_classifications)
HIGHEST_SENSITIVITY_CLASSIFICATION = "TOP_SECRET"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def create_access_token(client_id: str) -> tuple[str, int]:
    expires_in = timedelta(minutes=settings.oauth_token_expire_minutes)
    expires_at = datetime.now(UTC) + expires_in

    access_token = jwt.encode(
        {"sub": client_id, "exp": expires_at},
        settings.oauth_signing_key,
        algorithm=TOKEN_ALGORITHM,
    )

    return access_token, int(expires_in.total_seconds())


def verify_classification_access(
    classification: str,
    credentials: HTTPAuthorizationCredentials | None,
) -> None:
    if classification not in PROTECTED_CLASSIFICATIONS:
        return

    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"A valid access token is required for '{classification}' events",
    )

    if credentials is None:
        raise unauthorized

    try:
        jwt.decode(
            credentials.credentials,
            settings.oauth_signing_key,
            algorithms=[TOKEN_ALGORITHM],
        )
    except jwt.InvalidTokenError as error:
        raise unauthorized from error


@app.post("/oauth/token", response_model=TokenResponse, tags=["Auth"])
def issue_token(
    grant_type: Annotated[str, Form()],
    client_id: Annotated[str, Form()],
    client_secret: Annotated[str, Form()],
) -> TokenResponse:
    if grant_type != "client_credentials":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only the client_credentials grant type is supported",
        )

    valid_client_id = secrets.compare_digest(client_id, settings.oauth_client_id)
    valid_client_secret = secrets.compare_digest(
        client_secret,
        settings.oauth_client_secret,
    )

    if not (valid_client_id and valid_client_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials",
        )

    access_token, expires_in = create_access_token(client_id)

    return TokenResponse(access_token=access_token, expires_in=expires_in)


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

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (perf_counter() - start_time) * 1000

        logger.exception(
            "Request failed method=%s path=%s duration_ms=%.2f request_id=%s",
            request.method,
            request.url.path,
            duration_ms,
            request_id,
        )

        raise

    duration_seconds = perf_counter() - start_time
    duration_ms = duration_seconds * 1000

    response.headers["X-Request-ID"] = request_id

    REQUEST_COUNT.labels(
        method=request.method,
        path=request.url.path,
        status_code=str(response.status_code),
    ).inc()

    REQUEST_DURATION.labels(
        method=request.method,
        path=request.url.path,
    ).observe(duration_seconds)

    if response.status_code >= 500:
        log_level = logging.ERROR
    elif response.status_code >= 400:
        log_level = logging.WARNING
    else:
        log_level = logging.INFO

    logger.log(
        log_level,
        "Request completed method=%s path=%s status_code=%s duration_ms=%.2f request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
    )

    return response


def log_if_top_secret(event: TelemetryEventRecord) -> None:
    if event.classification != HIGHEST_SENSITIVITY_CLASSIFICATION:
        return

    logger.warning(
        "Top secret event recorded id=%s source=%s event_type=%s message=%s",
        event.id,
        event.source,
        event.event_type,
        event.message,
    )


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


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
    }


@app.get("/ready", tags=["Health"])
def readiness_check(
    session: SessionDependency,
) -> dict[str, str]:
    try:
        session.connection().execute(text("SELECT 1"))
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from error

    return {
        "status": "ready",
        "database": "connected",
    }


@app.get(
    "/metrics",
    tags=["Monitoring"],
    include_in_schema=False,
)
def metrics() -> Response:
    return Response(
        content=generate_latest(),
        headers={
            "Content-Type": CONTENT_TYPE_LATEST,
        },
    )


@app.post(
    "/events",
    response_model=TelemetryEventRecord,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    event_data: TelemetryEventCreate,
    session: SessionDependency,
    credentials: BearerCredentials = None,
) -> TelemetryEventRecord:
    verify_classification_access(event_data.classification, credentials)

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

    log_if_top_secret(event)

    return event


@app.get(
    "/events",
    response_model=list[TelemetryEventRecord],
)
def read_events(
    session: SessionDependency,
    credentials: BearerCredentials = None,
    source: str | None = None,
    classification: str | None = None,
    flagged: bool | None = None,
    offset: int = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[TelemetryEventRecord]:
    if classification is not None:
        verify_classification_access(classification, credentials)
    else:
        for protected_classification in PROTECTED_CLASSIFICATIONS:
            verify_classification_access(protected_classification, credentials)

    statement = select(TelemetryEventRecord)

    if source is not None:
        statement = statement.where(
            TelemetryEventRecord.source == source,
        )

    if classification is not None:
        statement = statement.where(
            TelemetryEventRecord.classification == classification,
        )

    if flagged is not None:
        statement = statement.where(
            TelemetryEventRecord.flagged == flagged,
        )

    statement = statement.offset(offset).limit(limit)

    return list(session.exec(statement).all())


@app.get(
    "/events/{event_id}",
    response_model=TelemetryEventRecord,
)
def read_event(
    event_id: int,
    session: SessionDependency,
    credentials: BearerCredentials = None,
) -> TelemetryEventRecord:
    event = find_event_or_404(event_id, session)

    verify_classification_access(event.classification, credentials)

    return event


@app.patch(
    "/events/{event_id}",
    response_model=TelemetryEventRecord,
)
def update_event(
    event_id: int,
    event_data: TelemetryEventUpdate,
    session: SessionDependency,
    credentials: BearerCredentials = None,
) -> TelemetryEventRecord:
    event = find_event_or_404(event_id, session)

    verify_classification_access(event.classification, credentials)

    updates = event_data.model_dump(exclude_unset=True)

    if "classification" in updates:
        verify_classification_access(updates["classification"], credentials)

    for field, value in updates.items():
        setattr(event, field, value)

    session.add(event)
    session.commit()
    session.refresh(event)

    logger.info(
        "Updated event id=%s",
        event.id,
    )

    log_if_top_secret(event)

    return event


@app.delete("/events/{event_id}")
def delete_event(
    event_id: int,
    session: SessionDependency,
    credentials: BearerCredentials = None,
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

    verify_classification_access(event.classification, credentials)

    session.delete(event)
    session.commit()

    logger.info(
        "Deleted event id=%s",
        event_id,
    )

    return {
        "message": "Event deleted successfully",
    }
