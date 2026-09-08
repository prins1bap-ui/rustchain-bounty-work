import pytest

from matcher import Candidate, candidate_from_reputation, rank_candidates, score_candidate


def test_strong_reputation_and_category_fit_wins():
    job = {"category": "code", "reward_rtc": 20}
    strong = Candidate("RTCstrong", trust_score=92, avg_rating=4.9, completed_jobs=20, total_rtc_earned=250, categories=("code",))
    weak = Candidate("RTCweak", trust_score=40, avg_rating=3.0, completed_jobs=2, total_rtc_earned=5, categories=("writing",))
    ranked = rank_candidates(job, [weak, strong])
    assert [r.wallet for r in ranked] == ["RTCstrong", "RTCweak"]
    assert ranked[0].score > ranked[1].score
    assert "verified category fit: code" in ranked[0].reasons


def test_capacity_penalty_can_change_order():
    job = {"category": "research"}
    busy = Candidate("busy", trust_score=80, avg_rating=4.5, completed_jobs=10, active_jobs=5, categories=("research",))
    free = Candidate("free", trust_score=78, avg_rating=4.5, completed_jobs=10, active_jobs=0, categories=("research",))
    ranked = rank_candidates(job, [busy, free])
    assert ranked[0].wallet == "free"
    assert ranked[0].components["capacity"] == 100
    assert ranked[1].components["capacity"] == 0


def test_missing_category_history_is_neutral_not_perfect():
    item = score_candidate({"category": "video"}, Candidate("new", trust_score=60, avg_rating=4, completed_jobs=1))
    assert item.components["category_fit"] == 50


def test_candidate_normalization_does_not_invent_missing_reputation():
    c = candidate_from_reputation("RTCnew", {"trust_score": 17})
    assert c.trust_score == 17
    assert c.avg_rating == 0
    assert c.completed_jobs == 0
    assert c.total_rtc_earned == 0


def test_duplicate_wallet_uses_last_explicit_candidate_once():
    ranked = rank_candidates(
        {"category": "code"},
        [Candidate("same", trust_score=1), Candidate("same", trust_score=99)],
    )
    assert len(ranked) == 1
    assert ranked[0].components["trust"] == 99


def test_deterministic_tiebreak_by_wallet():
    c1 = Candidate("b-wallet", trust_score=50)
    c2 = Candidate("A-wallet", trust_score=50)
    assert [r.wallet for r in rank_candidates({}, [c1, c2])] == ["A-wallet", "b-wallet"]


def test_limit_and_validation():
    candidates = [Candidate(f"w{i}", trust_score=i) for i in range(10)]
    assert len(rank_candidates({}, candidates, limit=3)) == 3
    with pytest.raises(ValueError):
        rank_candidates({}, candidates, limit=0)
    with pytest.raises(ValueError):
        rank_candidates({}, [Candidate(" ")])


def test_values_are_bounded_against_bad_upstream_ranges():
    result = score_candidate({}, Candidate("odd", trust_score=1000, avg_rating=99, completed_jobs=10_000, total_rtc_earned=1_000_000, active_jobs=100))
    assert result.components["trust"] == 100
    assert result.components["rating"] == 100
    assert result.components["experience"] == 100
    assert result.components["earnings_history"] == 100
    assert result.components["capacity"] == 0
    assert 0 <= result.score <= 100
