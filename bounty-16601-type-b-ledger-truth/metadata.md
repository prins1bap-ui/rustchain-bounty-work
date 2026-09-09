# Metadata

## Primary title
Pending Is Not Paid: How to Read RustChain Wallet State Correctly

## Alternate titles
1. RustChain Payouts Explained: Accepted vs Pending vs Confirmed
2. Stop Double-Counting RTC: A Practical Wallet-State Guide

## Description
RustChain exposes wallet transfer lifecycle state through its public wallet-history API. This explainer shows why an accepted bounty, a pending transfer, and confirmed RTC are three different accounting events, and how to build a tracker that does not double-count or prematurely call pending funds received.

Covered:
- `GET /wallet/history`
- pending vs confirmed transfer state
- accepted / queued / pending / received accounting
- transaction matching and one-time promotion
- why wallet evidence is stronger than informal payout wording for settlement state

Public source repository: https://github.com/Scottcjn/Rustchain

Author credit: @prins1bap-ui
Prepared with GPT-5.6 Sol assistance and manually constrained to public source claims.

## Chapters
00:00 Accepted is not received
00:25 Three payout events
01:05 Read wallet state, not wording
01:50 Why pending needs its own bucket
02:40 A machine-checkable workflow
03:30 Why strict accounting matters
04:15 Final rule

## Tags
RustChain, RTC, wallet, blockchain accounting, payout tracking, wallet history, Proof of Antiquity, crypto infrastructure, developer tooling, agent economy

## Thumbnail text
Primary: `PENDING ≠ PAID`
Alternate 1: `WHEN IS RTC REALLY RECEIVED?`
Alternate 2: `STOP DOUBLE-COUNTING RTC`
