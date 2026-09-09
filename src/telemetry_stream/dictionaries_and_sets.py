# #  Day 2: Dictionaries and sets

event: dict[str, str] = {
    "timestamp": "2026-09-02T09:00:00Z",
    "event_type": "login",
    "source": "server_1",
    "classification": "warning",
    "message": "Multiplie failed login attempts",
    "context": "authentication",
}


# # Access dictionary values by their keys.

print(f"Source: {event['source']}")
print(f"Classification: {event['classification']}")
print(f"Message: {event['message']}")


# Add a new key-value pair.
event["status"] = "under review"
print(f"Status: {event['status']}")

# Change an existing value.
event["classification"] = "critical"
print(f"reqUpdated classification: {event['classification']}")

# Loop through all dictionary keys and values.
print("\nComplete event:")

for key, value in event.items():
    print(f"{key}: {value}")

# A list containing the classifications of multiple events.
classifications: list[str] = [
    "info",
    "warning",
    "critical",
    "warning",
    "info",
    "warning",
]

# Count how many times each classification appears.
classification_counts: dict[str, int] = {}

for classification in classifications:
    classification_counts[classification] = classification_counts.get(classification, 0) + 1

print("\nClassification counts:")

for classification, count in classification_counts.items():
    print(f"{classification}: {count}")

# A list may contain duplicate values.
sources: list[str] = [
    "sensor-1",
    "server-1",
    "server-2",
    "sensor-1",
    "server-1",
]

print(f"\nSources with duplicates: {sources}")

# A set stores unique values, so duplicates are removed.
unique_sources: set[str] = set(sources)

print(f"Unique sources: {unique_sources}")

# Add a value to the set.
unique_sources.add("sensor-2")

# Adding an existing value does not create a duplicate.
unique_sources.add("server-1")

# Remove a value safely.
unique_sources.discard("server-2")

print("\nUpdated unique sources:")

for source in sorted(unique_sources):
    print(source)
