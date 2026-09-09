from telemetry_stream.collector import TelemetryCollector
from telemetry_stream.models import TelemetryEvent

event_1 = TelemetryEvent(
    "2026-08-24T12:00:00Z",
    "INFO",
    "sensor-1",
    "info",
    "System nominal",
    "startup",
    False,
)


event_2 = TelemetryEvent(
    timestamp="2026-08-26T09:05:00Z",
    event_type="command",
    source="server-1",
    classification="warning",
    message="Unexpected command detected",
    context="operating-system",
    flagged=True,
)

event_3 = TelemetryEvent(
    timestamp="2026-08-26T09:10:00Z",
    event_type="syscall",
    source="server-2",
    classification="critical",
    message="Restricted system call detected",
    context="security",
    flagged=True,
)


try:
    invalid_event = TelemetryEvent(
        "",
        "INFO",
        "sensor-1",
        "info",
        "System nominal",
        "startup",
        True,
    )
except ValueError as error:
    print(f"ValueError: {error}")


print("Program continued")


collector = TelemetryCollector()

collector.add_event(event_1)
collector.add_event(event_2)
collector.add_event(event_3)

print(f"Total events: {collector.event_count}")

flagged_events = collector.get_flagged_events()

print(f"Flagged events: {len(flagged_events)}")

for event in flagged_events:
    event.display()


for event in collector.events:
    event.display()
