# Publication metadata

## Primary title

**Queued Is Not Confirmed: Reading RustChain’s Payout Ledger Correctly**

## Alternate titles

- **RustChain Payments Have 4 States. Here’s Why That Matters.**
- **Approved, Pending, Confirmed: Stop Mixing These Up**

## Description

RustChain’s public bounty payout ledger defines four separate settlement states: Queued, Pending, Confirmed, and Voided. This source-backed explainer walks through those definitions, shows a real void-and-reissue example from the ledger, and explains a simple accounting rule: never report a payment at a stronger state than the evidence supports.

Public source:
https://github.com/Scottcjn/rustchain-bounties/issues/104

Script/storyboard package by `@prins1bap-ui`.

This is an accounting/status explainer. It does not execute transactions, instruct viewers to move funds, or claim that any individual reward is spendable.

## Chapters

00:00 One reward, four different states
00:20 The public payout ledger
00:50 What Queued means
01:20 What Pending means
01:55 What Confirmed means
02:25 Why Voided matters
02:55 What evidence belongs in a payout update
03:25 Three bookkeeping mistakes status separation prevents
04:05 The evidence-first state model

## Suggested tags

`RustChain`, `open source`, `blockchain`, `developer tooling`, `accounting`, `bounty`, `GitHub`, `AI agents`, `transparency`

## Thumbnail concept

Large center text: **QUEUED ≠ CONFIRMED**

Below it, four compact status pills:
`QUEUED | PENDING | CONFIRMED | VOIDED`

Background: cropped public issue #104 status-definition section, blurred enough to remain secondary but recognizable as GitHub documentation.

No dollar values or unverified RTC-to-USD conversion on the thumbnail.

## Author credit

`@prins1bap-ui`
