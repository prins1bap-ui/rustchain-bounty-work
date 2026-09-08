from __future__ import annotations

from dataclasses import asdict
from datetime import date
import json
from typing import Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from county_deed_pilot import CountyAdapter, DeedRecord, normalize_price


class NycAcrisAdapter(CountyAdapter):
    """Live public-source adapter for NYC ACRIS Real Property Master.

    NYC Open Data dataset: bnx9-e6tj
    Source agency: NYC Department of Finance

    This adapter intentionally uses the public Socrata API and does not bypass
    authentication, CAPTCHA, access controls, or non-public systems.
    """

    county = "New York City"
    state = "NY"
    source_system = "NYC ACRIS / NYC Open Data"
    dataset_id = "bnx9-e6tj"
    endpoint = f"https://data.cityofnewyork.us/resource/{dataset_id}.json"

    borough_names = {
        "1": "New York (Manhattan)",
        "2": "Bronx",
        "3": "Kings (Brooklyn)",
        "4": "Queens",
        "5": "Richmond (Staten Island)",
    }

    def __init__(self, limit: int = 100):
        if limit < 1 or limit > 50000:
            raise ValueError("limit must be between 1 and 50000")
        self.limit = limit

    def fetch(self, start_date: date, end_date: date) -> Iterable[dict]:
        # ACRIS uses doc_date. Restrict to deed-like records and a bounded
        # date window. The adapter keeps the query simple and auditable.
        start = start_date.isoformat() + "T00:00:00.000"
        end = end_date.isoformat() + "T23:59:59.999"
        where = (
            f"doc_date between '{start}' and '{end}' "
            "and doc_type in ('DEED','RPTT&RET')"
        )
        params = {
            "$limit": str(self.limit),
            "$order": "doc_date DESC",
            "$where": where,
        }
        request = Request(
            self.endpoint + "?" + urlencode(params),
            headers={"User-Agent": "county-deed-pilot/1.0"},
        )
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def normalize(self, raw: dict) -> DeedRecord:
        borough_code = str(raw.get("borough") or "").strip()
        county = self.borough_names.get(borough_code, f"NYC borough {borough_code or 'unknown'}")
        doc_id = raw.get("document_id") or raw.get("crfn")
        amount = raw.get("document_amt") or raw.get("doc_amount")

        return DeedRecord(
            county=county,
            state="NY",
            deal_date=(raw.get("doc_date") or "")[:10] or None,
            sale_price=normalize_price(amount),
            mortgage_term=None,
            property_type=None,
            instrument_number=str(doc_id) if doc_id else None,
            parcel_id=None,
            grantor=None,
            grantee=None,
            source_url=(
                "https://data.cityofnewyork.us/City-Government/"
                "ACRIS-Real-Property-Master/bnx9-e6tj"
            ),
            source_system=self.source_system,
            extraction_status="partial",
            notes=(
                "Live official ACRIS master record. Parcel, parties, commercial/land "
                "classification, and mortgage-term enrichment require joins to the "
                "official ACRIS Legals/Parties datasets and property classification data."
            ),
        )


if __name__ == "__main__":
    adapter = NycAcrisAdapter(limit=10)
    rows = adapter.fetch(date(2026, 1, 1), date.today())
    print(json.dumps([asdict(adapter.normalize(row)) for row in rows], indent=2))
