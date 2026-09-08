sources: list[str] = [
    "sensor-1",
    "server-1",
    "server-2",
    "sensor-2",
]

print(f"First source: {sources[0]}")
print(f"Second source: {sources[1]}")
print(f"Last source: {sources[-1]}")

first_two_sources = sources[0:2]

print(f"First two sources: {first_two_sources}")
print(f"Middle sources: {sources[1:3]}")
print(f"From the third source: {sources[2:]}")


sources.append("server-3")
print(f"After adding: {sources}")

sources.remove("sensor-2")
print(f"After removing: {sources}")

sources[0] = "sensor-primary"
print(f"After changing: {sources}")


print("\nAll sources:")
for source in sources:
    print(source)


print("\nSources with indexes:")

for index, source in enumerate(sources):
    print(f"{index}: {source}")

classifications: tuple[str, ...] = (
    "info",
    "warning",
    "critical",
)

print("\nClassifications:")
print(classifications[0])
print(classifications[1])
print(classifications[-1])

# Access tuple items with indexes.
print(f"\nFirst classification: {classifications[0]}")
print(f"Last classification: {classifications[-1]}")

# Loop through the tuple.
print("\nAllowed classifications:")

for classification in classifications:
    print(classification)


print(f"Second source: {sources[1]}")

print(f"Last source: {sources[-1]}")
