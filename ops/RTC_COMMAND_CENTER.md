# RTC Command Center

## Objective

Maximize **verified RTC accepted/queued and ultimately received per day**, not the number of submissions, nominal bounty value, or amount of code produced.

The governing metric is:

`expected_rtc_per_hour = title_reward_rtc × P(acceptance) × P(payout | acceptance) / estimated_hours`

Payout latency is a tie-breaker: when two candidates have similar expected RTC/hour, prefer the one with stronger evidence of recent maintainer settlement and the shorter path to an authoritative payout record.

## Canonical accounting stages

Only these stages are allowed:

1. `BUILT` — deliverable exists but has not been submitted.
2. `SUBMITTED` — maintainer can inspect the claim/deliverable.
3. `ACCEPTED_QUEUED` — authoritative maintainer evidence explicitly accepts or queues the reward.
4. `PENDING_ON_CHAIN` — authoritative payout evidence includes a pending transfer identifier and/or transaction hash tied to this claim.
5. `RECEIVED` — authoritative evidence shows the transfer completed to the claimant.
6. `DEAD` — awarded elsewhere, saturated, invalid, superseded, or otherwise no longer receivable.
7. `EXTERNALLY_BLOCKED` — requires a real external action/evidence that cannot presently be completed autonomously.

Never promote a claim merely because it was built, emailed, merged, or described as valuable.

## Corrected baseline — 2026-09-01

- `RECEIVED`: **0 RTC verified**.
- `PENDING_ON_CHAIN`: **0 RTC verified**.
- `ACCEPTED_QUEUED`: **93 RTC verified floor**.
  - #71: 25 RTC.
  - #398 Step 1: 10 RTC.
  - #398 Step 2: 7 RTC.
  - #254 accepted action: 1 RTC.
  - #402 kickoff tranche: 50 RTC.
- #402 completion tranche: **50 RTC submitted/conditional on accepted delivery**.
- #16497: **two distinct 33 RTC long-form submissions exist** under the stated 2/2 cap; neither is promoted without new maintainer adjudication.

The structured ledger in `ops/rtc_ledger.json` is authoritative for individual claims.

## Run algorithm

### Phase 1 — Receivables first, zero nagging

At the beginning of every RTC pass, inspect existing substantive claims for **new authoritative evidence only**: acceptance, queueing, merge/adjudication, requested revision, rejection, pending ID, transaction hash, or receipt.

Do not send generic follow-ups. Do not create a new email subject for an existing economic claim. A revision or new evidence belongs in the existing GitHub PR/thread or Gmail conversation whenever possible.

Priority receivables include #402 completion, both #16497 article slots, the distinct #685 submissions, and every other ledger row still at `SUBMITTED` where a maintainer has actually moved the state.

### Phase 2 — Build a current opportunity inventory

Search the authoritative bounty tracker and relevant Elyan repositories. Do **not** treat `state=open` as proof that work remains available.

Every candidate must pass all of these checks before construction:

- current issue is open and payable;
- authoritative current **title** reward is recorded;
- pool/cap/slot remains available;
- no conflicting cap already consumed by this claimant;
- issue comments checked for `/claim`, completion, maintainer reservation, award, or saturation;
- open PRs checked for the same deliverable;
- recently merged/closed PRs checked for the same deliverable;
- current target source inspected so the requested gap still exists;
- acceptance criteria are objectively satisfiable;
- required route can be completed with connected tools;
- no fabricated publication, hardware, account activity, engagement, test result, transaction, or endpoint evidence is required.

If one credible mergeable competing PR already occupies a first-wins deliverable, heavily discount the candidate. Two or more complete equivalents normally kill it.

### Phase 3 — Score before building

For each candidate record:

- `reward_rtc`
- `acceptance_probability` from 0 to 1
- `payout_probability_given_acceptance` from 0 to 1
- `estimated_hours`
- `recent_settlement_evidence` from 0 to 1
- `competition_count`
- `submission_route`

Base score:

`reward × acceptance_probability × payout_probability / hours`

Then prefer higher recent-settlement evidence and lower competition. Headline reward alone never wins the ranking.

### Phase 4 — One live construction

Only **one speculative build may be ACTIVE at a time**. Finish, validate, submit, and ledger it before beginning the next speculative build.

This rule does not prevent read-only screening or handling a concrete maintainer revision on an existing claim.

### Phase 5 — Submission hierarchy

For ordinary code/docs work, use this order:

1. authenticated upstream-network fork → focused branch → tested commit → upstream PR;
2. direct authorized GitHub issue/comment route;
3. writable own public repository when the bounty expressly accepts a standalone artifact;
4. official email fallback **only when the bounty/project explicitly authorizes it and GitHub write actually fails**.

Email fallback is valid but expensive in adjudication latency. Do not use it as the default merely because it is available.

### Phase 6 — Duplicate guard

One economic claim gets one canonical ledger ID.

- A revision is not a new claim.
- A re-send after a delivery failure is not a new claim.
- A second email with the same bounty/deliverable is marked `duplicate_of` or `revision_of`.
- A cap-overflow submission is never counted as receivable.
- A requested reward is not counted until authoritative evidence supports the applicable stage.

### Phase 7 — Update ledger immediately

After every meaningful action, update `ops/rtc_ledger.json` before starting another build. The ledger, not conversational memory, governs future accounting.

## Daily portfolio

Target execution capacity:

- **60%** — fresh, unsaturated, PR-able work with visible recent settlement behavior.
- **25%** — fast, stackable, objectively verifiable micro-bounties with high acceptance probability.
- **15%** — receivable reconciliation and concrete requested revisions.

If there is no high-quality candidate, submit nothing rather than manufacture activity.

## Candidate kill rules

Reject a candidate before construction when any of the following is true:

- requested gap no longer exists in current source;
- exact deliverable is already merged/awarded;
- first-wins slot is credibly occupied;
- claimant cap is already consumed;
- required external proof cannot be produced honestly;
- only submission route is unavailable and no official fallback is authorized;
- expected RTC/hour falls below a materially better executable candidate;
- the actual work falls outside applicable safety requirements.

Safety is evaluated from the **actual requested work**, not keyword matching. Do not reject benign wallet/blockchain/reliability work simply because of terminology, and do not rephrase unsafe work to evade product protections.

## Communication discipline

- Never send a generic adjudication reminder.
- Never submit the same economic claim under a new subject merely to increase visibility.
- Use one thread per claim whenever possible.
- Correct accounting mistakes with a concise ledger correction, then stop.
- Maintainer bandwidth is a scarce resource; optimize for reviewability.

## Success criteria

A good day is measured in this order:

1. RTC newly `RECEIVED`.
2. RTC newly `PENDING_ON_CHAIN` with authoritative transfer evidence.
3. RTC newly `ACCEPTED_QUEUED`.
4. High-probability new `SUBMITTED` work that passed every gate.

Raw submission count is not a success metric.
