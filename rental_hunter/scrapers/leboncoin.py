"""
scrapers/leboncoin.py – Leboncoin rental scraper.
Targets the public listing search page for Île-de-France apartments.
"""

from bs4 import BeautifulSoup

from rental_hunter.scrapers.base_scraper import BaseScraper


class LeboncoinScraper(BaseScraper):
    name = "Leboncoin"

    def search_url(
        self,
        max_price: int = 1200,
        min_surface: int = 30,
        expand_radius: bool = False,
    ) -> str:
        region = "ile_de_france" if expand_radius else "val_de_marne,paris,seine_saint_denis"
        return (
            f"https://www.leboncoin.fr/recherche"
            f"?category=10"   # locations
            f"&real_estate_type=2"  # apartment
            f"&price=min-{max_price}"
            f"&square=min-{min_surface}"
            f"&locations={region}"
        )

    def parse_listings(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        results = []

        for card in soup.select("article[data-qa-id='aditem_container'], li[data-qa-id]"):
            try:
                title_el = card.select_one(
                    "p[data-qa-id='aditem_title'], [class*='title']"
                )
                url_el = card.select_one("a[href]")
                price_el = card.select_one(
                    "span[data-qa-id='aditem_price'], [class*='price']"
                )
                location_el = card.select_one(
                    "p[data-qa-id='aditem_location'], [class*='location']"
                )
                attrs_el = card.select_one("[data-qa-id='aditem_params']")
                imgs = card.select("img[src]")

                title = title_el.get_text(strip=True) if title_el else ""
                href = url_el["href"] if url_el else ""
                if href and not href.startswith("http"):
                    href = "https://www.leboncoin.fr" + href
                price_text = price_el.get_text(strip=True) if price_el else ""
                city_text = location_el.get_text(strip=True) if location_el else ""
                attrs_text = attrs_el.get_text(strip=True) if attrs_el else ""

                price = self._extract_price(price_text)
                surface = self._extract_surface(attrs_text + " " + title)
                postal_code = self._extract_postal_code(city_text)
                description = attrs_text

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
                        "agency": "",
                    }
                )
            except Exception:
                continue

        return results
