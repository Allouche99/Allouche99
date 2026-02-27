"""
smart_mode.py – Adaptive listing management.

- If fewer than SMART_MODE_MIN_LISTINGS found: expand_radius = True on next cycle.
- If more than SMART_MODE_MAX_LISTINGS: rank and keep best N.
"""

from rental_hunter.config import SMART_MODE_MIN_LISTINGS, SMART_MODE_MAX_LISTINGS


def should_expand_radius(listing_count: int) -> bool:
    """Return True if the agent should expand its search radius."""
    return listing_count < SMART_MODE_MIN_LISTINGS


def apply_smart_cap(listings: list[dict]) -> list[dict]:
    """
    If there are more listings than the cap, keep only the top-N by total_score.
    """
    if len(listings) <= SMART_MODE_MAX_LISTINGS:
        return listings
    ranked = sorted(listings, key=lambda x: x.get("total_score", 0), reverse=True)
    return ranked[:SMART_MODE_MAX_LISTINGS]
