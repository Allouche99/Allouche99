"""
scrapers/pap.py – PAP (Particulier à Particulier) rental scraper.
"""

from bs4 import BeautifulSoup

from rental_hunter.scrapers.base_scraper import BaseScraper


class PAPScraper(BaseScraper):
    name = "PAP"

    def search_url(
        self,
        max_price: int = 1200,
        min_surface: int = 30,
        expand_radius: bool = False,
    ) -> str:
        region = "region_11" if expand_radius else "departement_75,departement_94,departement_93"
        return (
            f"https://www.pap.fr/annonce/locations-appartement-{region}"
            f"?prix_max={max_price}"
            f"&surface_min={min_surface}"
        )

    def parse_listings(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        results = []

        for card in soup.select("div.search-list-item, article.item-annonce"):
            try:
                title_el = card.select_one("h2, .item-title, a.item-title")
                url_el = card.select_one("a[href]")
                price_el = card.select_one(".price, .item-price, [class*='prix']")
                surface_el = card.select_one(".item-tags, .criterias")
                city_el = card.select_one(".item-description-header-localisation, .ville")
                desc_el = card.select_one(".item-description, .description")
                imgs = card.select("img[src]")
                agency_el = card.select_one(".agency-name, .agence")

                title = title_el.get_text(strip=True) if title_el else ""
                href = url_el["href"] if url_el else ""
                if href and not href.startswith("http"):
                    href = "https://www.pap.fr" + href
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
