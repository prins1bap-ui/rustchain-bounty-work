# Freelancer.com Bid Bridge

Purpose: submit lawful Freelancer.com bids through the official API without browser automation.

## Current target

- Project: Marketplace OEM Part Verification
- Project ID: `40688162`
- Public budget: `₹10,000-20,000 INR`
- Status checked 2026-09-07: open for bidding
- Deliverable: verify missing OEM vehicle-part numbers from marketplace URLs, return structured results with source-of-truth notes and evidence where available.
- Acceptance target: at least 95% of the batch should clear random spot-checks without correction.
- Prepared proposal: `ops/freelancer_oem_part_verification_bid.txt`

## Security and spend controls

- Uses Freelancer's official Python SDK only.
- Requires `FLN_OAUTH_TOKEN` in the environment. Never commit the token.
- `FLN_URL` is optional and defaults to production Freelancer.com.
- The bridge is read-only unless `--submit` is explicitly supplied.
- No browser automation, cookie extraction, paid membership purchase, or third-party credits are used.

## Install

```bash
python -m pip install -r ops/freelancer_requirements.txt
```

## Authenticated preflight, no bid

```bash
export FLN_OAUTH_TOKEN='...'
python ops/freelancer_bid_bridge.py \
  --project-id 40688162 \
  --amount 15000 \
  --period 4 \
  --milestone-percentage 100 \
  --description-file ops/freelancer_oem_part_verification_bid.txt
```

A successful preflight must print `DRY_RUN_OK`. It resolves the authenticated Freelancer identity and target project but does not place a bid.

## Submit

Only after the authenticated preflight succeeds:

```bash
python ops/freelancer_bid_bridge.py \
  --project-id 40688162 \
  --amount 15000 \
  --period 4 \
  --milestone-percentage 100 \
  --description-file ops/freelancer_oem_part_verification_bid.txt \
  --submit
```

The chosen ₹15,000 bid sits at the midpoint of the posted ₹10,000-20,000 range. The 4-day delivery period is deliberately conservative because the client has not disclosed the spreadsheet row count yet. If the API reports the project closed or rejects the bid, do not retry blindly; preserve the exact API error and move to the next qualified opportunity.
