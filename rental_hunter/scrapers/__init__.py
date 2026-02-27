"""
scrapers/__init__.py – Registry of all available scrapers.
"""

from rental_hunter.scrapers.seloger import SeLogerScraper
from rental_hunter.scrapers.leboncoin import LeboncoinScraper
from rental_hunter.scrapers.pap import PAPScraper
from rental_hunter.scrapers.bienici import BieniciScraper
from rental_hunter.scrapers.logic_immo import LogicImmoScraper
from rental_hunter.scrapers.paruvendu import ParuVenduScraper
from rental_hunter.scrapers.facebook import FacebookScraper
from rental_hunter.scrapers.agency import AgencyScraper

ALL_SCRAPERS = [
    SeLogerScraper,
    LeboncoinScraper,
    PAPScraper,
    BieniciScraper,
    LogicImmoScraper,
    ParuVenduScraper,
    FacebookScraper,
    AgencyScraper,
]

__all__ = ["ALL_SCRAPERS"]
