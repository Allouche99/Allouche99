"""
main.py – Rental Hunter orchestrator and scheduler.

Run:
    python main.py

The agent scrapes all configured sources every EMAIL_INTERVAL_HOURS hours,
scores listings, detects scams, persists new ones to SQLite, and sends an
HTML digest email.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone

import schedule

from rental_hunter.config import (
    EMAIL_INTERVAL_HOURS,
    MAX_PRICE_EUR,
    MIN_SURFACE_M2,
    SMART_MODE_MAX_LISTINGS,
)
from rental_hunter.database import init_db, init_sent_table, save_listing, get_unsent_listings, mark_sent
from rental_hunter.email_sender import send_digest
from rental_hunter.scoring import get_geo_score, get_transport_score, compute_total_score
from rental_hunter.scam_detector import classify_risk
from rental_hunter.commute import get_min_commute_minutes
from rental_hunter.smart_mode import should_expand_radius, apply_smart_cap
from rental_hunter.scrapers import ALL_SCRAPERS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rental_hunter.main")

# Track whether the previous cycle had few results
_expand_radius: bool = False


async def _run_scrapers(expand_radius: bool) -> list[dict]:
    """Run all scrapers concurrently and return combined raw listings."""
    tasks = [
        scraper_cls().fetch_listings(
            max_price=MAX_PRICE_EUR,
            min_surface=MIN_SURFACE_M2,
            expand_radius=expand_radius,
        )
        for scraper_cls in ALL_SCRAPERS
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    combined: list[dict] = []
    for r in results:
        if isinstance(r, list):
            combined.extend(r)
        else:
            logger.error("Scraper raised: %s", r)
    return combined


def _enrich_listing(listing: dict) -> dict:
    """Add geo score, transport score, total score, and risk level."""
    geo = get_geo_score(
        listing.get("postal_code", ""),
        listing.get("city", ""),
    )

    # Optionally compute commute time
    city = listing.get("city", "")
    postal = listing.get("postal_code", "")
    address = f"{city} {postal}".strip()
    commute_minutes = get_min_commute_minutes(address) if address else None

    transport = get_transport_score(
        listing.get("description", ""),
        commute_minutes,
    )

    total = compute_total_score(
        price=listing.get("price"),
        surface=listing.get("surface"),
        furnished=bool(listing.get("furnished")),
        geo_score=geo,
        transport_score=transport,
        commute_minutes=commute_minutes,
    )

    risk = classify_risk(listing)

    listing.update(
        geo_score=geo,
        transport_score=transport,
        total_score=total,
        risk_level=risk,
        detected_at=listing.get("detected_at") or datetime.now(timezone.utc).isoformat(),
    )
    return listing


def run_cycle() -> None:
    """One full scrape → enrich → persist → email cycle."""
    global _expand_radius

    logger.info("=== Starting scrape cycle (expand_radius=%s) ===", _expand_radius)

    raw = asyncio.run(_run_scrapers(expand_radius=_expand_radius))
    logger.info("Total raw listings collected: %d", len(raw))

    # Smart mode: decide next radius
    _expand_radius = should_expand_radius(len(raw))

    # Enrich and persist
    new_listings: list[dict] = []
    for listing in raw:
        listing = _enrich_listing(listing)
        if save_listing(listing):
            new_listings.append(listing)

    logger.info("New (unique) listings persisted: %d", len(new_listings))

    # Smart cap for email
    to_send = apply_smart_cap(new_listings)

    if to_send:
        send_digest(to_send)
        # Mark exactly the listings that were emailed as sent
        sent_ids = [lst["id"] for lst in to_send if lst.get("id")]
        if sent_ids:
            mark_sent(sent_ids)

    logger.info("=== Cycle complete ===")


def main() -> None:
    # Initialise database
    init_db()
    init_sent_table()

    # Run once immediately at startup
    run_cycle()

    # Schedule recurring cycles
    schedule.every(EMAIL_INTERVAL_HOURS).hours.do(run_cycle)

    logger.info(
        "Scheduler active – running every %d hour(s). Press Ctrl+C to stop.",
        EMAIL_INTERVAL_HOURS,
    )
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
