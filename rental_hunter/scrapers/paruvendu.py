"""
scrapers/paruvendu.py – ParuVendu rental scraper.
"""

from bs4 import BeautifulSoup

from rental_hunter.scrapers.base_scraper import BaseScraper


class ParuVenduScraper(BaseScraper):
    name = "ParuVendu"

    def search_url(
        self,
        max_price: int = 1200,
        min_surface: int = 30,
        expand_radius: bool = False,
    ) -> str:
        region = "11" if expand_radius else "94,75,93"  # 11 = Île-de-France region code
        return (
            f"https://www.paruvendu.fr/immobilier/louer/appartement/{region}/"
            f"?px2={max_price}&m1={min_surface}"
        )

    def parse_listings(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        results = []

        for card in soup.select(
            "div.annonce, article.annonce-item, li.result-item"
        ):
            try:
                title_el = card.select_one("h2, .annonce-title, [class*='title']")
                url_el = card.select_one("a[href]")
                price_el = card.select_one(".annonce-price, [class*='price']")
                surface_el = card.select_one(".surface, [class*='surface']")
                city_el = card.select_one(".ville, .localisation, [class*='city']")
                desc_el = card.select_one(".annonce-desc, [class*='description']")
                imgs = card.select("img[src]")

                title = title_el.get_text(strip=True) if title_el else ""
                href = url_el["href"] if url_el else ""
                if href and not href.startswith("http"):
                    href = "https://www.paruvendu.fr" + href
                price_text = price_el.get_text(strip=True) if price_el else ""
                surface_text = surface_el.get_text(strip=True) if surface_el else ""
                city_text = city_el.get_text(strip=True) if city_el else ""
                description = desc_el.get_text(strip=True) if desc_el else ""

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
                        "agency": "",
                    }
                )
            except Exception:
                continue

        return results
