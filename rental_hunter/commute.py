"""
commute.py – Optional Google Maps commute time calculation.
Returns None when the API key is not configured, so the rest of the
system degrades gracefully.
"""

import logging
from typing import Optional

from rental_hunter.config import GOOGLE_MAPS_API_KEY, COMMUTE_DESTINATIONS

logger = logging.getLogger(__name__)

_gmaps_client = None


def _get_client():
    global _gmaps_client
    if _gmaps_client is None and GOOGLE_MAPS_API_KEY:
        try:
            import googlemaps  # type: ignore

            _gmaps_client = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        except ImportError:
            logger.warning("googlemaps package not installed; commute scoring disabled.")
    return _gmaps_client


def get_min_commute_minutes(origin_address: str) -> Optional[float]:
    """
    Return the minimum commute time (in minutes, transit mode) from
    *origin_address* to any of the configured COMMUTE_DESTINATIONS.
    Returns None if the Google Maps API is unavailable.
    """
    client = _get_client()
    if client is None:
        return None

    min_minutes: Optional[float] = None
    for dest in COMMUTE_DESTINATIONS:
        try:
            result = client.distance_matrix(
                origins=[origin_address],
                destinations=[dest],
                mode="transit",
                language="fr",
            )
            element = result["rows"][0]["elements"][0]
            if element["status"] == "OK":
                duration_sec: float = element["duration"]["value"]
                minutes = duration_sec / 60
                if min_minutes is None or minutes < min_minutes:
                    min_minutes = minutes
        except Exception as exc:
            logger.warning("Google Maps API error for %s → %s: %s", origin_address, dest, exc)

    return min_minutes
