"""Finds activities with similar titles in the backend.

Usage (from crawler/):  uv run python find_duplicates.py [threshold]   (default 0.8)

Compares every pair of activities by compacted title (same normalization as
app/services/dedup.py). Pairs >= 0.9 would be merged by the crawler's dedup;
lower ones are shown as near-matches. Also prints the distance between the
two locations (dedup only merges within 150 m).
"""

import math
import re
import sys
from difflib import SequenceMatcher

import httpx

BACKEND = "http://localhost:8080"
THRESHOLD = float(sys.argv[1]) if len(sys.argv) > 1 else 0.8


def compact(title: str) -> str:
    return re.sub(r"[^a-zäöüß]+", "", title.lower().replace("münster", ""))


def distance_m(a: dict, b: dict) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(h))


def main() -> None:
    activities = httpx.get(f"{BACKEND}/activities", timeout=30).json()
    pairs = []
    for i in range(len(activities)):
        for j in range(i + 1, len(activities)):
            a, b = activities[i], activities[j]
            ratio = SequenceMatcher(None, compact(a["title"]), compact(b["title"])).ratio()
            if ratio >= THRESHOLD or a["title"].lower() == b["title"].lower():
                pairs.append((ratio, a, b))
    pairs.sort(key=lambda p: p[0], reverse=True)

    print(f"{len(activities)} activities, {len(pairs)} pair(s) with similarity >= {THRESHOLD}\n")
    for ratio, a, b in pairs:
        dist = distance_m(a["location"], b["location"])
        mark = "WOULD-MERGE by crawler dedup" if ratio >= 0.9 else "near-match"
        print(f"[{ratio:.2f}] {mark}, {dist:.0f} m apart")
        for act in (a, b):
            print(f"  - {act['id'][:8]}  {act['title']}  ({act['location']['address']})")
        print()
    if not pairs:
        print("no similar-title pairs found")


if __name__ == "__main__":
    main()
