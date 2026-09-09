from telemetry_stream.models import TelemetryEvent

event_1 = TelemetryEvent(
    timestamp="2026-09-02T09:15:00Z",
    event_type="login",
    source="server-1",
    classification="warning",
    message="Multiple failed login attempts",
    context="authentication",
    flagged=True,
)

event_2 = TelemetryEvent(
    timestamp="2026-09-02T09:05:00Z",
    event_type="ping",
    source="sensor-1",
    classification="info",
    message="System responded successfully",
    context="network",
    flagged=False,
)

event_3 = TelemetryEvent(
    timestamp="2026-09-02T09:25:00Z",
    event_type="syscall",
    source="server-2",
    classification="critical",
    message="Restricted system call detected",
    context="security",
    flagged=True,
)

event_4 = TelemetryEvent(
    timestamp="2026-09-02T09:20:00Z",
    event_type="logout",
    source="server-1",
    classification="info",
    message="User logged out",
    context="authentication",
    flagged=False,
)


events: list[TelemetryEvent] = [
    event_1,
    event_2,
    event_3,
    event_4,
]


def find_events_by_source(
    event_list: list[TelemetryEvent],
    source: str,
) -> list[TelemetryEvent]:
    matching_events: list[TelemetryEvent] = []

    for event in event_list:
        if event.source == source:
            matching_events.append(event)

    return matching_events


print("Events from server-1:")

server_events = find_events_by_source(events, "server-1")

for event in server_events:
    event.display()


print("\nEvents sorted by timestamp:")

events_by_timestamp = sorted(
    events,
    key=lambda event: event.timestamp,
)

for event in events_by_timestamp:
    event.display()


print("\nEvents sorted by source:")

events_by_source = sorted(
    events,
    key=lambda event: event.source,
)

for event in events_by_source:
    event.display()


print("\nEvents sorted from newest to oldest:")

newest_first = sorted(
    events,
    key=lambda event: event.timestamp,
    reverse=True,
)

for event in newest_first:
    event.display()
