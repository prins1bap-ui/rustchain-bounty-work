# RTC Command Center

## Objective

Maximize **verified RTC received per unit of execution time**. Secondary objectives, in order, are new `PENDING_ON_CHAIN`, new `ACCEPTED_QUEUED`, then only high-probability `SUBMITTED` work.

Raw submission count and nominal pipeline size are not success metrics.

## Governing economic score

Use a latency-adjusted score rather than headline reward alone:

`expected_collected_rtc_per_hour = reward_rtc × P(acceptance) × P(payout|acceptance) × settlement_velocity / estimated_hours`

Where `settlement_velocity` is a 0–1 factor based on observed review/settlement latency for that route/bounty class. A slow or historically unadjudicated route is materially discounted, not merely tie-broken.

Probability estimates must be calibrated from actual outcomes whenever enough history exists. Do not repeatedly use optimistic priors that conflict with observed acceptance or settlement behavior.

## Canonical accounting stages

Only these stages are allowed:

1. `BUILT`
2. `SUBMITTED`
3. `ACCEPTED_QUEUED`
4. `PENDING_ON_CHAIN`
5. `RECEIVED`
6. `DEAD`
7. `EXTERNALLY_BLOCKED`

Never promote a claim merely because it was built, emailed, merged, or described as valuable.

## Current conversion state

As of 2026-09-02 the verified fixed-value funnel is:

- `SUBMITTED`: 607 RTC
- `ACCEPTED_QUEUED`: 93 RTC
- `PENDING_ON_CHAIN`: 0 RTC
- `RECEIVED`: 0 RTC

This ratio makes **conversion/settlement the current binding constraint**. The command center therefore operates in `SETTLEMENT_ADJUDICATION` mode until the mode-switch conditions below are met.

The structured ledger in `ops/rtc_ledger.json` remains authoritative for individual claims. `ops/efficiency_policy.json` is authoritative for mode, recheck triggers, and discovery policy.

## Mode switching

### SETTLEMENT_ADJUDICATION mode — current default

Use this mode whenever either condition is true:

- accepted/queued RTC is materially overdue relative to authoritative settlement guidance; or
- fixed-value submitted backlog is greater than 3× accepted/queued backlog without corresponding conversion.

Allocation target:

- **70%** receivable reconciliation, concrete adjudication repair, requested revisions, and settlement evidence.
- **20%** delta discovery for newly created/materially updated high-quality opportunities.
- **10%** new construction, only when the candidate clears the elevated build gate.

Do **not** create more speculative work merely to increase nominal pipeline value.

### PRODUCTION mode

Return to normal production only when settlement is demonstrably moving or the submitted/accepted imbalance materially improves.

Allocation target:

- 55% fresh high-conversion work
- 25% fast stackable work
- 20% receivable reconciliation

## Phase 1 — Receivables first

At the beginning of every substantive RTC pass, inspect existing receivables for **new authoritative evidence only**: acceptance, queueing, requested revision, rejection, pending ID, transaction hash, or receipt.

Every receivable should carry, where evidence exists:

- `submitted_at`
- `accepted_at`
- `expected_review_by`
- `expected_settlement_by`
- `age_hours`
- `next_action_trigger`

An overdue settlement relative to an authoritative timeline is a **concrete reconciliation discrepancy**, not a generic follow-up condition. Investigate authoritative channels for missing evidence. Do not spam maintainers.

Never send generic adjudication reminders and never create a new email subject for an existing economic claim.

## Phase 2 — Route-first candidate gate

Before deep source review, competition analysis, or construction, verify the submission route.

Immediate kill if:

- required upstream repo is not writable and no allowed alternative exists;
- required external publication/account/hardware action is unavailable;
- required GitHub action is not exposed by the connected route;
- required fund movement/signing/payment is excluded;
- only an unauthorized fallback exists.

Only after route viability passes should the system spend effort on source-gap analysis, cap/slot checks, competing PR review, or implementation planning.

## Phase 3 — Delta discovery, not full rescans

After a baseline inventory exists, search primarily for:

- newly created bounty issues;
- materially updated bounty issues;
- changed reward/cap/acceptance terms;
- competitor PR closure/rejection that re-opens a lane;
- newly available connector/submission route;
- maintainer messages that change adjudication economics.

Do not fully rescan terminal candidates each run.

Every rejected candidate gets a recheck trigger:

- `never` — awarded, expired, claimant cap consumed, superseded.
- `route_change` — only revisit if a required connector/write/publication route becomes available.
- `competitor_change` — revisit only if occupying implementation is rejected/closed without award.
- `maintainer_update` — revisit only if reward, cap, rules, or assignment changes.
- `date_trigger` — revisit only on/after a specific date.

## Phase 4 — Elevated build gate

In `SETTLEMENT_ADJUDICATION` mode, a new speculative build must satisfy all of these:

- route executable now;
- clearly benign execution category;
- objectively verifiable acceptance criteria;
- unsaturated and not credibly occupied;
- claimant cap available;
- expected collected RTC/hour materially exceeds the value of additional receivable work;
- evidence of recent maintainer acceptance/settlement for the same or similar route;
- no meaningful increase in adjudication burden from duplicative package expansion.

Keep at most one speculative build active.

## #16471 throttle

The existing #16471 finding set is frozen at the current submitted count unless one of these occurs:

- maintainer confirms/adjudicates at least part of the current set;
- maintainer requests additional findings;
- a newly discovered defect is exceptionally distinct and high-confidence and clearly outweighs the adjudication-cost penalty.

Do not expand the finding count simply because the bounty formula is uncapped.

## Submission hierarchy

1. authenticated upstream-network fork → focused branch → tests → upstream PR;
2. direct authorized GitHub issue/comment route;
3. writable own public repository when expressly accepted;
4. official email fallback only when explicitly authorized and the normal GitHub route actually fails.

Email fallback is a latency penalty and should be reflected in scoring.

## Duplicate guard

One economic claim gets one canonical ledger ID. Revisions, re-sends, evidence corrections, and thread consolidations are not new claims. Cap overflow is never counted.

## 500 RTC rolling target

Track both:

- `gap_to_500_received_rtc`
- `verified_24h_receivable_ceiling_rtc`

Never imply the 500 RTC target is presently achievable unless authoritative evidence supports enough claims progressing through the required stages within the window.

If the verified ceiling is below 500, state the binding constraints internally and continue only economically justified work.

## Narrow execution allowlist

Detailed execution is restricted to documentation, tutorials, localization/accessibility, ordinary functional reliability, developer tooling, SDK/examples, reproducible objective QA, content packages, receivable reconciliation, and other clearly benign contribution work.

Candidates outside that allowlist are rejected before detailed source analysis. Do not rename or reframe disallowed work to force it through.

## Communication discipline

Notify only for concrete stage changes, actual work built/submitted, an unavoidable owner-only blocker to a high-value live opportunity, a material rolling-scoreboard change, or genuine exhaustion.

Maintainer bandwidth is a scarce economic resource. Optimize for conversion and reviewability.

## Success criteria

A good run is measured in this order:

1. new `RECEIVED` RTC;
2. new `PENDING_ON_CHAIN` RTC;
3. new `ACCEPTED_QUEUED` RTC;
4. concrete repair that increases probability of conversion;
5. only then, a high-probability new `SUBMITTED` deliverable.
