# Storyboard — “Queued Is Not Confirmed”

Target: 16:9 YouTube explainer, approximately 4–5 minutes. Every factual screen should show or link the public RustChain source instead of relying on decorative claims.

## 0:00–0:20 — The bookkeeping shortcut

**Narration:** opening paragraph about a bounty being approved, marked queued, and then casually treated as arrived.

**Visual:** four large status cards animate onto screen: `QUEUED`, `PENDING`, `CONFIRMED`, `VOIDED`. Briefly blur them together, then separate them.

**On-screen text:** `These are different states.`

No wallet balance or payment amount should be fabricated for this opener.

## 0:20–0:50 — Source of truth

**Visual:** browser capture of public RustChain bounty issue #104. Frame the title:

`[LEDGER] Bounty Payout Ledger — Queued / Pending / Confirmed`

Then move to the “Status Definitions” section.

**Callout:** `Public payout ledger • issue #104`

## 0:50–1:20 — Queued

**Visual:** highlight the published definition of `Queued`.

Animated flow:

`APPROVED` → `TRANSFER SUBMITTED` → `QUEUED`

Stop the arrow there. Do not animate directly to confirmed.

**On-screen text:** `Queued ≠ Confirmed`

## 1:20–1:55 — Pending

**Visual:** highlight the `Pending` definition and one public pending ledger row containing a Pending ID and Tx Hash.

Create a simple 24-hour timeline graphic labeled only as the ledger’s published “24h pending window.”

**On-screen text:** `Evidence gets more specific: Pending ID + Tx Hash`

Do not claim the example transaction is currently still pending; describe it as a ledger example.

## 1:55–2:25 — Confirmed

**Visual:** highlight the `Confirmed` definition, then show one historical row already labeled Confirmed.

Flow graphic now extends:

`QUEUED` → `PENDING` → `CONFIRMED`

**On-screen text:** `Pending window passed • transfer confirmed`

## 2:25–2:55 — Voided and reissued

**Visual:** use the two public BoTTube ledger rows for `BoozeLee` / `boozelee`.

Show:

`Pending ID 27` → `VOIDED: wrong casing`

then a separate arrow:

`reissued` → `Pending ID 29`

**On-screen text:** `Submitted does not guarantee the same transfer confirms.`

Keep wallet strings visible only if captured directly from the public ledger.

## 2:55–3:25 — What a payout update should contain

**Visual:** highlight the operational note listing:
- bounty reference
- wallet
- amount
- pending ID
- tx hash

Animate those five fields into an evidence card.

Secondary callout: `Pending confirmations are processed hourly` with the source line visible.

## 3:25–4:05 — Three bookkeeping failures

Use three clean cards:

1. `DOUBLE COUNTING`
   Visual: one reward duplicated across queued/pending/confirmed columns, then collapsed back into one lifecycle.

2. `PREMATURE SUCCESS`
   Visual: “Approved” stamp prevented from jumping straight to “Confirmed.”

3. `LOST EXCEPTIONS`
   Visual: void/reissue branch remains visible.

These are explanatory consequences derived from keeping the ledger states distinct, not claims that RustChain has committed these mistakes.

## 4:05–4:35 — The model

Full-screen state diagram:

`QUEUED → PENDING → CONFIRMED`

with a branch from pre-confirmation states to:

`VOIDED`

Narration gives the rule: report the strongest state the evidence actually supports, and no stronger.

## 4:35–4:50 — End card

**Text:**

`Never promote a payment beyond the evidence.`

Footer:
`Source: RustChain public payout ledger #104`
`Script + storyboard: @prins1bap-ui`

No transaction signing, wallet action, transfer tutorial, or payment execution is shown anywhere in this production.
