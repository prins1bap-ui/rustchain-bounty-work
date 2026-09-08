# Live Source Pilot: NYC ACRIS

This portfolio proof now includes a source-specific adapter for an official public real-estate recording system rather than only synthetic fixtures.

## Official source

NYC Department of Finance maintains the Automated City Register Information System (ACRIS). NYC states that ACRIS provides access to recorded real-property documents including deeds and mortgages, and that records for Manhattan, Queens, Bronx, and Brooklyn are available online from 1966 to the present. NYC Open Data publishes ACRIS datasets for large-scale structured access.

Primary structured dataset used here:

- **ACRIS - Real Property Master**
- NYC Open Data dataset ID: `bnx9-e6tj`
- Provider: NYC Department of Finance
- Public dataset page: `https://data.cityofnewyork.us/City-Government/ACRIS-Real-Property-Master/bnx9-e6tj`

Related official datasets useful for enrichment:

- Real Property Legals: `8h5j-fqxa`
- Real Property Parties: `636b-3b5g`
- Real Property References: `pwkr-dpni`
- Document Control Codes: `7isb-wh4c`

## What the adapter demonstrates

`nyc_acris_adapter.py` queries the public Socrata endpoint with a bounded date window and deed-like document types, then normalizes the returned source records to the project schema.

The adapter demonstrates:

- a real source-specific implementation;
- bounded, restartable extraction;
- use of an official public API rather than screen scraping when a structured endpoint exists;
- source provenance on every normalized record;
- explicit partial status when requested fields require additional joins;
- no guessing of mortgage terms, parcel attributes, or party identities;
- no CAPTCHA, authentication, or access-control bypass.

## Commercial / land filtering

The Upwork target specifically requests commercial real-estate and land deals. ACRIS master records alone are not sufficient to make that classification reliably. A production implementation should join master records to official legal/parcel data and an authoritative property-classification source, then apply deterministic inclusion rules. Records that cannot be classified confidently should be marked `needs_review`, not silently included.

## Mortgage term

Mortgage term should only be populated where an official public record exposes enough information to derive it reliably. The current master adapter intentionally returns `null` for mortgage term because inventing a value from incomplete public fields would make the dataset look complete while being wrong.

## Why this matters for a multi-county project

The useful pattern is not 'one scraper per county forever.' It is:

1. identify the county's recorder/assessor platform or official data endpoint;
2. use a reusable adapter for common vendor systems where possible;
3. normalize into one schema;
4. retain source evidence;
5. isolate failures by county;
6. explicitly surface unsupported or missing fields;
7. add outlier adapters only where needed.

That architecture scales materially better than a monolithic scraper and makes silent coverage gaps easier to detect.
