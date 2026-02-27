"""
tests/test_scam_detector.py – Unit tests for heuristic scam detection.
"""

import pytest
from rental_hunter.scam_detector import classify_risk_heuristic


class TestScamDetectorHeuristic:
    def _make_listing(self, **kwargs) -> dict:
        base = {
            "title": "Appartement 2 pièces",
            "price": 900.0,
            "surface": 40.0,
            "description": "Beau appartement bien situé avec cuisine équipée et parking.",
            "image_count": 5,
            "agency": "Agence ImmoPlus",
        }
        base.update(kwargs)
        return base

    def test_normal_listing_is_safe(self):
        listing = self._make_listing()
        assert classify_risk_heuristic(listing) == "SAFE"

    def test_suspicious_keyword_raises_warning(self):
        listing = self._make_listing(
            description="Envoyez un virement beforehand pour réserver.",
            agency="",
        )
        assert classify_risk_heuristic(listing) in ("WARNING", "HIGH RISK")

    def test_price_anomaly_raises_flag(self):
        # €/m² = 200/40 = 5 < threshold of 7
        listing = self._make_listing(price=200.0, surface=40.0)
        result = classify_risk_heuristic(listing)
        assert result in ("WARNING", "HIGH RISK")

    def test_no_photos_raises_flag(self):
        # No photos + short description together accumulate enough flags for WARNING
        listing = self._make_listing(image_count=0, agency="", description="ok")
        result = classify_risk_heuristic(listing)
        assert result in ("WARNING", "HIGH RISK")

    def test_poor_description_raises_flag(self):
        # Short description + no photos → two flags → WARNING
        listing = self._make_listing(description="ok", agency="", image_count=0)
        result = classify_risk_heuristic(listing)
        assert result in ("WARNING", "HIGH RISK")

    def test_western_union_is_high_risk(self):
        listing = self._make_listing(
            description="Paiement via western union uniquement. Pas de photos.",
            image_count=0,
            agency="",
            price=300.0,
            surface=40.0,
        )
        result = classify_risk_heuristic(listing)
        assert result == "HIGH RISK"

    def test_agency_listing_with_photos_is_safe(self):
        listing = self._make_listing(
            agency="Century 21",
            image_count=10,
            price=1100.0,
            surface=45.0,
            description=(
                "Bel appartement de 45m² situé en plein cœur de Créteil, "
                "proche RER D et bus, cuisine équipée, balcon exposé sud."
            ),
        )
        assert classify_risk_heuristic(listing) == "SAFE"
