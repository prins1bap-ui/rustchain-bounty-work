# Cross-Project Failure Audit — 2026-09-09

This document records recurring failures found across the current revenue/work threads and the durable handling rule for each. Historical red CI runs are grouped by root cause instead of counted as separate incidents.

## Executive diagnosis

The dominant failure was not one broken service. It was a process problem: materially different failure classes were repeatedly treated as the same retryable technical defect. That produced duplicate troubleshooting, unnecessary workflow runs, stale red history, and infrastructure work disconnected from payment.

The corrected model is documented in `ops/EXECUTION_FAILURE_GUARDRAILS.md`.

## Incident register

| Area | Failure / symptom | Root cause | Action taken | Status |
|---|---|---|---|---|
| Upwork ChatGPT connector | Account discovery identifies the single TALENT/Freelancer account, but downstream freelancer profile/financial calls reject the same context with contradictory Client/Agency/Freelancer role errors | Connector/platform role-context binding defect after successful authentication | Reproduced in-session; stop disconnect/reconnect loops; keep vendor support evidence focused on post-discovery role binding | EXTERNAL BLOCKER |
| Replit `ParchedBurlywoodMysql` | App lookup succeeds but even read-only Agent operation times out | Replit connector/Agent operation timeout, not proof of app-code failure | Reproduced in-session; no repeated Agent retries; prefer verified GitHub route | EXTERNAL BLOCKER / HOLD |
| GitHub writes to Scottcjn upstream | `Resource not accessible by integration` on upstream issue/comment/PR operations | GitHub App installation scope/permissions | Stop blind retries; preserve evidence in owned repo; use only permitted submission fallback | EXTERNAL PERMISSION BOUNDARY |
| RTC Preflight Queue | Scan and validation succeeded, then run failed during generated queue commit/rebase | Workflow self-mutated `main`, racing other automation | Removed self-commit; contents read-only; generated queue uploaded as Actions artifact | FIXED + VERIFIED GREEN 2026-09-09 |
| Agent Economy funded-job scan | Early live endpoint failures plus self-commit design | External endpoint drift plus unnecessary repository mutation | Made manual/read-only; endpoint responses captured as artifact; no self-commit | FIXED DESIGN 2026-09-09 |
| RTC Agent Jobs Snapshot | `/agent/jobs` returned live 404 despite expected upstream route | Upstream deployment/domain drift | No endless retries; noisy snapshot workflow later removed | CLOSED / EXTERNAL |
| Mesen independent reproduction | Missing `numpy`; GUI emulator launch used as version probe; legitimate benchmark mismatch caused evidence/QA steps to be skipped | Harness dependencies/environment plus incorrect failure semantics | Added dependency; removed GUI version execution; measurement may fail without suppressing evidence; QA/evidence upload always runs | PATCHED; NEW RUN NOT YET OBSERVED |
| Apify PPE QA Resume | Push automatically launched short-lived interactive OAuth device flow and failed after authorization expired | Interactive authorization incorrectly attached to unattended push trigger | Removed push trigger; manual dispatch only | FIXED DESIGN |
| Apify Device Bootstrap Deploy | Same unattended interactive OAuth pattern | Same trigger-design defect | Removed push trigger; manual dispatch only | FIXED DESIGN |
| Apify controlled deploy | Missing token fails deployment preflight | Correct authorization/configuration boundary, not a code defect | Preserve fail-closed behavior; no spend/billing/legal action without owner authorization | EXPECTED BLOCKER |
| Apify Actor Source QA | Historical source-QA failures during hardening | Source/toolchain/hash changes during active development | Current QA is deterministic/read-only, reconstructs canonical scanner, validates hash/schemas/tests/no-token source, and builds exact Docker image | CURRENT HARNESS HARDENED |
| Clawlancer readonly relay | Ordinary pushes could launch a short-lived encrypted handoff and then time out | Stateful/interactive work attached to every push | Quarantined workflow; manual-only harmless stub; original recoverable in Git history | QUARANTINED |
| Clawlancer rail validation/secret probe | Ordinary pushes could register/claim/deliver against external marketplace | Stateful commercial operation attached to every push; duplicate-operation risk | Quarantined workflow; manual-only harmless stub | QUARANTINED |
| #747 verifier CI | Multiple early failures | Workflow/security/logic defects during hardening | Later branch head completed successfully | CLOSED GREEN |
| Beacon RTC watchdog QA | Multiple early failures | Package/API mismatch during implementation | Later branch head completed successfully | CLOSED GREEN |
| RIP-302 Go client QA | Formatting/QA failure | `gofmt` ordering | Follow-up fix completed successfully | CLOSED GREEN |
| #293 Publish held RTC | Final publish step failed after evidence generation | `ffmpeg` missing on runner | Dependency added; follow-up run succeeded | CLOSED GREEN |
| 685 Rust Agent Economy SDK CI | Multiple early Rust CI failures | Rust compatibility/build hardening | Follow-up compatibility fix completed successfully | CLOSED GREEN |
| t2000 zero-cost/lifecycle | Historical `No jobs were run` | Workflow eligibility/trigger structure | Current workflows contain unconditional runner-eligible jobs and manual dispatch | STRUCTURALLY CLOSED |
| #177 recovered-assets publish | Historical verify/publish failures | Assets/workflow state changed during recovery | Current workflow is manual verification only with fixed byte counts and SHA-256 checks | CLOSED DESIGN; RUN ONLY WHEN NEEDED |
| Generic outbound validation | Activity without substantive buyer response/payment | Weak channel/offer evidence and repeated low-signal outreach | Do not expand unchanged experiment; require materially different buyer/offer/channel | COMMERCIAL TEST FAILED |
| Chargeback referral work | No attributable paid conversion | Merchant/counterparty dependency and no merchant-approved conversion | Do not count research or outreach as revenue; only continue on permission-bearing buyer signal | HOLD / MODIFY |

## Repairs made on 2026-09-09

- `ops/EXECUTION_FAILURE_GUARDRAILS.md` added as the permanent retry/failure-classification gate.
- `.github/workflows/rtc-preflight.yml` changed from self-committing generated queue files to read-only artifact output. Verification run succeeded.
- `.github/workflows/agent-economy-scan.yml` changed to manual/read-only artifact output; no repository self-commit.
- `apify-bridge-20260902:.github/workflows/apify-ppe-qa-resume.yml` changed to manual dispatch only.
- `apify-bridge-20260902:.github/workflows/apify-device-bootstrap-deploy.yml` changed to manual dispatch only.
- `bounty-16517-mesen-20260909:.github/workflows/bounty-16517-mesen.yml` hardened for dependencies, headless behavior, negative-result evidence preservation, and non-hanging binary verification.
- In `prins1bap-ui/prins1bap-ui-ardy-director`, legacy Clawlancer stateful/interactive push workflows were quarantined.

## Operating rule from this audit

Do not retry a failure merely because it is red. Retry only after identifying the exact prior failure class and a material change that makes the next attempt different.

Do not build more infrastructure merely because another integration is blocked. Revenue work must be tied to a buyer, payable bounty, or verified commercial dependency.

A successful technical task is not revenue. Only externally collected payment counts as revenue.
