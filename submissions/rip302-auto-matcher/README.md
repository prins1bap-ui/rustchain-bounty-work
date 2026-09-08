# RIP-302 Reputation Auto-Matcher

A deterministic, explainable implementation of the **75 RTC Auto-matching** task in rustchain-bounties #683.

The matcher ranks candidate workers for an Agent Economy job using public reputation evidence instead of choosing the largest wallet or an opaque random score.

## Scoring

Each candidate receives a 0–100 score from:

- 35% trust score
- 20% average rating
- 15% completed-job experience
- 5% historical RTC earnings
- 10% current capacity
- 15% category fit

Experience and earnings use logarithmic scaling so one very old/high-volume account cannot make every newer worker mathematically irrelevant. Missing category history is neutral (50), not falsely treated as a perfect match. Active workload reduces the capacity component.

Every recommendation returns its component scores and human-readable reasons, making the ranking auditable.

## Live mode

The CLI reads current reputation from the public RIP-302 endpoint:

```bash
python matcher.py \
  --job '{"category":"code","reward_rtc":25}' \
  --wallet RTCcandidate1 \
  --wallet RTCcandidate2
```

By default it queries:

`GET https://rustchain.org/agent/reputation/<wallet>`

It performs no transfers, escrow actions, claims, or other mutations.

## Library use

```python
from matcher import Candidate, rank_candidates

job = {"category": "research", "reward_rtc": 10}
candidates = [
    Candidate("RTCa", trust_score=90, avg_rating=4.8, completed_jobs=12, categories=("research",)),
    Candidate("RTCb", trust_score=75, avg_rating=5.0, completed_jobs=3, categories=("code",)),
]

for match in rank_candidates(job, candidates):
    print(match.wallet, match.score, match.reasons)
```

## QA

```bash
python -m py_compile matcher.py test_matcher.py
pytest -q
```

Tests cover reputation/category ranking, capacity penalties, missing-data handling, deduplication, deterministic tie-breaking, limits/validation, and bounding malformed upstream values.

## Scope / non-duplication

This targets the separately advertised **Tier 3 Auto-matching — 75 RTC** deliverable in #683. Before implementation, the current #683 issue thread and repository search were checked for an existing auto-matching implementation; the visible competing work covered SDK, CLI, Discord and Beacon integrations, not this task.

RTC wallet: `RTCc5449fe1b93385961152720c864c0f073dae5855`
