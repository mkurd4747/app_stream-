from tit_stream.collector import TelemetryCollector
from tit_stream.models import TelemetryEvent


def create_sample_collector() -> TelemetryCollector:
    collector = TelemetryCollector()

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
        source="server-1",
        classification="critical",
        message="Restricted system call detected",
        context="security",
        flagged=True,
    )

    collector.add_event(event_1)
    collector.add_event(event_2)
    collector.add_event(event_3)

    return collector


def test_event_count() -> None:
    collector = create_sample_collector()

    assert collector.event_count == 3


def test_get_events_by_source() -> None:
    collector = create_sample_collector()

    results = collector.get_events_by_source("server-1")

    assert len(results) == 2
    assert results[0].source == "server-1"
    assert results[1].source == "server-1"


def test_get_events_by_source_with_no_match() -> None:
    collector = create_sample_collector()

    results = collector.get_events_by_source("unknown-server")

    assert results == []


def test_sort_events_by_timestamp() -> None:
    collector = create_sample_collector()

    sorted_events = collector.get_events_sorted_by_timestamp()

    assert sorted_events[0].timestamp == "2026-09-02T09:05:00Z"
    assert sorted_events[1].timestamp == "2026-09-02T09:15:00Z"
    assert sorted_events[2].timestamp == "2026-09-02T09:25:00Z"


def test_sort_does_not_change_original_list() -> None:
    collector = create_sample_collector()

    original_first_event = collector.events[0]

    collector.get_events_sorted_by_timestamp()

    assert collector.events[0] is original_first_event


def test_count_by_classification() -> None:
    collector = create_sample_collector()

    counts = collector.count_by_classification()

    assert counts == {
        "warning": 1,
        "info": 1,
        "critical": 1,
    }


def test_get_unique_sources() -> None:
    collector = create_sample_collector()

    sources = collector.get_unique_sources()

    assert sources == {
        "server-1",
        "sensor-1",
    }
