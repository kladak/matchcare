from app.services.matching import WEIGHTS, jaccard, location_score, score_pair, tier_score


def test_jaccard():
    assert jaccard({"a", "b"}, {"b", "c"}) == 1 / 3
    assert jaccard(set(), {"a"}) == 0.0


def test_location_and_tier():
    assert location_score("SF", "Bay", "SF", "Bay") == 1.0
    assert location_score("Oakland", "Bay", "SF", "Bay") == 0.55
    assert location_score("Denver", "Front", "SF", "Bay") == 0.15
    assert tier_score("premium", {"standard", "premium"}) == 1.0
    assert tier_score("basic", {"premium"}) == 0.0


def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_score_pair_explainable():
    b = score_pair(
        preferred_specialties={"Cardiology", "Endocrinology"},
        provider_specialties={"Cardiology", "Internal Medicine"},
        patient_city="San Francisco",
        patient_region="Bay Area",
        provider_city="San Francisco",
        provider_region="Bay Area",
        patient_tier="premium",
        accepted_tiers={"standard", "premium"},
        remaining_slots=7,
        weekly_capacity=12,
    )
    assert b.specialty > 0
    assert b.location == 1.0
    assert b.tier == 1.0
    assert 0 < b.availability < 1
    assert 0 < b.score <= 1
