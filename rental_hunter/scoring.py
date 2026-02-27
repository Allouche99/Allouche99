"""
scoring.py – Geographic and transport scoring engine.

Geographic scores (cumulative):
  +4  city in 94 (Val-de-Marne)
  +3  city in Paris (75)
  +2  city in 93 close to 94
  +1  < 45 min commute (set externally)
  +0  otherwise

Transport scores:
  +3  RER nearby
  +2  Metro nearby
  +1  Bus nearby
  +2  commute < 30 min
  +1  commute < 45 min
"""

import re
from typing import Optional

from rental_hunter.config import GEO_SCORES, CITIES_93_NEAR_94


# ---------------------------------------------------------------------------
# Geographic scoring
# ---------------------------------------------------------------------------

def get_geo_score(postal_code: str, city: str) -> int:
    """
    Return a geographic priority score for a listing location.
    postal_code: string like '94100', '75011', '93200'
    city:        normalised city name (lower-case)
    """
    prefix = (postal_code or "").strip()[:2]
    city_norm = (city or "").lower().strip()

    if prefix == "94":
        return GEO_SCORES["94"]  # +4

    if prefix == "75":
        return GEO_SCORES["75"]  # +3

    if prefix == "93":
        # Extra check: is it a 93 city that borders 94?
        for known in CITIES_93_NEAR_94:
            if known in city_norm:
                return GEO_SCORES["93"]  # +2
        return GEO_SCORES["93"]  # still +2 for all 93

    return 0


# ---------------------------------------------------------------------------
# Transport scoring
# ---------------------------------------------------------------------------

_RER_PATTERN = re.compile(r"\bRER\s*[ABCDE]\b", re.IGNORECASE)
_METRO_PATTERN = re.compile(r"\b(métro|metro)\b", re.IGNORECASE)
_BUS_PATTERN = re.compile(r"\bbus\b", re.IGNORECASE)


def get_transport_score(
    description: str,
    commute_minutes: Optional[float] = None,
) -> int:
    """
    Return a transport-quality score based on description text and optional
    commute time in minutes.
    """
    score = 0
    text = description or ""

    if _RER_PATTERN.search(text):
        score += 3
    if _METRO_PATTERN.search(text):
        score += 2
    if _BUS_PATTERN.search(text):
        score += 1

    if commute_minutes is not None:
        if commute_minutes < 30:
            score += 2
        elif commute_minutes < 45:
            score += 1

    return score


# ---------------------------------------------------------------------------
# Combined score
# ---------------------------------------------------------------------------

def compute_total_score(
    price: Optional[float],
    surface: Optional[float],
    furnished: bool,
    geo_score: int,
    transport_score: int,
    commute_minutes: Optional[float] = None,
) -> float:
    """
    Combine all signals into a single comparable score.
    Higher is better.
    """
    total: float = geo_score + transport_score

    # Commute bonus already included in transport_score; add geo commute bonus
    if commute_minutes is not None and commute_minutes < 45:
        total += 1  # geo score +1 for < 45 min

    # Slight bonus for unfurnished
    if not furnished:
        total += 0.5

    return total
