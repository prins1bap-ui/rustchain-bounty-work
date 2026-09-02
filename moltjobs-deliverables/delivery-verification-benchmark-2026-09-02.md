# Agent marketplace delivery-verification benchmark

**Prepared:** 2026-09-02  
**Scope:** How six marketplaces establish that delivered work is real, what role automation vs. human review plays, what happens when an artifact URL dies, and what prevents a fabricated artifact from being accepted.  
**Method:** First-party product pages, specifications, documentation, terms, and public settlement records only. Where a platform does not document a behavior, this report says **not documented** rather than inferring it.

## Executive summary

The six platforms use three materially different trust models:

1. **Executable verification:** TaskBounty is the clearest example. It runs submitted code in an isolated E2B environment, requires the existing suite to pass, and requires a fresh regression test to fail before the fix and pass after it.
2. **Escrow + acceptance criteria + review:** MoltJobs and WorkProtocol combine prefunding with machine checks where the work type permits them, then retain a requester/human review or dispute path.
3. **Escrow + settlement evidence, with less documented artifact checking:** t2000, WorkPNP, and AgentsBay document escrow and settlement clearly, but their public material is less specific about a universal automated verifier for arbitrary deliverable URLs.

A recurring weakness is **artifact durability**. An on-chain delivery hash proves that a seller committed to particular bytes or a particular reference at a point in time; it does not, by itself, make a linked artifact retrievable later. Of the sources reviewed, MoltJobs is the only platform here where current job specifications visibly expose explicit proof-hold/liveness requirements for some URL-based jobs. None of the other reviewed public docs describes a universal dead-URL recheck for every arbitrary artifact URL.

## Comparison matrix

| Platform | Automated verification? | Human review? | If a deliverable URL dies | What blocks fabricated/empty work? | Payment / escrow model |
|---|---|---|---|---|---|
| **MoltJobs** | **Yes, at least at the acceptance-criteria layer.** Its requester docs say checks run before approval and an empty submission with no artifact is rejected automatically. | **Yes.** Requester reviews the result; 72-hour silence auto-approves. | **Job-dependent.** Current public jobs can specify `Proof Hold Hours` and require a URL to remain live. I did not find a platform-wide promise that every arbitrary URL is continuously re-probed. | Structured acceptance criteria, automatic rejection of submissions with no deliverable artifact, proof-of-work hash on public jobs, then requester review. | USDC on Base; funded before work, held in escrow, released on approval or review-window expiry. |
| **WorkProtocol** | **Yes for typed/automatable work.** Code verification can run tests, lint, and build checks; the protocol also supports structured criteria. | **Yes for subjective work.** Requester review is bounded by a verification window; no response auto-approves. Disputes can go to arbitration. | **Not documented as a universal URL-liveness rule.** The API accepts deliverables such as a diff URL, but the public protocol does not specify a general recurring liveness probe for arbitrary URLs. | Automated acceptance criteria for supported categories; human verification for subjective work; dispute/arbitration if rejected. | USDC on Base or Stripe; payment locked at job creation and released after successful verification. |
| **TaskBounty** | **Strongly yes for code.** Every submission runs in an isolated E2B microVM. Existing tests must pass, and a fresh regression test must pass on the fix and fail on the pre-fix code. | **Maintainer still controls merge.** The sandbox is the verification gate before the work reaches the maintainer; payout is tied to the winning/merged result under the published flow. | **The normal artifact is a PR rather than an arbitrary hosted file.** Public docs do not describe a generic dead-URL workflow because the verifier clones/applies code and runs it. Patch submissions can send the unified diff directly. | PR existence/ownership/reference checks, sandboxed application of the code, existing test suite, and the fail-before/pass-after regression-test requirement. A fabricated screenshot or prose-only claim cannot satisfy that gate. | Funded bounty held until verified/merged result; contributor receives the published solver share. |
| **t2000** | **No universal content verifier documented in the sources reviewed.** Delivery hashes and job state are on-chain; the buyer reviews delivered work. | **Yes, buyer review is explicit.** Public settled/rejected jobs show buyers rating and accepting/rejecting deliveries. | **Not guaranteed by the delivery hash.** A hash makes the commitment immutable, but does not keep an external URL alive. I found no universal public liveness-recheck promise. A public rejected job shows that an unreadable local-file-path “delivery” can be rejected. | On-chain delivery commitment plus buyer review. Public history makes the delivery/settlement trail auditable, but correctness still depends on the buyer for general text/artifact jobs. | USDC on Sui, locked in on-chain escrow; current terms state a 5% service fee from seller settlement. |
| **WorkPNP** | **Not documented as a general automatic artifact verifier** on the public overview reviewed. | **Yes.** Buyer accepts work; buyer silence for 72 hours auto-accepts. Disputes can release, refund, or split escrow. | **Not documented.** The public overview does not state a recurring URL-liveness check or durable-artifact store. | Buyer acceptance and dispute handling. The reviewed public material does not describe a universal machine check that proves arbitrary artifact content is genuine. | USDC on Base, escrowed before work; 90% worker / 10% platform on acceptance. |
| **AgentsBay** | **Claimed yes, but mechanism is underspecified publicly.** Homepage says funds release when the deliverable “verifies” and describes “no human in the loop.” | Homepage says **no human in the loop** for the normal verification flow. | **Not documented in the public material reviewed.** I found no first-party explanation of what happens if an externally hosted artifact later becomes unreachable. | Homepage says delivery must verify before release, but the reviewed public material does not expose enough detail to establish what verifier runs, what evidence it checks, or how it detects a fabricated but well-formed artifact. | USDC escrow on Polygon according to the current homepage. |

## Platform notes

### 1. MoltJobs

MoltJobs' requester documentation describes a two-stage model: automatic acceptance-criteria checks run first, then the requester reviews the result. A submission with no deliverable artifact is rejected automatically. If the requester does nothing, the documented review window ends in auto-approval.

For URL durability, the strongest evidence is in current public job specs rather than the generic requester page. The active “durable-hosting guide” job itself exposes a 720-hour proof hold and explicitly requires a URL the worker controls and keeps live. Another current research job exposes a 168-hour proof hold. That demonstrates the platform can make liveness duration part of a job contract, but it is not evidence that every MoltJobs URL is universally rechecked forever.

**Sources**
- https://moltjobs.io/hire
- https://moltjobs.io/open-jobs/078f1c4a-37b9-4957-b8f7-b73dd32d90ed
- https://moltjobs.io/open-jobs/9d23732f-d613-4d62-8525-0f9f31713631

### 2. WorkProtocol

WorkProtocol documents verification as a first-class protocol stage. Code jobs can run a specified test command, lint checks, and build validation. Subjective work instead goes to requester review. The protocol explicitly includes an auto-approval path when a requester ignores delivered work and a dispute/arbitration path after rejection.

The API accepts structured deliverables, including URL-shaped artifacts, but the public protocol and API references reviewed do not specify a universal recurring liveness probe for those URLs. Therefore this report does not assume one exists.

**Sources**
- https://workprotocol.ai/protocol
- https://workprotocol.ai/docs/reference
- https://workprotocol.ai/for-requesters

### 3. TaskBounty

TaskBounty has the most concrete anti-fabrication gate in this sample for code work. The platform says it clones the repo into an isolated E2B microVM, runs the existing suite, and requires a newly added regression test to fail on the original code and pass on the proposed fix. Its FAQ also describes submission-level checks such as confirming that the PR exists, was authored by the submitter, and references the bounty issue.

This design mostly avoids the “dead artifact URL” problem because the artifact is normally source code in a PR. For agents that cannot open a PR, TaskBounty documents direct unified-diff submission; the service applies the patch and runs the same verifier rather than trusting an external screenshot or prose assertion.

**Sources**
- https://www.task-bounty.com/for-agents
- https://www.task-bounty.com/how-it-works
- https://www.task-bounty.com/faq

### 4. t2000

t2000's public terms state that jobs are funded into on-chain escrow on Sui and released to the seller on settlement. Public job pages expose a durable chain of posted, claimed, delivered, and settled/rejected transactions.

That creates strong evidence that a delivery happened, but it does not automatically prove the content was correct. A current rejected job is an instructive example: the seller delivered only a local path (`/tmp/staking_answer.md`), and the buyer rejected it because there was no readable answer to grade. This is direct evidence that the buyer-review layer, not merely the existence of an on-chain delivery event, is doing meaningful verification for general work.

A delivery/content hash is an integrity commitment, not a hosting guarantee. The public sources reviewed do not say that t2000 continuously probes externally hosted artifacts after delivery.

**Sources**
- https://t2000.ai/terms
- https://t2000.ai/jobs/0xb5e5526052f5ecaed765ee7b625e38539c590886cc968297024ad4ce3e6f1967
- https://t2000.ai/jobs/0xb08f5e621551e52e0eca888e18f3be87f091ef92cf66fbfb20e2310a3cf31ab5

### 5. WorkPNP

WorkPNP's public homepage says the buyer funds USDC escrow before work starts. The worker bids, delivers by the deadline, and the buyer accepts; if the buyer is silent for 72 hours, the job auto-accepts. A dispute can resolve to release, refund, or split.

The public overview reviewed does not claim a universal machine verifier for arbitrary delivered artifacts and does not explain what happens if a hosted URL becomes unavailable after delivery. The honest classification is therefore human/buyer acceptance plus dispute resolution, with dead-URL behavior **not documented** in the source reviewed.

**Source**
- https://workpnp.com/

### 6. AgentsBay

AgentsBay's homepage makes a stronger automation claim than WorkPNP: a worker delivers an artifact, funds release “on verification,” and the page says there is “no human in the loop.” It also says job funds sit in USDC escrow on Polygon.

However, the public material I could verify does not explain the verification algorithm in enough detail to answer whether it executes code, validates schemas, checks hashes, probes URLs, or uses some other evaluator. It likewise does not document a policy for an artifact URL that later dies. Those fields are therefore marked **not documented** rather than filled with inference.

**Source**
- https://agentsbay.ai/

## Practical conclusions for an agent operator

- **For executable code, prefer a verifier that can reproduce the result**, not one that only checks that a URL or hash exists. TaskBounty's fail-before/pass-after regression-test gate is the strongest documented example in this sample.
- **For research/content artifacts, escrow is only half the problem.** A URL can be valid at submission and dead days later. A job-level proof-hold/liveness rule, as exposed by current MoltJobs jobs, directly addresses that failure mode.
- **An immutable hash is evidence of commitment, not evidence of retrievability or correctness.** t2000's public ledger is valuable for auditability, but general work still needs meaningful review.
- **Auto-approval protects workers from disappearing requesters, but it raises the value of strong pre-approval checks.** MoltJobs, WorkProtocol, and WorkPNP all document time-bounded requester review/auto-accept patterns in some form.
- **“Not documented” is decision-relevant.** If a platform does not publish what its verifier checks or what happens to dead URLs, an autonomous worker should not silently assume the strongest implementation.
