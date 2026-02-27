"""
scam_detector.py – Heuristic and optional AI-based scam detection.

Risk levels:
  SAFE       – no red flags
  WARNING    – one or more soft signals
  HIGH RISK  – strong scam indicators
"""

import logging
from typing import Optional

from rental_hunter.config import (
    PRICE_PER_M2_ANOMALY_THRESHOLD,
    SCAM_KEYWORDS,
    OPENAI_API_KEY,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Heuristic detection
# ---------------------------------------------------------------------------

def _count_flags(listing: dict) -> int:
    """Count the number of scam signals in a listing dict."""
    flags = 0
    description = (listing.get("description") or "").lower()
    title = (listing.get("title") or "").lower()
    text = description + " " + title

    # 1. Price anomaly
    price: Optional[float] = listing.get("price")
    surface: Optional[float] = listing.get("surface")
    if price and surface and surface > 0:
        price_per_m2 = price / surface
        if price_per_m2 < PRICE_PER_M2_ANOMALY_THRESHOLD:
            flags += 2  # strong signal

    # 2. No photos
    if listing.get("image_count", 0) == 0:
        flags += 1

    # 3. Suspicious keywords
    for kw in SCAM_KEYWORDS:
        if kw.lower() in text:
            flags += 2
            break  # count once

    # 4. External contact only (no agency, phone not provided)
    if not listing.get("agency") and "whatsapp" in text:
        flags += 1

    # 5. Poor description (too short)
    if len(description) < 50:
        flags += 1

    # 6. No agency mention and private listing with very low price
    if not listing.get("agency") and price and price < 400:
        flags += 1

    return flags


def classify_risk_heuristic(listing: dict) -> str:
    flags = _count_flags(listing)
    if flags >= 4:
        return "HIGH RISK"
    if flags >= 2:
        return "WARNING"
    return "SAFE"


# ---------------------------------------------------------------------------
# Optional OpenAI classification
# ---------------------------------------------------------------------------

def classify_risk_ai(listing: dict) -> str:
    """
    Use OpenAI to classify risk.  Falls back to heuristic if API key is
    missing or the call fails.
    """
    if not OPENAI_API_KEY:
        return classify_risk_heuristic(listing)

    try:
        import openai  # type: ignore

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        prompt = (
            "You are a real-estate fraud expert. Classify the following French "
            "rental listing as SAFE, WARNING, or HIGH RISK based on potential "
            "scam indicators. Reply with exactly one of: SAFE, WARNING, HIGH RISK.\n\n"
            f"Title: {listing.get('title', '')}\n"
            f"Price: {listing.get('price', '')} €\n"
            f"Surface: {listing.get('surface', '')} m²\n"
            f"Description: {listing.get('description', '')[:500]}\n"
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0,
        )
        answer = response.choices[0].message.content.strip().upper()
        if answer in {"SAFE", "WARNING", "HIGH RISK"}:
            return answer
        return classify_risk_heuristic(listing)
    except Exception as exc:
        logger.warning("OpenAI scam detection failed: %s – falling back to heuristic", exc)
        return classify_risk_heuristic(listing)


def classify_risk(listing: dict) -> str:
    """Main entry point: use AI if available, else heuristic."""
    return classify_risk_ai(listing)
