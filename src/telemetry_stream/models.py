class TelemetryEvent:
    def __init__(
        self,
        timestamp: str,
        event_type: str,
        source: str,
        classification: str,
        message: str,
        context: str,
        flagged: bool,
    ) -> None:
        if not timestamp.strip():
            raise ValueError("Timestamp cannot be empty")

        if not event_type.strip():
            raise ValueError("Event type cannot be empty")

        if not source.strip():
            raise ValueError("Source cannot be empty")

        allowed_classifications = {"info", "warning", "critical"}

        if classification not in allowed_classifications:
            raise ValueError("Classification must be info, warning, or critical")

        self.timestamp = timestamp
        self.event_type = event_type
        self.source = source
        self.classification = classification
        self.message = message
        self.context = context
        self.flagged = flagged

    def display(self) -> None:
        print(
            f"[{self.timestamp}] "
            f"{self.event_type.upper()} "
            f"({self.classification}) "
            f"from {self.source}: {self.message}"
        )
