"""
tests/test_database.py – Unit tests for the SQLite persistence layer.
Uses a temporary database file to avoid polluting the real one.
"""

import os
import tempfile
from pathlib import Path
import pytest

# Patch DB_PATH before importing database module
import rental_hunter.database as db_module


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Redirect DB_PATH to a temporary file for each test."""
    tmp_db = tmp_path / "test_rental_hunter.db"
    monkeypatch.setattr(db_module, "DB_PATH", tmp_db)
    db_module.init_db()
    db_module.init_sent_table()
    yield tmp_db


def _sample_listing(**kwargs) -> dict:
    base = {
        "url": "https://example.com/listing/1",
        "title": "Appartement 2p Créteil",
        "price": 900.0,
        "surface": 40.0,
        "city": "Créteil",
        "postal_code": "94000",
        "furnished": False,
        "source": "TestSource",
        "agency": "",
        "description": "Bel appartement lumineux.",
        "image_count": 4,
        "geo_score": 4,
        "transport_score": 3,
        "total_score": 7.5,
        "risk_level": "SAFE",
        "detected_at": "2024-01-01T10:00:00",
    }
    base.update(kwargs)
    return base


class TestSaveListing:
    def test_new_listing_saved(self):
        listing = _sample_listing()
        result = db_module.save_listing(listing)
        assert result is True

    def test_duplicate_not_saved(self):
        listing = _sample_listing()
        db_module.save_listing(listing)
        result = db_module.save_listing(listing)
        assert result is False

    def test_different_url_saved(self):
        listing1 = _sample_listing(url="https://example.com/1")
        listing2 = _sample_listing(url="https://example.com/2")
        assert db_module.save_listing(listing1) is True
        assert db_module.save_listing(listing2) is True

    def test_different_price_saved(self):
        listing1 = _sample_listing(price=900.0)
        listing2 = _sample_listing(url="https://example.com/other", price=800.0)
        assert db_module.save_listing(listing1) is True
        assert db_module.save_listing(listing2) is True


class TestListingExists:
    def test_exists_after_save(self):
        listing = _sample_listing()
        db_module.save_listing(listing)
        assert db_module.listing_exists(listing["url"], listing["title"], listing["price"]) is True

    def test_not_exists_before_save(self):
        assert db_module.listing_exists(
            "https://example.com/nonexistent", "title", 500.0
        ) is False


class TestMarkSent:
    def test_mark_sent_removes_from_unsent(self):
        listing = _sample_listing()
        db_module.save_listing(listing)
        unsent = db_module.get_unsent_listings()
        assert len(unsent) == 1
        db_module.mark_sent([unsent[0]["id"]])
        assert len(db_module.get_unsent_listings()) == 0
