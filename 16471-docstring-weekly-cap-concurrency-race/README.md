# RustChain #16471 finding: per-issue concurrency lets simultaneous docstring claims overrun the weekly cap

Current sources:
- `scripts/docstring_gate.py`
- `.github/workflows/docstring-gate.yml`

The weekly cap is enforced with a non-atomic read-then-approve sequence. `docstring_rtc_this_week(author)` reads already verified grants; only later does the current run apply `bounty-eligible` and `docstring-verified`. There is no contributor-scoped lock or atomic reservation.

The workflow concurrency key is `docstring-gate-${{ github.event.issue.number || github.run_id }}`. Two issue-event runs for two different claim numbers therefore have different concurrency groups and may run at the same time even when both claims belong to the same contributor.

Concrete wrong-effect path:

1. Contributor has 30 RTC of docstring grants in the rolling window.
2. Two separate merged-PR claims are adjudicated concurrently; each is worth 10 RTC.
3. Run A reads `already = 30`. Run B independently reads `already = 30` before either run publishes its verification labels/marker.
4. Each evaluates `30 + 10 > 40` as false and proceeds to the eligible branch.
5. Both runs apply `docstring-verified` and queue 10 RTC, leaving 50 RTC verified inside a nominal 40 RTC/week ceiling. Both runs can exit successfully and no lookup failed.

This is distinct from the existing weekly-cap findings involving API failure, issue creation time, and untrusted payout markers. Here all data is valid and trusted; the invariant fails because the check and reservation are not serialized.

Suggested remediation: serialize cap decisions per contributor or persist an atomic reservation/ledger update before marking a claim payable. A contributor-scoped concurrency group is the simplest workflow-level guard for event-driven runs, though the durable invariant should ideally live in an atomic payout ledger.

`repro.py` models two simultaneous 10 RTC decisions from the same 30 RTC starting state and shows both approve, ending at 50 RTC.
