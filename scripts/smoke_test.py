"""End-to-end smoke test against a running telemetry-stream-api instance.

Exercises the same flow a person would walk through manually in /docs:
get a token, use it to create/list events, and confirm auth and validation
are actually enforced. Runs over real HTTP against a live server -- it does
not import the app or spin one up itself.

Usage:
    python scripts/smoke_test.py [--base-url http://127.0.0.1:8000]

Reads client credentials from TELEMETRY_STREAM_OAUTH_CLIENT_ID /
TELEMETRY_STREAM_OAUTH_CLIENT_SECRET (same names the app itself uses),
or pass --client-id/--client-secret explicitly.

Exits non-zero if any check fails, so it can be run in CI or a deploy
pipeline as a post-deploy gate, not just by hand.
"""

import argparse
import os
import sys
from dataclasses import dataclass

import httpx


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


def run_checks(base_url: str, client_id: str, client_secret: str) -> list[CheckResult]:
    results: list[CheckResult] = []

    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        health_response = client.get("/health")
        results.append(
            CheckResult(
                "GET /health",
                health_response.status_code == 200,
                f"status={health_response.status_code}",
            )
        )

        ready_response = client.get("/ready")
        results.append(
            CheckResult(
                "GET /ready",
                ready_response.status_code == 200,
                f"status={ready_response.status_code}",
            )
        )

        no_token_response = client.post(
            "/events",
            json={
                "timestamp": "2026-01-01T00:00:00Z",
                "event_type": "smoke-test",
                "source": "smoke_test.py",
                "classification": "info",
                "message": "should be rejected, no token",
                "context": "smoke-test",
            },
        )
        results.append(
            CheckResult(
                "POST /events without token is rejected",
                no_token_response.status_code == 401,
                f"status={no_token_response.status_code}",
            )
        )

        token_response = client.post(
            "/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        token_ok = token_response.status_code == 200
        results.append(
            CheckResult(
                "POST /oauth/token issues a token",
                token_ok,
                f"status={token_response.status_code}",
            )
        )

        if not token_ok:
            return results

        access_token = token_response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        create_response = client.post(
            "/events",
            headers=auth_headers,
            json={
                "timestamp": "2026-01-01T00:00:00Z",
                "event_type": "smoke-test",
                "source": "smoke_test.py",
                "classification": "info",
                "message": "created by the smoke test",
                "context": "smoke-test",
                "confidence": 0.75,
            },
        )
        results.append(
            CheckResult(
                "POST /events with token succeeds",
                create_response.status_code == 201,
                f"status={create_response.status_code}",
            )
        )

        invalid_response = client.post(
            "/events",
            headers=auth_headers,
            json={
                "timestamp": "2026-01-01T00:00:00Z",
                "event_type": "smoke-test",
                "source": "smoke_test.py",
                "classification": "info",
                "message": "should be rejected, bad confidence",
                "context": "smoke-test",
                "confidence": 1.5,
            },
        )
        results.append(
            CheckResult(
                "POST /events rejects out-of-range confidence",
                invalid_response.status_code == 422,
                f"status={invalid_response.status_code}",
            )
        )

        list_response = client.get("/events", headers=auth_headers)
        results.append(
            CheckResult(
                "GET /events with token succeeds",
                list_response.status_code == 200,
                f"status={list_response.status_code}",
            )
        )

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.environ.get("SMOKE_TEST_BASE_URL", "http://127.0.0.1:8000"),
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

    print(f"Running smoke test against {args.base_url}\n")

    try:
        results = run_checks(args.base_url, args.client_id, args.client_secret)
    except httpx.ConnectError as error:
        print(f"error: could not connect to {args.base_url}: {error}", file=sys.stderr)
        return 2

    failures = 0
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"  [{status}] {result.name} ({result.detail})")
        if not result.passed:
            failures += 1

    print()
    if failures:
        print(f"{failures} of {len(results)} checks failed")
        return 1

    print(f"All {len(results)} checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
