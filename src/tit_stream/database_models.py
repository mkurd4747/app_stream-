from sqlmodel import Field, SQLModel


class TelemetryEventRecord(SQLModel, table=True):
    __tablename__ = "telemetry_events"

    id: int | None = Field(default=None, primary_key=True)
    timestamp: str = Field(index=True)
    event_type: str
    source: str = Field(index=True)
    classification: str = Field(index=True)
    message: str
    context: str
    flagged: bool = Field(default=False, index=True)
