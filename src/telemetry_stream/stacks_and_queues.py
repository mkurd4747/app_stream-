from collections import deque

from telemetry_stream.models import TelemetryEvent

event_1 = TelemetryEvent(
    timestamp="2026-09-02T09:00:00Z",
    event_type="ping",
    source="sensor-1",
    classification="info",
    message="System responded successfully",
    context="network",
    flagged=False,
)

event_2 = TelemetryEvent(
    timestamp="2026-09-02T09:05:00Z",
    event_type="login",
    source="server-1",
    classification="warning",
    message="Multiple failed login attempts",
    context="authentication",
    flagged=True,
)

event_3 = TelemetryEvent(
    timestamp="2026-09-02T09:10:00Z",
    event_type="syscall",
    source="server-2",
    classification="critical",
    message="Restricted system call detected",
    context="security",
    flagged=True,
)

event_stack: list[TelemetryEvent] = []

event_stack.append(event_1)
event_stack.append(event_2)
event_stack.append(event_3)

print(f"Events in stack: {len(event_stack)}")

print("\nProcessing stack:")

while event_stack:
    current_event = event_stack.pop()
    current_event.display()

print(f"Events remaining in stack: {len(event_stack)}")


# QUEUE: first in, first out (FIFO)

event_queue: deque[TelemetryEvent] = deque()

event_queue.append(event_1)
event_queue.append(event_2)
event_queue.append(event_3)

print(f"\nEvents in queue: {len(event_queue)}")

print("\nProcessing queue:")

while event_queue:
    current_event = event_queue.popleft()
    current_event.display()

print(f"Events remaining in queue: {len(event_queue)}")
