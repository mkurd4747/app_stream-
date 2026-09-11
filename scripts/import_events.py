"""Import telemetry events from a file on disk into a running telemetry-stream-api.

Reads rows from a CSV or JSON file, validates each one against the same
TelemetryEventCreate schema the API itself uses, then POSTs it to /events
over real HTTP -- same flow as a person pasting requests into /docs, just
driven from a file instead of by hand.

CSV columns (JSON: same keys, one object per array element):
    timestamp, event_type, source, classification, message, context,
    flagged, object_id, latitude, longitude, altitude_m, grid, confidence

Only timestamp, event_type, source, classification, message, context are
required; the rest may be left blank/omitted. classification must be one of
UNCLASSIFIED, CONFIDENTIAL, SECRET, TOP_SECRET.

Usage:
    python scripts/import_events.py --file data/events.csv
    python scripts/import_events.py --file data/events.json --base-url http://127.0.0.1:8123

Reads client credentials from TELEMETRY_STREAM_OAUTH_CLIENT_ID /
TELEMETRY_STREAM_OAUTH_CLIENT_SECRET (same names the app itself uses),
or pass --client-id/--client-secret explicitly. The client must have the
"create" permission (the default admin client does).
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from telemetry_stream.schemas import TelemetryEventCreate  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

OPTIONAL_NUMERIC_FIELDS = {"latitude", "longitude", "altitude_m", "confidence"}


def load_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON file must contain a list of event objects")
        return data

    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            return [clean_csv_row(row) for row in csv.DictReader(handle)]

    raise ValueError(f"Unsupported file type: {path.suffix} (use .csv or .json)")


def clean_csv_row(row: dict[str, str]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}

    for key, value in row.items():
        if value is None or value == "":
            continue

        if key == "flagged":
            cleaned[key] = value.strip().lower() in {"1", "true", "yes"}
        elif key in OPTIONAL_NUMERIC_FIELDS:
            cleaned[key] = float(value)
        else:
            cleaned[key] = value

    return cleaned


def import_events(
    base_url: str,
    client_id: str,
    client_secret: str,
    rows: list[dict[str, Any]],
) -> int:
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        token_response = client.post(
            "/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )

        if token_response.status_code != 200:
            print(
                f"error: could not get access token (status={token_response.status_code}): "
                f"{token_response.text}",
                file=sys.stderr,
            )
            return 1

        auth_headers = {
            "Authorization": f"Bearer {token_response.json()['access_token']}",
        }

        failures = 0

        for index, row in enumerate(rows, start=1):
            try:
                event = TelemetryEventCreate(**row)
            except ValidationError as error:
                print(f"  [SKIP] row {index}: {error}")
                failures += 1
                continue

            response = client.post(
                "/events",
                headers=auth_headers,
                json=event.model_dump(exclude_unset=True),
            )

            if response.status_code == 201:
                print(f"  [OK]   row {index}: created event id={response.json()['id']}")
            else:
                print(f"  [FAIL] row {index}: status={response.status_code} {response.text}")
                failures += 1

    total = len(rows)
    print(f"\n{total - failures} of {total} events imported")

    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, type=Path, help="Path to a .csv or .json file")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("IMPORT_EVENTS_BASE_URL", "http://127.0.0.1:8000"),
    )
    parser.add_argument(
        "--client-id",
        default=os.environ.get("TELEMETRY_STREAM_OAUTH_CLIENT_ID"),
    )
    parser.add_argument(
        "--client-secret",
        default=os.environ.get("TELEMETRY_STREAM_OAUTH_CLIENT_SECRET"),
    )
    args = parser.parse_args()

    if not args.client_id or not args.client_secret:
        print(
            "error: client-id/client-secret required "
            "(set TELEMETRY_STREAM_OAUTH_CLIENT_ID / "
            "TELEMETRY_STREAM_OAUTH_CLIENT_SECRET or pass --client-id/--client-secret)",
            file=sys.stderr,
        )
        return 2

    if not args.file.exists():
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 2

    rows = load_rows(args.file)
    print(f"Importing {len(rows)} event(s) from {args.file} into {args.base_url}\n")

    try:
        return import_events(args.base_url, args.client_id, args.client_secret, rows)
    except httpx.ConnectError as error:
        print(f"error: could not connect to {args.base_url}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
