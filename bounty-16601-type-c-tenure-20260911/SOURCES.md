# SOURCES — Claim-by-Claim Verification

Checked 2026-09-11 against the public RustChain project surface. This package intentionally avoids market-price, profit, hashrate, or guaranteed-return claims.

## Claim 1 — RustChain uses Proof of Antiquity / hardware multipliers

Source: https://rustchain.org/

The public RustChain site describes Proof of Antiquity and lists protocol multipliers by hardware class. The short uses only the general statement that supported hardware begins with a protocol-defined base Proof-of-Antiquity weight; it does not invent a multiplier for any specific machine.

## Claim 2 — Tenure grows by +5% per year

Source: https://rustchain.org/

The public protocol description states that miners gain **+5% per year of tenure**.

## Claim 3 — Tenure bonus is capped at +50% after ten years

Source: https://rustchain.org/

The same protocol description states a **+50% cap after 10 years**. The published formula is presented as:

`tenure_formula = base * min(1.0 + 0.05 * years_mining, 1.5)`

That is the basis for the storyboard timeline and narration. No extrapolation above the stated cap is made.

## Claim 4 — Tenure operates on top of the base multiplier

Source: https://rustchain.org/

The formula above multiplies the base value by the tenure factor, supporting the script language that tenure growth is applied on top of the base multiplier.

## Claim 5 — Installation starts with `pip install clawrtc`

Source: https://rustchain.org/

The project’s public quick-start instructions use:

`pip install clawrtc`

The CTA reproduces only that installation command and points viewers back to the official documentation.

## Accuracy boundary

The package describes protocol weighting, not expected income. It contains an explicit on-screen disclosure that a protocol multiplier is not a guaranteed financial return. No third-party benchmark, token price, dollar value, earnings projection, or unverified performance figure appears in the package.