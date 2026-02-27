"""
tests/test_scoring.py – Unit tests for the geographic and transport scoring engine.
"""

import pytest
from rental_hunter.scoring import (
    get_geo_score,
    get_transport_score,
    compute_total_score,
)


class TestGeoScore:
    def test_94_scores_4(self):
        assert get_geo_score("94100", "Créteil") == 4

    def test_75_scores_3(self):
        assert get_geo_score("75011", "Paris 11e") == 3

    def test_93_scores_2(self):
        assert get_geo_score("93100", "Montreuil") == 2

    def test_unknown_scores_0(self):
        assert get_geo_score("69001", "Lyon") == 0

    def test_empty_postal_scores_0(self):
        assert get_geo_score("", "Somewhere") == 0

    def test_92_scores_0(self):
        # 92 (Hauts-de-Seine) is not in primary/secondary zones → 0
        assert get_geo_score("92100", "Boulogne") == 0


class TestTransportScore:
    def test_rer_adds_3(self):
        assert get_transport_score("Proche RER A") == 3

    def test_metro_adds_2(self):
        assert get_transport_score("Accès métro ligne 13") == 2

    def test_bus_adds_1(self):
        assert get_transport_score("Bus disponible") == 1

    def test_combined_transport(self):
        # RER + metro + bus = 3+2+1 = 6
        score = get_transport_score("RER D, métro et bus à 5 min")
        assert score == 6

    def test_commute_under_30_adds_2(self):
        score = get_transport_score("", commute_minutes=25)
        assert score == 2

    def test_commute_under_45_adds_1(self):
        score = get_transport_score("", commute_minutes=40)
        assert score == 1

    def test_commute_over_45_adds_0(self):
        score = get_transport_score("", commute_minutes=60)
        assert score == 0

    def test_no_description(self):
        assert get_transport_score("") == 0

    def test_rer_pattern_case_insensitive(self):
        assert get_transport_score("rer b à 2 minutes") == 3


class TestComputeTotalScore:
    def test_unfurnished_bonus(self):
        s1 = compute_total_score(900, 40, furnished=False, geo_score=4, transport_score=3)
        s2 = compute_total_score(900, 40, furnished=True, geo_score=4, transport_score=3)
        assert s1 > s2

    def test_commute_bonus_applied(self):
        with_commute = compute_total_score(
            900, 40, furnished=False, geo_score=4, transport_score=3, commute_minutes=40
        )
        without_commute = compute_total_score(
            900, 40, furnished=False, geo_score=4, transport_score=3, commute_minutes=None
        )
        assert with_commute > without_commute

    def test_total_is_numeric(self):
        score = compute_total_score(1000, 35, furnished=True, geo_score=3, transport_score=2)
        assert isinstance(score, (int, float))
        assert score > 0
