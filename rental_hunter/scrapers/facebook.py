"""
scrapers/facebook.py – Facebook Marketplace public rental scraper.
Only scrapes publicly visible listings (no login required).
"""

from bs4 import BeautifulSoup

from rental_hunter.scrapers.base_scraper import BaseScraper


class FacebookScraper(BaseScraper):
    name = "Facebook Marketplace"

    def search_url(
        self,
        max_price: int = 1200,
        min_surface: int = 30,
        expand_radius: bool = False,
    ) -> str:
        # Facebook Marketplace public search for property rentals near Paris
        radius_km = 60 if expand_radius else 30
        return (
            f"https://www.facebook.com/marketplace/paris/propertyrentals"
            f"?maxPrice={max_price}"
            f"&radius={radius_km}"
            f"&propertyType=apartment"
        )

    def parse_listings(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        results = []

        # Facebook Marketplace DOM varies; target common patterns for public listings
        for card in soup.select(
            "div[data-testid='marketplace_feed_item'], "
            "div[class*='x1lliihq'], "
            "div[aria-label*='location']"
        ):
            try:
                title_el = card.select_one(
                    "span[class*='x1lliihq'], div[class*='title'], span[dir='auto']"
                )
                url_el = card.select_one("a[href*='/marketplace/item/']")
                price_el = card.select_one("span[class*='price'], div[class*='price']")
                imgs = card.select("img[src]")

                title = title_el.get_text(strip=True) if title_el else ""
                href = url_el["href"] if url_el else ""
                if href and not href.startswith("http"):
                    href = "https://www.facebook.com" + href
                price_text = price_el.get_text(strip=True) if price_el else ""

                price = self._extract_price(price_text)
                surface = self._extract_surface(title)
                postal_code = self._extract_postal_code(title)
                description = title  # public cards show limited info

                if not title or not href:
                    continue

                results.append(
                    {
                        "source": self.name,
                        "url": href,
                        "title": title,
                        "price": price,
                        "surface": surface,
                        "city": "",
                        "postal_code": postal_code,
                        "description": description,
                        "image_count": len(imgs),
                        "furnished": "meublé" in title.lower(),
                        "agency": "",
                    }
                )
            except Exception:
                continue

        return results
