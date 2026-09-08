# Google Apps Script + PDF Extraction Pipeline Proof

This portfolio proof demonstrates a maintainable Google Apps Script workflow for ingesting PDF-derived structured data into Google Sheets with validation, idempotency, audit fields, and carrier-specific parsing adapters.

## Why this exists

Real document automation projects usually fail in one of two ways:

1. extraction logic is tangled directly into spreadsheet writes, making every new document format risky to add;
2. reruns silently duplicate records or overwrite good data with incomplete parses.

This proof separates document-family parsing from normalization and persistence so new carriers or statement layouts can be added without rewriting the rest of the pipeline.

## Architecture

`Drive / uploaded PDF -> parser adapter -> normalized record -> validation -> idempotency check -> Google Sheet -> exception log`

The sample Apps Script implementation includes:

- a parser-registry pattern for carrier/document-specific adapters;
- normalized output fields independent of source layout;
- deterministic record keys for safe reruns;
- append-or-update behavior;
- validation before persistence;
- explicit null handling instead of guessed values;
- source file IDs and timestamps for traceability;
- separate exception logging;
- configuration kept away from core business logic.

## Files

- `Code.gs` — orchestration, normalization, validation, and Sheet persistence.
- `sample_parser.gs` — sample carrier-specific adapter using pre-extracted text blocks.
- `sample_output.json` — synthetic normalized result for demonstration.

## Production adaptation

A real deployment can plug in Google Cloud Document AI / Form Parser output, OCR text, or another extraction service. The adapter only needs to return the normalized contract expected by `Code.gs`.

That means one stable workflow can support dozens of carrier-specific statement formats while keeping QA and persistence behavior consistent.

## Portfolio integrity

This is an engineering proof, not a claim of prior paid client work. Sample data is synthetic and clearly labeled.