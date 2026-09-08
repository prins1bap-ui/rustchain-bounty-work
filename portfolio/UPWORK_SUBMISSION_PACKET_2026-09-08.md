# Upwork Submission Packet — 2026-09-08

## Priority 1: $2,000 public-record data extraction

Listing: https://www.upwork.com/freelance-jobs/apply/Scrapping-Data_~022096300324827683967/

Public state verified 2026-09-08: $2,000 fixed price, worldwide, 20–50 proposals, 0 interviewing, 0 invites.

### Cover letter

The hard part is not extracting one county. It is preventing silent gaps across thousands of incompatible county recorder and assessor systems.

I’ve already built the extraction architecture around that problem, including a live official-source adapter for NYC ACRIS/Open Data. The framework normalizes records into one schema, preserves source provenance, deduplicates results, isolates county-specific failures, and explicitly flags unsupported fields instead of guessing.

For your scope, I would start with a representative pilot across materially different county systems, validate the commercial-property and land filters, then scale the proven adapters across the remaining sources. The output can include transaction date, price, available financing details, property/document identifiers, county, source URL, and an exception report for unsupported or inaccessible fields.

I can complete the posted scope for the $2,000 fixed price, subject to final output and county-access requirements.

Proof:
- portfolio/county_deed_pilot/nyc_acris_adapter.py
- portfolio/county_deed_pilot/county_deed_pilot.py
- portfolio/county_deed_pilot/schema.json
- portfolio/county_deed_pilot/LIVE_SOURCE_NOTES.md

Bid settings: $2,000 fixed; no boost by default; no extra Connects purchase without explicit approval.

## Priority 2: $500 Google Apps Script / GCP PDF extraction

Listing: https://www.upwork.com/freelance-jobs/apply/Google-Apps-Script-GCP-Automation-PDF-Scraping_~022095733507643556934/

### Cover letter

Your main scaling risk is not writing one parser. It is keeping 30–40 document-specific parsers consistent, restartable, and safe to rerun as layouts change.

I’ve built a proof implementation for that architecture in Google Apps Script: a parser registry, normalized output schema, validation before persistence, deterministic record keys for idempotent reruns, append-or-update behavior in Google Sheets, and a separate exception log. The pipeline is designed so Google Cloud Document AI/Form Parser output, OCR text, or another extraction service can feed the same normalized record layer.

That structure lets each parser stay small while validation, persistence, retry, and exception logic remains shared. I can implement the requested workflow for the posted $500 fixed price, assuming the final document layouts and GCP project access are provided.

Proof:
- portfolio/apps_script_pdf_pipeline/README.md
- portfolio/apps_script_pdf_pipeline/Code.gs
- portfolio/apps_script_pdf_pipeline/sample_parser.gs
- portfolio/apps_script_pdf_pipeline/sample_output.json

Bid settings: $500 fixed; no boost by default; no extra Connects purchase without explicit approval.

## Final submission checklist

Before submission verify invitations, existing proposal status, exact Connects cost, current Connects balance, final bid, attachments, and any authenticated screening questions. A proposal counts only after Upwork confirms submission.
