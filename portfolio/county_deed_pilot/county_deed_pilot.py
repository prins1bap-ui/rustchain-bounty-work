from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from typing import Iterable, Optional


@dataclass(frozen=True)
class DeedRecord:
    county: str
    state: str
    deal_date: Optional[str]
    sale_price: Optional[float]
    mortgage_term: Optional[str]
    property_type: Optional[str]
    instrument_number: Optional[str]
    parcel_id: Optional[str]
    grantor: Optional[str]
    grantee: Optional[str]
    source_url: str
    source_system: str
    extraction_status: str
    notes: Optional[str] = None


class CountyAdapter:
    """Base interface for one county/public-record system adapter."""

    county: str
    state: str
    source_system: str

    def fetch(self, start_date: date, end_date: date) -> Iterable[dict]:
        raise NotImplementedError

    def normalize(self, raw: dict) -> DeedRecord:
        raise NotImplementedError


def normalize_price(value) -> Optional[float]:
    if value in (None, "", "N/A", "NA"):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def validate_record(record: DeedRecord) -> list[str]:
    issues: list[str] = []
    if not record.county:
        issues.append("missing county")
    if not record.state:
        issues.append("missing state")
    if not record.source_url.startswith(("http://", "https://")):
        issues.append("invalid source_url")
    if record.sale_price is not None and record.sale_price < 0:
        issues.append("negative sale_price")
    if record.extraction_status not in {"ok", "partial", "needs_review", "unsupported"}:
        issues.append("invalid extraction_status")
    return issues


def record_key(record: DeedRecord) -> tuple:
    """Stable deduplication key that avoids relying on a single field."""
    return (
        record.state.lower(),
        record.county.lower(),
        (record.instrument_number or "").lower(),
        (record.parcel_id or "").lower(),
        record.deal_date or "",
        record.sale_price,
    )


def run_adapters(adapters: Iterable[CountyAdapter], start_date: date, end_date: date):
    records: list[dict] = []
    exceptions: list[dict] = []
    seen: set[tuple] = set()

    for adapter in adapters:
        try:
            raw_rows = adapter.fetch(start_date, end_date)
            county_count = 0
            for raw in raw_rows:
                record = adapter.normalize(raw)
                issues = validate_record(record)
                if issues:
                    exceptions.append({
                        "county": adapter.county,
                        "state": adapter.state,
                        "reason": "; ".join(issues),
                        "source_system": adapter.source_system,
                    })
                    continue

                key = record_key(record)
                if key in seen:
                    continue
                seen.add(key)
                records.append(asdict(record))
                county_count += 1

            if county_count == 0:
                exceptions.append({
                    "county": adapter.county,
                    "state": adapter.state,
                    "reason": "adapter completed with zero accepted records; verify source/result window",
                    "source_system": adapter.source_system,
                })

        except Exception as exc:  # adapter failures are isolated per county
            exceptions.append({
                "county": getattr(adapter, "county", "unknown"),
                "state": getattr(adapter, "state", "unknown"),
                "reason": f"adapter failure: {type(exc).__name__}: {exc}",
                "source_system": getattr(adapter, "source_system", "unknown"),
            })

    return {"records": records, "exceptions": exceptions}


if __name__ == "__main__":
    # Intentionally no live scraping in this portfolio entry. County adapters
    # should be added only after reviewing each public system's access pattern,
    # terms, rate limits, and data fields.
    result = run_adapters([], date(2021, 1, 1), date.today())
    print(result)
