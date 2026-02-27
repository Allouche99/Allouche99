"""
scrapers/logic_immo.py – Logic-Immo rental scraper.
"""

from bs4 import BeautifulSoup

from rental_hunter.scrapers.base_scraper import BaseScraper


class LogicImmoScraper(BaseScraper):
    name = "Logic-Immo"

    def search_url(
        self,
        max_price: int = 1200,
        min_surface: int = 30,
        expand_radius: bool = False,
    ) -> str:
        zone = "ile-de-france" if expand_radius else "94,75,93"
        return (
            f"https://www.logic-immo.com/location-immobilier-{zone},0_1/"
            f"options/groupprptypesids=1/pricemax={max_price}/surfacemin={min_surface}"
        )

    def parse_listings(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        results = []

        for card in soup.select(
            "article.offer-item, div.offer-block, li.offer-card"
        ):
            try:
                title_el = card.select_one("h2, .offer-title, [class*='title']")
                url_el = card.select_one("a[href]")
                price_el = card.select_one(".offer-price, [class*='price']")
                surface_el = card.select_one(".offer-area, [class*='surface']")
                city_el = card.select_one(".offer-locality, [class*='city']")
                desc_el = card.select_one(".offer-description, [class*='description']")
                imgs = card.select("img[src]")
                agency_el = card.select_one(".agency-name, [class*='agency']")

                title = title_el.get_text(strip=True) if title_el else ""
                href = url_el["href"] if url_el else ""
                if href and not href.startswith("http"):
                    href = "https://www.logic-immo.com" + href
                price_text = price_el.get_text(strip=True) if price_el else ""
                surface_text = surface_el.get_text(strip=True) if surface_el else ""
                city_text = city_el.get_text(strip=True) if city_el else ""
                description = desc_el.get_text(strip=True) if desc_el else ""
                agency = agency_el.get_text(strip=True) if agency_el else ""

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
