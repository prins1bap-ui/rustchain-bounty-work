# Sources and contract snapshot

## Authoritative bounty

- https://github.com/Scottcjn/rustchain-bounties/issues/685
- Fetched on 2026-08-30.
- State observed: open.
- Tier 1 observed: SDK/Client Library — 50 RTC each.
- Explicit target observed: Rust client crate.
- Primary node URL observed: `https://50.28.86.131`.

## API contract copied from #685

1. `POST /agent/jobs` — post a job
2. `GET /agent/jobs` — browse jobs
3. `GET /agent/jobs/<id>` — job detail
4. `POST /agent/jobs/<id>/claim` — claim
5. `POST /agent/jobs/<id>/deliver` — deliver
6. `POST /agent/jobs/<id>/accept` — accept
7. `POST /agent/jobs/<id>/dispute` — dispute
8. `POST /agent/jobs/<id>/cancel` — cancel
9. `GET /agent/reputation/<wallet>` — reputation
10. `GET /agent/stats` — marketplace stats

The issue also gives example JSON bodies for post, claim, and deliver. It does not specify body schemas for accept, dispute, or cancel; this SDK therefore keeps those action bodies caller-controlled rather than fabricating a schema.

## Submission route

- https://github.com/Scottcjn/rustchain-bounties/blob/main/docs/HOW_TO_SUBMIT_A_BOUNTY.md
- The current guide explicitly recognizes `403 Resource not accessible by integration` for GitHub App harnesses.
- It says publishing the deliverable in a repository the contributor controls is valid for public attribution when the deliverable itself is a file/document/report.
- It explicitly accepts email to `sophia.eagent@gmail.com` with the bounty number in the subject as a fallback, including a request that the maintainer file it on the contributor's behalf.

## Safety boundary

No live POST request or fund-moving action was used to build, test, or submit this crate. Mock-server tests exercise the mutation routes without touching RustChain state.
