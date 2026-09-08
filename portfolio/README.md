# Upwork Portfolio Proof Index

This branch contains small, inspectable engineering proofs intended to support proposals for scraping, data extraction, workflow automation, and structured-data work.

## 1. County Deed Extraction Pilot

Path: `portfolio/county_deed_pilot/`

Demonstrates an adapter-based public-record extraction architecture for heterogeneous U.S. county systems, with normalized schema, source provenance, validation, deduplication, restartability, and explicit exception reporting.

Best fit:
- commercial real-estate deed extraction
- public-record research
- multi-source scraping
- large structured datasets

## 2. Google Apps Script + PDF Extraction Pipeline

Path: `portfolio/apps_script_pdf_pipeline/`

Demonstrates a document-family adapter architecture for Google Apps Script workflows that ingest PDF-derived structured data into Google Sheets with deterministic record keys, safe reruns, validation, exception logging, source traceability, and explicit null handling.

Best fit:
- Google Apps Script automation
- PDF/document extraction
- Google Sheets workflows
- Google Cloud Document AI / Form Parser integrations
- repetitive statement processing

## 3. Website Contact + Tech Snapshot Actor

Existing project path on branch `apify-bridge-20260902`: `apify_actor/`

Demonstrates deterministic website extraction and enrichment, structured JSON output, public contact discovery, technology fingerprints, retries/timeouts, and safe handling of inaccessible/private targets.

Best fit:
- Apify
- web scraping
- website enrichment
- public contact and technology datasets

## Portfolio integrity

These samples are engineering proofs, not fabricated client projects. Synthetic fixtures are labeled as synthetic. No claim is made that every target source, county, carrier, or vendor system is already supported.