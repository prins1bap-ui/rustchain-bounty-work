# Website Contact + Tech Snapshot — $1 / 1,000 successful audits

**Enrich a public website from one lightweight HTTP request.** Submit up to 500 public HTTP/HTTPS URLs and receive one deterministic JSON record per unique URL with public contact signals, social profiles, technology fingerprints, metadata, structured-data signals, forms, redirects, server information, and common security-header presence.

Built for **lead enrichment, agency research, CRM preprocessing, technology discovery, and API/agent workflows** where a multi-page or browser crawl would add cost without being necessary.

## What you get

For every successfully fetched HTML page, the Actor returns:

- page title, meta description, canonical URL, language, and generator metadata
- Organization name and schema types found in JSON-LD where present
- public emails from visible text, `mailto:` links, and JSON-LD
- public phone signals from visible text, `tel:` links, and JSON-LD
- public social profile links for LinkedIn, Facebook, Instagram, X/Twitter, YouTube, GitHub, TikTok, Pinterest, Threads, Bluesky, and WhatsApp when present
- **45+ deterministic technology fingerprints** spanning CMS/ecommerce, front-end frameworks, analytics/ad tech, CRM/marketing/support, payment providers, and CDN/infrastructure signals
- HTML form count
- requested/final URL, redirects, HTTP status, HTTPS status, server header, content type, and bytes read
- presence/missing status for common HTTP security headers
- structured, non-billable error records for invalid, blocked, failed, oversized, timed-out, or non-HTML targets

The Actor does **not** log in, solve CAPTCHAs, bypass access controls, crawl private networks, or claim to reveal technologies that are not observable from the returned homepage response.

## Input

```json
{
  "urls": [
    "https://example.com",
    "https://www.example.org"
  ],
  "timeoutSeconds": 10,
  "maxRetries": 1
}
```

Duplicate normalized URLs are processed only once per run. Private, loopback, link-local, reserved, and other non-public network targets are rejected. Redirect destinations are checked using the same public-network rule.

## Output example

```json
{
  "requestedUrl": "https://example.com",
  "normalizedUrl": "https://example.com/",
  "finalUrl": "https://example.com/",
  "statusCode": 200,
  "redirectCount": 0,
  "status": "SUCCESS",
  "errorCode": null,
  "errorMessage": null,
  "title": "Example Domain",
  "metaDescription": null,
  "generator": null,
  "language": "en",
  "canonicalUrl": null,
  "organizationName": null,
  "structuredDataTypes": [],
  "detectedTechnologies": [],
  "forms": 0,
  "emails": [],
  "phones": [],
  "socialProfiles": {},
  "https": true,
  "server": null,
  "contentType": "text/html",
  "bytesRead": 1256,
  "securityHeadersPresent": [],
  "securityHeadersMissing": [
    "strict-transport-security",
    "content-security-policy",
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "permissions-policy"
  ]
}
```

## Pricing

**Planned launch price: $0.001 per successful website audit ($1.00 per 1,000).**

A custom `website-audit` Pay-Per-Event event is intended to be charged only after a unique URL returns a successful HTML audit record. Invalid URLs, private-network targets, DNS/network failures, HTTP errors, unsupported content types, timeouts, and oversized responses are intended to remain uncharged.

The price shown in Apify Console is authoritative. Monetization configuration must be verified there before Store publication.

## Accuracy and limitations

This is an evidence-based snapshot, not a full crawler or a BuiltWith-style historical database. Technology detection uses fingerprints observable in the returned HTML. It may miss server-side, dynamically injected, deliberately hidden, or page-specific technologies. A matching asset or string can occasionally create a false positive.

Contact extraction is limited to the fetched page in this validation version. It does not follow contact/about/team pages. JavaScript-only content may not be visible because the Actor deliberately uses a standard HTTP request rather than a browser.

## Reliability and safety controls

- URL normalization and per-run deduplication
- maximum 500 URLs per run
- 3–20 second configurable timeout
- up to two retries for transient failures
- 1.5 MB response cap
- HTML content-type checks
- localhost/private/reserved/non-global network blocking before requests and redirects
- deterministic output shape for success and error records
- no OpenAI or other paid third-party API dependency

## Responsible use

Only submit websites you are authorized to access. The Actor reads publicly returned web content and does not bypass authentication or technical access restrictions. You are responsible for applicable website terms, privacy law, anti-spam rules, and downstream use of exported contact information.

## API and automation

As an Apify Actor, this tool is intended to be callable through Apify's API and automation ecosystem. Its explicit input, dataset, and output schemas are designed for predictable machine-to-machine use.

## Validation-stage disclosure

This Actor is in paid-validation stage. No accuracy percentage, savings claim, customer-result claim, or demand claim is made without supporting evidence. The initial experiment measures actual paid usage rather than downloads, page views, or free runs.
