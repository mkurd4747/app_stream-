import json
from pathlib import Path
from typing import Any

from telemetry_stream.models import TelemetryEvent


class TelemetryCollector:
    def __init__(self) -> None:
        self.events: list[TelemetryEvent] = []

    def add_event(self, event: TelemetryEvent) -> None:
        self.events.append(event)

    @property
    def event_count(self) -> int:
        return len(self.events)

    def get_flagged_events(self) -> list[TelemetryEvent]:
        return [event for event in self.events if event.flagged]

    def get_events_by_source(
        self,
        source: str,
    ) -> list[TelemetryEvent]:
        return [event for event in self.events if event.source == source]

    def get_events_sorted_by_timestamp(
        self,
    ) -> list[TelemetryEvent]:
        return sorted(
            self.events,
            key=lambda event: event.timestamp,
        )

    def count_by_classification(self) -> dict[str, int]:
        counts: dict[str, int] = {}

        for event in self.events:
            counts[event.classification] = counts.get(event.classification, 0) + 1

        return counts

    def get_unique_sources(self) -> set[str]:
        return {event.source for event in self.events}

    def save_to_json(self, path: Path) -> None:
        event_dictionaries = [
            {
                "timestamp": event.timestamp,
                "event_type": event.event_type,
                "source": event.source,
                "classification": event.classification,
                "message": event.message,
                "context": event.context,
                "flagged": event.flagged,
            }
            for event in self.events
        ]

        with path.open("w", encoding="utf-8") as file:
            json.dump(event_dictionaries, file, indent=4)

    def load_from_json(self, path: Path) -> None:
        with path.open("r", encoding="utf-8") as file:
            records: list[dict[str, Any]] = json.load(file)

        for record in records:
            event = TelemetryEvent(**record)
            self.add_event(event)
