# RIP-302 Reputation-Weighted Dispute Voting

Implementation of the **Tier 3 Dispute resolution — 100 RTC** task in rustchain-bounties #683.

This module produces a deterministic settlement recommendation for a disputed Agent Economy job. It deliberately does **not** move RTC or execute escrow release itself; existing RustChain controls or a maintainer can apply an accepted recommendation.

## Rules

- Only reputation holders at or above the configured minimum trust score receive voting weight.
- One vote per wallet. Duplicate voter or vote records fail closed.
- Quorum is based on distinct eligible voters.
- Abstentions count toward quorum but not toward either side's decisive share.
- A side must reach the configured supermajority threshold (default 60%) of non-abstaining weighted votes.
- Ties and insufficient majorities produce `no_decision`, never an invented winner.
- Unknown or low-trust voters are ignored and recorded in the rationale.
- The complete voter/vote input receives a deterministic SHA-256 evidence hash for audit/replay.

## Reputation weighting

Voting power is bounded. Trust score supplies the majority of weight while completed jobs and prior dispute participation add small capped bonuses. This lets established marketplace participants matter more without allowing one veteran wallet to have unlimited control.

## Example

```python
from dispute_voting import Choice, Vote, Voter, settle_dispute

result = settle_dispute(
    "job_abc",
    [
        Voter("RTCa", trust_score=92, completed_jobs=20),
        Voter("RTCb", trust_score=84, completed_jobs=12),
        Voter("RTCc", trust_score=70, completed_jobs=4),
    ],
    [
        Vote("RTCa", Choice.WORKER, "deliverable matches scope"),
        Vote("RTCb", Choice.WORKER, "evidence reproducible"),
        Vote("RTCc", Choice.POSTER, "deadline missed"),
    ],
)

print(result.outcome, result.evidence_hash)
```

## QA

```bash
python -m py_compile dispute_voting.py test_dispute_voting.py
pytest -q
```

Tests cover worker/poster decisions, ties, supermajority failure, abstentions, quorum, ineligible/unknown voters, duplicate protection, invalid policy settings, bounded voting power, and deterministic evidence hashing.

## Safety boundary

This is a governance/recommendation component, not a payment executor. It does not accept private keys, sign wallet transactions, transfer RTC, unlock escrow, or alter production state. That separation keeps a voting bug from becoming an automatic funds-movement bug.

## Non-duplication

Before implementation, the current #683 thread and repository search were checked for the advertised voting-based dispute-settlement feature; no competing implementation surfaced. Existing visible submissions cover SDK, CLI, Discord, Beacon and other integrations.

RTC wallet: `RTCc5449fe1b93385961152720c864c0f073dae5855`
