# Upwork Proposal Notes — Commercial Real-Estate Deed Extraction

Target posting: `Scrapping Data` — $2,000 fixed price.

## Client problem

The difficult part is not scraping one county site. It is preventing silent coverage gaps across thousands of incompatible recorder/assessor systems while keeping the result auditable.

## Proposed architecture

- County/vendor adapters behind one normalized schema.
- Five-year date-window filtering.
- Commercial/land classification rules validated in a pilot before scale-out.
- Deal date and sale price normalized into structured fields.
- Mortgage term captured only when the public source actually exposes it; otherwise explicit null/exception status.
- Stable deduplication across instrument number, parcel, date, and price.
- Source URL and source-system provenance retained per record.
- Per-county status and exception reporting so unsupported counties are visible rather than silently skipped.
- Restartable batches and isolated adapter failures.

## Recommended pilot

Start with a small representative set of counties using materially different public-record systems. Validate:

1. source access pattern;
2. commercial/land filtering;
3. schema completeness;
4. duplicate handling;
5. sale-price normalization;
6. mortgage-term availability;
7. source provenance;
8. failure/exception reporting.

Only after the pilot is accepted should the adapter library be expanded across recurring vendor platforms and county-specific outliers.

## Portfolio evidence

This directory contains an inspectable adapter interface, normalized record model, validation, deduplication, failure isolation, explicit synthetic fixtures, and deterministic QA tests. It is an engineering proof, not a fabricated prior client engagement.

## Proposal draft

Your main risk is not scraping one county. It is getting consistent, auditable results across thousands of incompatible recorder and assessor systems without silently skipping unsupported counties.

I would build this as a restartable public-records pipeline with county/vendor adapters behind one normalized schema. Each accepted record retains its source URL and extraction status, duplicate records are removed deterministically, and fields such as mortgage term are left explicitly unavailable when the public source does not expose them rather than being guessed.

I have already prepared an inspectable engineering proof around that architecture: normalized deed records, validation, deduplication, per-county failure isolation, source provenance, exception reporting, and deterministic QA tests.

I would begin with a representative pilot across several materially different county systems, validate the commercial/land filters and output schema with you, then scale the proven adapters. I can complete the posted scope for the $2,000 fixed price, subject to the final county-access and output requirements.
