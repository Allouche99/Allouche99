"""
scrapers/base_scraper.py – Abstract base class for all rental scrapers.

Each concrete scraper must implement:
  - name: str  (display name)
  - search_url(max_price, min_surface, expand_radius): str
  - parse_listings(page_content: str) -> list[dict]

The base class handles:
  - Playwright browser management (headless + stealth)
  - Random delays to mimic human behaviour
  - Rotating user agents
  - robots.txt respect
"""

import asyncio
import logging
import random
import re
import urllib.parse
import urllib.robotparser
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
]


class BaseScraper(ABC):
    name: str = "base"

    # ---------------------------------------------------------------------------
    # Public interface
    # ---------------------------------------------------------------------------

    @abstractmethod
    def search_url(
        self,
        max_price: int = 1200,
        min_surface: int = 30,
        expand_radius: bool = False,
    ) -> str:
        """Return the URL to scrape for this run."""

    @abstractmethod
    def parse_listings(self, html: str) -> list[dict]:
        """Parse raw HTML and return a list of listing dicts."""

    async def fetch_listings(
        self,
        max_price: int = 1200,
        min_surface: int = 30,
        expand_radius: bool = False,
    ) -> list[dict]:
        """
        High-level method: fetch the page with Playwright and parse it.
        Returns an empty list if scraping fails or robots.txt disallows.
        """
        url = self.search_url(max_price, min_surface, expand_radius)

        if not self._robots_allowed(url):
            logger.info("[%s] robots.txt disallows %s – skipping.", self.name, url)
            return []

        html = await self._fetch_with_playwright(url)
        if not html:
            return []

        listings = self.parse_listings(html)
        logger.info("[%s] Found %d raw listings.", self.name, len(listings))
        return listings

    # ---------------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------------

    def _robots_allowed(self, url: str) -> bool:
        try:
            parsed = urllib.parse.urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch("*", url)
        except Exception:
            return True  # assume allowed if we can't read robots.txt

    async def _fetch_with_playwright(self, url: str) -> Optional[str]:
        try:
            from playwright.async_api import async_playwright  # type: ignore

            user_agent = random.choice(_USER_AGENTS)
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=user_agent,
                    locale="fr-FR",
                    timezone_id="Europe/Paris",
                    viewport={"width": 1366, "height": 768},
                )
                # Stealth: hide webdriver property
                await context.add_init_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )
                page = await context.new_page()
                await asyncio.sleep(random.uniform(1.0, 3.0))  # random pre-delay
                await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                await asyncio.sleep(random.uniform(2.0, 5.0))  # mimic reading
                html = await page.content()
                await browser.close()
                return html
        except Exception as exc:
            logger.error("[%s] Playwright fetch failed for %s: %s", self.name, url, exc)
            return None

    # ---------------------------------------------------------------------------
    # Shared parsing helpers
    # ---------------------------------------------------------------------------

    @staticmethod
    def _extract_price(text: str) -> Optional[float]:
        m = re.search(r"(\d[\d\s]*)\s*[€e]", text.replace("\xa0", " "))
        if m:
            return float(m.group(1).replace(" ", ""))
        return None

    @staticmethod
    def _extract_surface(text: str) -> Optional[float]:
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*m[²2]", text, re.IGNORECASE)
        if m:
            return float(m.group(1).replace(",", "."))
        return None

    @staticmethod
    def _extract_postal_code(text: str) -> str:
        m = re.search(r"\b(7[5-9]\d{3}|9[0-5]\d{3})\b", text)
        return m.group(1) if m else ""
