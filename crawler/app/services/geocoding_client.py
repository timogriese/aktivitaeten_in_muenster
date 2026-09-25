from __future__ import annotations

import asyncio
import time

import httpx

from app.core.config import settings

# City of Münster, generous bounding box. Geocoded points outside are rejected.
MUENSTER_BOUNDS = (51.84, 52.07, 7.47, 7.78)  # lat_min, lat_max, lon_min, lon_max
_TOO_VAGUE = {"city", "county", "state", "country"}


def in_muenster(lat: float, lon: float) -> bool:
    lat_min, lat_max, lon_min, lon_max = MUENSTER_BOUNDS
    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max


class GeocodingClient:
    """Address -> coordinates via Photon (komoot, OpenStreetMap data, no API key).

    Searches only inside the Münster bounding box. Requests are spaced ~1 s apart as a
    courtesy to the free public instance; results are cached per query.
    (Public Nominatim was tried first but rate-limits the hackathon network with 429s.)
    """

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = (base_url or settings.geocoding_url).rstrip("/")
        self._lock = asyncio.Lock()
        self._last_request = 0.0
        self._cache: dict[str, tuple[float, float] | None] = {}

    async def geocode(self, query: str) -> tuple[float, float] | None:
        key = query.strip().lower()
        if key in self._cache:
            return self._cache[key]

        lat_min, lat_max, lon_min, lon_max = MUENSTER_BOUNDS
        async with self._lock:
            wait = 1.0 - (time.monotonic() - self._last_request)
            if wait > 0:
                await asyncio.sleep(wait)
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(
                    f"{self._base_url}/api/",
                    params={
                        "q": query,
                        "limit": 1,
                        "lang": "de",
                        "bbox": f"{lon_min},{lat_min},{lon_max},{lat_max}",
                    },
                    headers={"User-Agent": settings.geocoding_user_agent},
                )
            self._last_request = time.monotonic()
        response.raise_for_status()

        features = response.json().get("features") or []
        coordinates = None
        # A hit that is just the city/region itself says nothing about where the activity is.
        if features and features[0]["properties"].get("type") not in _TOO_VAGUE:
            lon, lat = features[0]["geometry"]["coordinates"][:2]
            coordinates = (float(lat), float(lon))
        self._cache[key] = coordinates
        return coordinates
