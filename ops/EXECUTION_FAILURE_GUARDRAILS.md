# Execution Failure Guardrails

Purpose: prevent repeat failures, duplicate troubleshooting, false progress, and unsafe or wasteful retries across RTC/RustChain, Apify, Upwork, Replit, outreach, and related revenue experiments.

## 1. Classify before retrying

Every failed action must be assigned one class before another attempt:

1. REPO_OR_CODE_DEFECT — fixable in code/configuration owned here.
2. CONNECTOR_OR_PLATFORM_DEFECT — authenticated external integration is internally inconsistent, unavailable, timed out, or lacks required capability.
3. AUTHORIZATION_BOUNDARY — requires account-owner approval, OAuth confirmation, legal acceptance, billing, identity verification, or another user-only action.
4. EXPECTED_NEGATIVE_RESULT — the test executed correctly and disproved the hypothesis; do not label this an infrastructure failure.
5. MARKET_OR_COUNTERPARTY_OUTCOME — buyer did not respond, upstream maintainer did not merge, merchant did not convert, etc.; do not retry the same tactic merely because the result was commercially disappointing.
6. STALE_OR_SUPERSEDED_ATTEMPT — an old red run whose underlying defect has already been corrected; do not resurrect it.

No retry is permitted until the failure class and a materially different next action are identified.

## 2. Upwork connector

Known failure class: CONNECTOR_OR_PLATFORM_DEFECT.

Observed behavior: account discovery can return a single Freelancer/TALENT organization successfully while the immediately following freelancer-scoped read rejects the same context as non-Freelancer or otherwise binds the wrong account role.

Rules:
- Do not recommend or perform another disconnect/reconnect cycle unless new vendor evidence specifically shows that the defect has changed.
- Do not create additional Upwork accounts or agency relationships as a workaround.
- Do not interpret successful account discovery as proof that downstream freelancer operations work.
- A successful repair requires, in one session: account discovery -> freelancer profile read -> Connects read -> job read/proposal readiness without role contradiction.
- Zero Connects is a commercial constraint, not a connector defect. Never spend Connects or money without explicit approval.

## 3. GitHub upstream writes

Known failure class: CONNECTOR_OR_PLATFORM_DEFECT when the installed GitHub integration cannot write to an upstream repository outside its granted installation scope.

Rules:
- After a confirmed integration-scope 403 such as "Resource not accessible by integration," do not repeatedly attempt issue comments, PR creation, or other writes to the same inaccessible upstream scope.
- Keep source, evidence, branches, and reproducible artifacts in the user-owned repository.
- Use only an explicitly permitted upstream submission route or documented fallback when available.
- A GitHub Actions red status is not by itself evidence of a code defect. Inspect the failed job and logs first.

## 4. GitHub Actions test semantics

Rules:
- Separate harness/infrastructure errors from legitimate negative test outcomes.
- Missing dependencies, wrong runner environment, malformed workflow conditions, unavailable secrets, and skipped evidence upload are infrastructure defects.
- A benchmark that runs correctly but does not reproduce the claimed result is an EXPECTED_NEGATIVE_RESULT.
- Evidence collection and artifact upload should use `if: always()` when a negative outcome is itself valuable evidence.
- Do not convert a scientific or validation mismatch into a false pass. Preserve the negative result and make the job semantics explicit.

## 5. Apify

Known failure classes: AUTHORIZATION_BOUNDARY for device OAuth; CONFIGURATION_REQUIRED when a deployment secret/token is absent.

Rules:
- Interactive OAuth/device authorization workflows must be manually dispatched only. Never trigger them automatically on an ordinary Git push.
- Missing APIFY_TOKEN must fail closed before any paid or mutating API call.
- Do not publish, enable paid usage, change billing, accept legal terms, or configure payout identity without explicit user approval.
- Do not keep expanding infrastructure while verified revenue remains zero unless a buyer requirement creates a concrete need.

## 6. Replit

Known failure class: CONNECTOR_OR_PLATFORM_DEFECT when app lookup succeeds but read/update Agent operations time out.

Rules:
- Do not repeatedly fire the same Agent request after the timeout pattern has been reproduced.
- Do not claim an update applied unless the connector confirms it and the app's updated state can be read back.
- Prefer the verified GitHub-based route for work that can be completed there while Replit Agent operations remain unreliable.

## 7. Revenue and outreach

Rules:
- Sent messages, repositories, QA passes, job discoveries, proposals drafted but not submitted, traffic, and technical completion are not revenue.
- A buyer exposure counts only when the message/proposal was actually delivered through a lawful executable channel.
- Repeating generic outbound after a failed validation threshold is prohibited without a materially changed buyer, offer, channel, or evidence basis.
- No fabricated customers, payments, reviews, credentials, demand, or results.
- Prioritize buyer-initiated demand and payment probability over further infrastructure.

## 8. Retry gate

Before retrying any previously failed action, record:
- exact previous failure;
- failure class;
- what has materially changed;
- why the new attempt can succeed where the old one could not;
- spend/authorization impact;
- success criterion.

If nothing material changed, do not retry.

## 9. Success definitions

Technical repair: the previously failing operation succeeds and a read-back or independent check confirms it.

Commercial progress: a qualified exposure, substantive buyer response, accepted paid scope, contract, or verified payment, clearly distinguished from internal activity.

Revenue: externally collected payment only. Revenue is never inferred from work completed, submission status, token value, pending rewards, or verbal interest.
