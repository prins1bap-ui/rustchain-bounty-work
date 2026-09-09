# Storyboard — Pending Is Not Paid

Format: 16:9 YouTube explainer, 4–5 minutes. No third-party stock media required. All shots can be captured from public RustChain GitHub pages, terminal/API output, or simple original diagrams.

## Shot 1 — 0:00–0:12
Visual: Large on-screen words appear one at a time: `ACCEPTED` → `PENDING` → `CONFIRMED`.
Overlay: “These are not the same state.”

## Shot 2 — 0:12–0:25
Visual: Original three-column ledger mockup labeled Accepted / Pending / Received. A 28 RTC card moves only into Pending.
Overlay: “Do not count it twice.”

## Shot 3 — 0:25–0:45
Visual: Public RustChain repository README in browser. Slow crop over the project title and live explorer/wallet references.
Capture note: use only the public repository page.

## Shot 4 — 0:45–1:05
Visual: Original pipeline diagram:
`Bounty accepted → payout queued → wallet pending → wallet confirmed`.
Animate arrows left to right.

## Shot 5 — 1:05–1:28
Visual: Public `docs/WALLET_TRANSFER_STATE_GUIDE.md` page. Highlight the wallet-history section and the documented lifecycle statuses.
Overlay: `GET /wallet/history`.

## Shot 6 — 1:28–1:50
Visual: Terminal capture of a read-only example request to the public wallet-history endpoint using a placeholder wallet ID. Blur or omit unrelated data.
Overlay: “Wallet state beats wording for settlement.”

## Shot 7 — 1:50–2:15
Visual: Split screen. Left: generic message bubble saying “Paid.” Right: JSON-style record showing `status: pending`.
Overlay: “Intent ≠ settlement.”

## Shot 8 — 2:15–2:40
Visual: Four ledger buckets appear: SUBMITTED, ACCEPTED, PENDING_ON_CHAIN, RECEIVED. A single payment token progresses through the buckets without duplication.

## Shot 9 — 2:40–3:05
Visual: Checklist animation:
1. Record bounty + amount
2. Query wallet history
3. Match transfer identifiers
4. Preserve pending state
5. Promote once on confirmation

## Shot 10 — 3:05–3:30
Visual: Close crop on transaction-hash and status fields in a synthetic JSON example. Use obviously fictional hashes, not a real user wallet.
Overlay: “One transfer. One lifecycle state.”

## Shot 11 — 3:30–3:55
Visual: Public RustChain README section on hardware verification / machine-checkable evidence, then dissolve back to the wallet-state pipeline.
Narrative bridge: verification philosophy applied to accounting.

## Shot 12 — 3:55–4:20
Visual: Four question cards:
“What did I submit?”
“What was accepted?”
“What is pending?”
“What is confirmed?”
Each maps to one ledger stage.

## Shot 13 — 4:20–end
Visual: Final title card.
Text: “Accepted is a decision. Pending is in flight. Confirmed is received.”
Subtext: “Source-grounded RustChain accounting.”

## Production notes
- Use original diagrams and typography only.
- No music is required; if Elyan adds music, use properly licensed or original audio.
- Do not show private email, private wallet credentials, secrets, or private GitHub data.
- API captures should be read-only and use public documentation or placeholder identifiers where possible.
