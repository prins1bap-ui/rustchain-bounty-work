# RustChain Bounty Spec Linter + Reward Drift Detector

Read-only, zero-dependency Python CLI for detecting inconsistent RustChain bounty metadata before payout ambiguity reaches contributors.

## Detects
- title vs body RTC reward mismatch
- live issue vs `agent.json` featured-bounty payout mismatch
- missing bounty labels
- missing parseable RTC rewards
- stale open/closed wording

## Usage

```bash
python bounty_spec_linter.py issue 13226
python bounty_spec_linter.py --format json issue 13226
python bounty_spec_linter.py scan --limit 100
```

Offline fixtures:

```bash
python bounty_spec_linter.py --agent-json tests/fixture_agent.json issue 13226 --issue-json tests/fixture_issue_13226.json
```

## Tests

```bash
python -m unittest discover -s tests -v
```

Exit code 2 means error-severity drift was detected. Exit code 0 means no error-severity finding.

## Safety
Public GET requests only. No comments, edits, wallet actions, transfers, signatures, payments, or security testing.

## Origin
Built as the greenlit Builder-tier deliverable for Scottcjn/rustchain-bounties issue #402 by `@prins1bap-ui`.
