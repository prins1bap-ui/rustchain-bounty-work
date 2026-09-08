# Upwork Proposal Notes — Google Apps Script / GCP PDF Scraping

Target posting: `Google Apps Script / GCP Automation: PDF Scraping` — $500 fixed price.

## Client problem

The core challenge is not extracting one statement. It is building a maintainable carrier-by-carrier parsing system that can safely process changing document batches, avoid duplicate writes, and make failures visible.

## Proposed architecture

- One carrier-specific parser/normalizer module per stable statement layout.
- Google Apps Script orchestration for Drive/Sheets workflow.
- GCP Form Parser / document extraction where appropriate.
- Deterministic statement keys to prevent duplicate processing.
- Explicit validation and exception logging.
- Safe reruns with processed-record tracking.
- Structured output into Google Sheets with source/document traceability.
- Parser registry so the ~30–40 carrier formats can be added incrementally without rewriting the workflow.
- Clear handling of unsupported or low-confidence fields rather than guessing.

## Recommended delivery sequence

1. Implement one representative carrier end-to-end.
2. Validate field mapping and output schema with the client.
3. Add shared orchestration, deduplication, exception reporting, and rerun safety.
4. Expand the parser registry across remaining carriers.
5. Deliver concise setup/maintenance documentation.

## Portfolio evidence

This directory demonstrates the intended structure: carrier-specific parsing adapters, deterministic keys, validation, safe reruns, exception logging, and synthetic sample output. It is an engineering proof, not a fabricated prior client engagement.

## Proposal draft

The scalable part of this job is not the first PDF parser. It is making carrier #2 through carrier #40 cheap and predictable to add without breaking the workflow.

I would structure the system around a shared Apps Script orchestration layer plus one small parser/normalizer per carrier format. Each statement gets a deterministic key so reruns do not create duplicate rows, parse failures are logged explicitly, and unsupported fields remain blank/flagged rather than guessed. GCP Form Parser can handle document extraction where it adds value, while the Apps Script layer handles Drive/Sheets workflow, validation, and output.

I have already prepared an inspectable proof around this architecture, including carrier-specific parser adapters, validation, duplicate protection, safe reruns, exception logging, and synthetic sample output.

I would start with one representative carrier, confirm the exact field mapping with you, then scale the same pattern across the remaining ~30–40 statement formats. I can work within the posted $500 fixed-price scope, subject to the final field list and document-access requirements.
