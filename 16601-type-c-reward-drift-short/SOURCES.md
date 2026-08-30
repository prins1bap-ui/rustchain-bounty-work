# Source map

Every factual claim in this package maps to a public source below.

## Claim: issue #13226 currently shows 7 RTC in the title and 10 RTC in the body

Public issue:
https://github.com/Scottcjn/rustchain-bounties/issues/13226

Current title:
`[BOUNTY: 7 RTC] Add an llms.txt + GEO entity profile to a RustChain ecosystem repo`

Current body opening:
`## Bounty: GEO/AEO optimization — **10 RTC**`

## Claim: the Bounty Spec Linter detects title/body reward drift and other metadata inconsistencies

Project README:
https://github.com/prins1bap-ui/rustchain-bounty-work/blob/main/402-bounty-spec-linter/README.md

Implementation:
https://github.com/prins1bap-ui/rustchain-bounty-work/blob/main/402-bounty-spec-linter/bounty_spec_linter.py

Tests:
https://github.com/prins1bap-ui/rustchain-bounty-work/blob/main/402-bounty-spec-linter/tests/test_linter.py

The published implementation contains checks for:
- `TITLE_BODY_REWARD_DRIFT`
- `AGENT_MANIFEST_REWARD_DRIFT`
- `MISSING_BOUNTY_LABEL`
- `MISSING_REWARD`
- `STATE_TEXT_DRIFT`

## Claim: the tool is read-only and does not execute payouts or wallet actions

Safety statement:
https://github.com/prins1bap-ui/rustchain-bounty-work/blob/main/402-bounty-spec-linter/README.md

The README states that the tool uses public GET requests only and performs no comments, edits, wallet actions, transfers, signatures, payments, or security testing.

## Claim: RustChain maintainer greenlit this linter concept as a Builder-tier micro-grant

Maintainer comment:
https://github.com/Scottcjn/rustchain-bounties/issues/402#issuecomment-5469209687

The maintainer described the Bounty Spec Linter + Reward Drift Detector as automating adjudication and reward-consistency checking otherwise done by hand.

## Editorial constraint

The Short must not represent issue #13226’s conflicting 7/10 RTC figures as a paid amount, nor represent the linter as automatically resolving or changing payouts.
