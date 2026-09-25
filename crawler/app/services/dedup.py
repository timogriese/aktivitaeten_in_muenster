from __future__ import annotations

import math
import re
from difflib import SequenceMatcher

from app.models.activity import ActivityCreate, Location

_MAX_DISTANCE_M = 150
# Deliberately strict: merging two different offers overwrites one of them, which is worse
# than keeping a duplicate. "Malkurs im Kreativ-Haus" vs. "Töpferkurs im Kreativ-Haus" is ~0.8.
_MIN_SIMILARITY = 0.9


def align_to_existing(activity: ActivityCreate, known: list[tuple[str, Location]]) -> ActivityCreate:
    """Returns `activity` with the title of a near-duplicate from `known`, if there is one.

    The backend dedups by exact title only; reusing the existing title turns a second entry
    for the same place ("Aasee" vs. "Aasee Münster", "Kreativhaus" vs. "Kreativ-Haus") into
    an update of the first.
    """
    title = _compact(activity.title)
    for known_title, location in known:
        if _distance_m(activity.location, location) > _MAX_DISTANCE_M:
            continue
        other = _compact(known_title)
        if other == title:
            return activity if known_title == activity.title else activity.model_copy(update={"title": known_title})
        if SequenceMatcher(None, title, other).ratio() >= _MIN_SIMILARITY:
            return activity.model_copy(update={"title": known_title})
    return activity


def _compact(title: str) -> str:
    """Lower-case letters only, without the ubiquitous "Münster"."""
    return re.sub(r"[^a-zäöüß]+", "", title.lower().replace("münster", ""))


def _distance_m(a: Location, b: Location) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a.lat, a.lon, b.lat, b.lon))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(h))
