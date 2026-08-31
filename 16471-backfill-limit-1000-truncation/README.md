# RustChain bounty #16471 finding: PR-review backfill silently omits older claims beyond its 1,000-issue window

**Reporter:** `@prins1bap-ui`  
**RTC wallet:** `RTCc5449fe1b93385961152720c864c0f073dae5855`  
**Scope:** `scripts/pr_review_gate_backfill.py`  
**Current source blob checked:** `ab1eadfc6de9dbee2723950bdbb1a09831cdd5db`

## Summary

The PR-review backfill is explicitly intended to rescue old claims that missed normal adjudication. It says it processes the oldest waiting contributors first. But candidate enumeration is hard-capped before that ordering logic runs:

```python
["gh", "issue", "list", "-R", REPO, "--state", "open",
 "--limit", "1000", "--json", "number,title,labels"]
```

GitHub CLI's default `gh issue list` behavior returns the most recent open items. The current `Scottcjn/rustchain-bounties` repository has **1,311 open issues** as measured through GitHub's issue search API on 2026-08-31.

Therefore, the backfill can see at most 1,000 of those 1,311 open issues. Up to 311 older open issues are outside the candidate set before `list_unprocessed()` ever applies its `sorted(never), sorted(stranded)` oldest-first policy.

An old unprocessed PR-review claim in the omitted tail is silently invisible on every run as long as it remains outside the newest 1,000-item window. The workflow can still print a normal adjudication summary and exit 0.

## Why the later sort does not fix this

The script comments say:

```python
# Oldest first: the longest-waiting contributor gets an answer first.
return sorted(never), sorted(stranded)
```

But this sort applies only to the already-truncated 1,000-item response. Sorting cannot recover omitted issues.

This creates the exact opposite of the backfill's stated guarantee: the oldest claims are the ones most likely to be excluded before prioritization.

## Deterministic reproduction

`poc.py` models 1,311 open issues numbered oldest to newest, with issue #1 being an unprocessed PR-review claim and all others unrelated. It then models the current `--limit 1000` recent-item fetch and the script's later filtering/sorting.

Expected output:

```text
total_open         = 1311
fetch_limit        = 1000
returned_count     = 1000
omitted_count      = 311
claim_1_enumerated = False
backfill_never     = []
REPRODUCED: oldest unprocessed review claim is invisible before oldest-first sorting
```

No network, credentials, wallet operations, or production mutations are needed for the proof.

## Current evidence

On 2026-08-31, GitHub's search API returned:

```json
{"total_count": 1311, "incomplete_results": false}
```

for:

```text
repo:Scottcjn/rustchain-bounties is:issue is:open
```

So the repository is currently above the script's 1,000-issue enumeration ceiling.

## Impact

An old review claim that the backfill exists specifically to rescue can remain permanently unadjudicated while the workflow reports successful completion for everything it did see. No exception, non-zero exit, or "claims omitted by enumeration" notice is produced.

This is distinct from my earlier backfill finding where the `gh issue list` subprocess itself fails and empty stdout is treated as an empty candidate set. Here the `gh` command succeeds and returns valid JSON; the defect is successful-but-incomplete enumeration caused by the hard limit.

## Suggested fix

Enumerate all pages/candidates rather than imposing a 1,000-item global pre-filter. Practical options include:

- use GitHub search specifically for review-claim titles/labels with pagination;
- paginate the issue list until exhaustion;
- or explicitly query oldest-first before applying a bounded processing budget.

`MAX_PER_RUN` should bound **adjudications**, not candidate discovery. If candidate discovery itself must be bounded, the workflow should detect and report that the result set was truncated rather than treating the returned window as complete.

Add a regression with >1,000 open issues and an old unprocessed review claim outside the first fetched page/window, and assert that the claim remains discoverable.

Submitted for maintainer confirmation under bounty #16471. No acceptance or payout is asserted until confirmed.