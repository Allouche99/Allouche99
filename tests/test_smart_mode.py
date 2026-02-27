"""
tests/test_smart_mode.py – Unit tests for smart mode logic.
"""

from rental_hunter.smart_mode import should_expand_radius, apply_smart_cap
from rental_hunter.config import SMART_MODE_MIN_LISTINGS, SMART_MODE_MAX_LISTINGS


class TestShouldExpandRadius:
    def test_expands_when_few_results(self):
        assert should_expand_radius(SMART_MODE_MIN_LISTINGS - 1) is True

    def test_no_expand_when_enough(self):
        assert should_expand_radius(SMART_MODE_MIN_LISTINGS) is False

    def test_no_expand_with_many(self):
        assert should_expand_radius(100) is False

    def test_expands_on_zero(self):
        assert should_expand_radius(0) is True


class TestApplySmartCap:
    def _make_listings(self, n: int) -> list[dict]:
        return [{"total_score": float(i), "title": f"Listing {i}"} for i in range(n)]

    def test_cap_applied_to_best_n(self):
        total_count = SMART_MODE_MAX_LISTINGS + 10
        listings = self._make_listings(total_count)
        capped = apply_smart_cap(listings)
        assert len(capped) == SMART_MODE_MAX_LISTINGS
        # Scores are 0..total_count-1; after cap, lowest kept score = total_count - MAX
        expected_min_score = total_count - SMART_MODE_MAX_LISTINGS
        scores = [l["total_score"] for l in capped]
        assert min(scores) >= expected_min_score

    def test_no_cap_when_under_limit(self):
        listings = self._make_listings(5)
        assert apply_smart_cap(listings) == listings

    def test_exact_limit_unchanged(self):
        listings = self._make_listings(SMART_MODE_MAX_LISTINGS)
        assert apply_smart_cap(listings) == listings
