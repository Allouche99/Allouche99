"""
scrapers/agency.py – Scraper for public real estate agency websites
in departments 94, 93, and Paris.

Rather than hard-coding individual agencies (which change frequently),
this scraper targets publicly known agency portals via their search pages.
"""

import asyncio
import logging
from typing import Optional

from bs4 import BeautifulSoup

from rental_hunter.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# List of public agency search URLs; extend as needed
_AGENCY_SEARCH_URLS = [
    # Century 21
    "https://www.century21.fr/annonces/f/location-appartement/d-94/",
    # Orpi
    "https://www.orpi.com/recherche/rent/apartment/?localisation=94&maxPrice=1200",
    # Guy Hoquet
    "https://www.guy-hoquet.com/biens/result#filters[type_transactions][]=LOCATION"
    "&filters[type_biens][]=APPARTEMENT&filters[localites][]=94",
    # Foncia
    "https://fr.foncia.com/location/appartement/ile-de-france?loyer_max=1200",
]


class AgencyScraper(BaseScraper):
    name = "Agency"

    def search_url(
        self,
        max_price: int = 1200,
        min_surface: int = 30,
        expand_radius: bool = False,
    ) -> str:
        # Return the first agency URL; the overridden fetch_listings handles all
        return _AGENCY_SEARCH_URLS[0]

    async def fetch_listings(
        self,
        max_price: int = 1200,
        min_surface: int = 30,
        expand_radius: bool = False,
    ) -> list[dict]:
        """Fetch from all agency URLs and aggregate results."""
        all_results: list[dict] = []
        for url in _AGENCY_SEARCH_URLS:
            if not self._robots_allowed(url):
                logger.info("[%s] robots.txt disallows %s – skipping.", self.name, url)
                continue
            html = await self._fetch_with_playwright(url)
            if html:
                listings = self.parse_listings(html)
                # Tag with source agency domain and fix relative URLs
                from urllib.parse import urlparse, urljoin
                domain = urlparse(url).netloc.replace("www.", "")
                for lst in listings:
                    if not lst.get("agency"):
                        lst["agency"] = domain
                    href = lst.get("url", "")
                    if href and not href.startswith("http"):
                        lst["url"] = urljoin(url, href)
                all_results.extend(listings)
        logger.info("[%s] Total agency listings: %d", self.name, len(all_results))
        return all_results

    def parse_listings(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        results = []

        # Generic selectors that cover multiple agency site structures
        for card in soup.select(
            "article.property-card, div.bien-item, li.result-item, "
            "div[class*='property'], div[class*='listing']"
        ):
            try:
                title_el = card.select_one(
                    "h2, h3, .property-title, [class*='title']"
                )
                url_el = card.select_one("a[href]")
                price_el = card.select_one(
                    ".property-price, .price, [class*='price'], [class*='loyer']"
                )
                surface_el = card.select_one(
                    ".property-surface, [class*='surface'], [class*='area']"
                )
                city_el = card.select_one(
                    ".property-city, .city, [class*='city'], [class*='location']"
                )
                desc_el = card.select_one("[class*='description'], [class*='desc']")
                imgs = card.select("img[src]")
                agency_el = card.select_one("[class*='agency'], [class*='agence']")

                title = title_el.get_text(strip=True) if title_el else ""
                href = url_el["href"] if url_el else ""
                price_text = price_el.get_text(strip=True) if price_el else ""
                surface_text = surface_el.get_text(strip=True) if surface_el else ""
                city_text = city_el.get_text(strip=True) if city_el else ""
                description = desc_el.get_text(strip=True) if desc_el else ""
                agency = agency_el.get_text(strip=True) if agency_el else ""

                if href and not href.startswith("http"):
                    # We don't know which agency site this came from here,
                    # so relative URLs are left as-is; fetch_listings sets the correct domain.
                    pass

                price = self._extract_price(price_text)
                surface = self._extract_surface(surface_text + " " + title)
                postal_code = self._extract_postal_code(city_text)

                if not title or not href:
                    continue

                results.append(
                    {
                        "source": self.name,
                        "url": href,
                        "title": title,
                        "price": price,
                        "surface": surface,
                        "city": city_text,
                        "postal_code": postal_code,
                        "description": description,
                        "image_count": len(imgs),
                        "furnished": "meublé" in (title + description).lower(),
                        "agency": agency,
                    }
                )
            except Exception:
                continue

        return results
