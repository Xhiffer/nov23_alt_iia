"""Tests de la logique de routing canary (pure, sans MLflow ni FastAPI)."""
import random

from canary import read_canary_pct, should_route_to_canary


def test_pct_zero_never_routes_to_canary():
    assert should_route_to_canary(0.0) is False


def test_pct_hundred_always_routes_to_canary():
    assert should_route_to_canary(100.0) is True


def test_pct_negative_treated_as_zero():
    assert should_route_to_canary(-5.0) is False


def test_routing_is_deterministic_with_seeded_rng():
    rng = random.Random(42)
    sequence = [should_route_to_canary(10.0, rng) for _ in range(5)]
    rng2 = random.Random(42)
    sequence2 = [should_route_to_canary(10.0, rng2) for _ in range(5)]
    assert sequence == sequence2


def test_routing_share_is_approximately_pct():
    rng = random.Random(1)
    n = 10000
    hits = sum(should_route_to_canary(20.0, rng) for _ in range(n))
    # ~20% attendu ; tolérance large pour éviter la flakiness.
    assert 0.17 < hits / n < 0.23


def test_read_canary_pct_parses_and_clamps():
    assert read_canary_pct({"CANARY_TRAFFIC_PCT": "10"}) == 10.0
    assert read_canary_pct({"CANARY_TRAFFIC_PCT": "250"}) == 100.0
    assert read_canary_pct({"CANARY_TRAFFIC_PCT": "-3"}) == 0.0
    assert read_canary_pct({"CANARY_TRAFFIC_PCT": "abc"}) == 0.0
    assert read_canary_pct({}) == 0.0
