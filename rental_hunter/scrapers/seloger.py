"""
scrapers/seloger.py – SeLoger rental scraper.
Targets the public listing search page for Île-de-France apartments.
"""

from bs4 import BeautifulSoup

from rental_hunter.scrapers.base_scraper import BaseScraper


class SeLogerScraper(BaseScraper):
    name = "SeLoger"

    def search_url(
        self,
        max_price: int = 1200,
        min_surface: int = 30,
        expand_radius: bool = False,
    ) -> str:
        # SeLoger URL structure for renting apartments in Île-de-France
        region = "ile-de-france" if expand_radius else "94,75,93"
        return (
            f"https://www.seloger.com/list.htm"
            f"?types=1"           # apartment
            f"&projects=1"        # rental
            f"&price=0/{max_price}"
            f"&surface={min_surface}/NaN"
            f"&places=[{{'cp':'{region}'}}]"
            f"&enterprise=0&qsVersion=1.0"
        )

    def parse_listings(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        results = []

        for card in soup.select("[data-listing-id], article.listing-item, div.CardContent"):
            try:
                title_el = card.select_one("a.listing-title, h2, .card__title")
                url_el = card.select_one("a[href]")
                price_el = card.select_one(".price, .listing-price, [class*='price']")
                surface_el = card.select_one(".surface, [class*='surface']")
                city_el = card.select_one(".city, .location, [class*='locality']")
                desc_el = card.select_one(".description, .resume")
                imgs = card.select("img[src]")

                title = title_el.get_text(strip=True) if title_el else ""
                url = url_el["href"] if url_el else ""
                if url and not url.startswith("http"):
                    url = "https://www.seloger.com" + url
                price_text = price_el.get_text(strip=True) if price_el else ""
                surface_text = surface_el.get_text(strip=True) if surface_el else ""
                city_text = city_el.get_text(strip=True) if city_el else ""
                description = desc_el.get_text(strip=True) if desc_el else ""

                price = self._extract_price(price_text)
                surface = self._extract_surface(surface_text or title)
                postal_code = self._extract_postal_code(city_text)

                if not title or not url:
                    continue

                results.append(
                    {
                        "source": self.name,
                        "url": url,
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
