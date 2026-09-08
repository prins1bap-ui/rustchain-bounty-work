import pytest

from dispute_voting import Choice, Vote, Voter, settle_dispute, voting_weight


def voters():
    return [
        Voter("alice", 90, completed_jobs=25, disputes_participated=3),
        Voter("bob", 80, completed_jobs=10, disputes_participated=1),
        Voter("cara", 70, completed_jobs=5),
        Voter("low", 20, completed_jobs=100),
    ]


def test_worker_wins_with_quorum_and_threshold():
    result = settle_dispute(
        "d1",
        voters(),
        [Vote("alice", Choice.WORKER), Vote("bob", Choice.WORKER), Vote("cara", Choice.POSTER)],
    )
    assert result.quorum_met is True
    assert result.outcome == "worker"
    assert result.worker_weight > result.poster_weight
    assert len(result.evidence_hash) == 64


def test_poster_can_win():
    result = settle_dispute(
        "d2",
        voters(),
        [Vote("alice", Choice.POSTER), Vote("bob", Choice.POSTER), Vote("cara", Choice.WORKER)],
    )
    assert result.outcome == "poster"


def test_below_threshold_yields_no_decision():
    equal = [Voter("a", 80), Voter("b", 80), Voter("c", 80), Voter("d", 80)]
    result = settle_dispute(
        "d3",
        equal,
        [Vote("a", Choice.WORKER), Vote("b", Choice.WORKER), Vote("c", Choice.POSTER), Vote("d", Choice.POSTER)],
        min_voters=4,
    )
    assert result.outcome == "no_decision"
    assert result.quorum_met is True


def test_abstention_counts_for_quorum_not_decisive_share():
    equal = [Voter("a", 90), Voter("b", 90), Voter("c", 90)]
    result = settle_dispute(
        "d4",
        equal,
        [Vote("a", Choice.WORKER), Vote("b", Choice.WORKER), Vote("c", Choice.ABSTAIN)],
    )
    assert result.quorum_met is True
    assert result.outcome == "worker"
    assert result.abstain_weight > 0


def test_low_trust_vote_is_ignored_and_can_break_quorum():
    result = settle_dispute(
        "d5",
        voters(),
        [Vote("alice", Choice.WORKER), Vote("bob", Choice.WORKER), Vote("low", Choice.WORKER)],
    )
    assert result.quorum_met is False
    assert result.outcome == "no_decision"
    assert result.votes_counted == 2


def test_unknown_voter_is_ignored_with_reason():
    result = settle_dispute(
        "d6",
        voters(),
        [Vote("alice", Choice.WORKER), Vote("bob", Choice.WORKER), Vote("ghost", Choice.POSTER)],
    )
    assert result.quorum_met is False
    assert any("unknown voter ghost" in r for r in result.rationale)


def test_duplicate_vote_fails_closed():
    with pytest.raises(ValueError, match="duplicate vote"):
        settle_dispute("d7", voters(), [Vote("alice", Choice.WORKER), Vote("alice", Choice.POSTER)])


def test_duplicate_voter_fails_closed():
    with pytest.raises(ValueError, match="duplicate voter"):
        settle_dispute("d8", [Voter("same", 90), Voter("same", 80)], [])


def test_invalid_policy_parameters_fail_closed():
    with pytest.raises(ValueError):
        settle_dispute("", voters(), [])
    with pytest.raises(ValueError):
        settle_dispute("d", voters(), [], min_voters=0)
    with pytest.raises(ValueError):
        settle_dispute("d", voters(), [], decision_threshold=0.5)


def test_voting_weight_is_bounded_and_requires_trust():
    assert voting_weight(Voter("low", 49.9, completed_jobs=9999)) == 0
    weight = voting_weight(Voter("high", 999, completed_jobs=9999, disputes_participated=999))
    assert 1 <= weight <= 7


def test_evidence_hash_is_deterministic_across_voter_order():
    vote_set = [Vote("alice", Choice.WORKER, "evidence A"), Vote("bob", Choice.POSTER, "evidence B"), Vote("cara", Choice.ABSTAIN)]
    one = settle_dispute("stable", voters(), vote_set)
    two = settle_dispute("stable", list(reversed(voters())), list(reversed(vote_set)))
    assert one.evidence_hash == two.evidence_hash
    assert one.outcome == two.outcome
