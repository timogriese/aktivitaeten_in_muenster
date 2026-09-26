"""Bulk import: runs crawl cycles until the backend holds TARGET activities.

Usage (from crawler/):  uv run python bulk_import.py [target] [max_cycles]
Defaults: target=600, max_cycles=400.

Each cycle costs 5 Tavily credits. One progress line per cycle is appended to
bulk-progress.log. Stops early when the target is reached, max cycles is hit,
or Tavily signals quota exhaustion.
"""

import sys
import time
from datetime import datetime, UTC

import httpx

CRAWLER = "http://localhost:8000"
BACKEND = "http://localhost:8080"
TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 600
MAX_CYCLES = int(sys.argv[2]) if len(sys.argv) > 2 else 400
LOG_FILE = "bulk-progress.log"


def backend_count() -> int:
    response = httpx.get(f"{BACKEND}/activities", timeout=30)
    response.raise_for_status()
    return len(response.json())


def log(message: str) -> None:
    line = f"{datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} {message}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(line + "\n")


def main() -> None:
    fail_streak = 0
    for cycle in range(1, MAX_CYCLES + 1):
        total = backend_count()
        if total >= TARGET:
            log(f"DONE: target reached - backend has {total} activities after {cycle - 1} cycles")
            return
        try:
            response = httpx.post(f"{CRAWLER}/crawl", timeout=900)
        except httpx.HTTPError as error:
            log(f"cycle {cycle}: request error: {error} - retrying in 30 s")
            time.sleep(30)
            continue
        if response.status_code != 200:
            body = response.text[:300]
            if any(word in body.lower() for word in ("credit", "quota", "insufficient")):
                log(f"cycle {cycle}: Tavily quota exhausted (HTTP {response.status_code}) - stopping")
                return
            fail_streak += 1
            log(f"cycle {cycle}: HTTP {response.status_code}: {body}")
            if fail_streak >= 3:
                log(f"stopping after {fail_streak} consecutive crawl failures")
                return
            time.sleep(30)
            continue
        fail_streak = 0
        data = response.json()
        total = backend_count()
        remaining = max(0, TARGET - total)
        log(
            f"cycle {cycle}/{MAX_CYCLES}: found={data.get('found')} "
            f"created={data.get('created')} updated={data.get('updated')} rejected={data.get('rejected')}"
            f" | backend total={total} ({remaining} to go)"
        )
    log(f"max cycles ({MAX_CYCLES}) reached - backend has {backend_count()} activities")


if __name__ == "__main__":
    main()
