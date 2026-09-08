# County Deed Extraction Pilot

A small, auditable proof-of-capability for extracting and normalizing commercial real-estate deed data from heterogeneous U.S. county public-record systems.

## What this demonstrates

- Adapter-based extraction for incompatible county recorder/assessor systems
- A single normalized output schema across sources
- Source provenance on every accepted record
- Explicit missing/unsupported fields instead of guessed values
- Retryable, restartable county-by-county execution
- Deduplication and validation hooks
- Exception reporting for counties that require a custom adapter

## Target fields

- county
- state
- deal_date
- sale_price
- mortgage_term
- property_type
- instrument_number
- parcel_id
- grantor
- grantee
- source_url
- source_system
- extraction_status
- notes

`mortgage_term` is populated only when the public source exposes enough information to support it. Missing data remains `null`.

## Architecture

The pilot separates orchestration from county-specific extraction. Each adapter converts its source into the same record model. This avoids the brittle approach of pretending 3,000 county systems share one DOM or query interface.

```text
county list
   -> adapter registry
      -> county adapter
         -> raw public record
            -> normalization
               -> validation
                  -> deduplication
                     -> structured output + exception report
```

## Safety and data-quality boundaries

This project is designed for public records. It does not bypass authentication, CAPTCHAs, access controls, or rate limits. Records with uncertain commercial-property classification or unsupported mortgage terms are flagged for review rather than inferred.

## Why this matters at national scale

The main failure mode in a multi-county scrape is silent incompleteness. A process can appear to finish while incompatible counties quietly return zero records. This pilot therefore treats per-county completion status, source provenance, and explicit exceptions as first-class output.

## Included

- `county_deed_pilot.py` — adapter/orchestration skeleton with validation and deterministic normalization
- `schema.json` — normalized output schema
- `sample_records.json` — illustrative schema examples only, clearly marked as synthetic

This portfolio sample is an engineering proof. It does not claim that all U.S. counties are already supported or that the synthetic sample rows came from live county systems.