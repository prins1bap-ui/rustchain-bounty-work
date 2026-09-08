from datetime import date

from county_deed_pilot import (
    CountyAdapter,
    DeedRecord,
    normalize_price,
    run_adapters,
    validate_record,
)


class DemoCountyAdapter(CountyAdapter):
    county = "Demo County"
    state = "MI"
    source_system = "synthetic-fixture"

    def fetch(self, start_date: date, end_date: date):
        return [
            {
                "deal_date": "2026-01-02",
                "sale_price": "$1,250,000",
                "instrument_number": "2026-001",
                "parcel_id": "P-001",
            },
            # Intentional duplicate. The pipeline should emit it only once.
            {
                "deal_date": "2026-01-02",
                "sale_price": "$1,250,000",
                "instrument_number": "2026-001",
                "parcel_id": "P-001",
            },
        ]

    def normalize(self, raw: dict) -> DeedRecord:
        return DeedRecord(
            county=self.county,
            state=self.state,
            deal_date=raw["deal_date"],
            sale_price=normalize_price(raw["sale_price"]),
            mortgage_term=None,
            property_type="commercial",
            instrument_number=raw["instrument_number"],
            parcel_id=raw["parcel_id"],
            grantor="Synthetic Grantor LLC",
            grantee="Synthetic Buyer LLC",
            source_url="https://example.gov/records/2026-001",
            source_system=self.source_system,
            extraction_status="partial",
            notes="Synthetic fixture; mortgage term intentionally unavailable.",
        )


def test_normalize_price():
    assert normalize_price("$1,250,000") == 1_250_000.0
    assert normalize_price("N/A") is None
    assert normalize_price("not-a-price") is None


def test_validation_rejects_bad_source_url():
    record = DeedRecord(
        county="Demo County",
        state="MI",
        deal_date="2026-01-02",
        sale_price=100.0,
        mortgage_term=None,
        property_type="commercial",
        instrument_number="1",
        parcel_id="1",
        grantor=None,
        grantee=None,
        source_url="not-a-url",
        source_system="fixture",
        extraction_status="ok",
    )
    assert "invalid source_url" in validate_record(record)


def test_run_adapters_deduplicates_records():
    result = run_adapters(
        [DemoCountyAdapter()],
        date(2021, 1, 1),
        date(2026, 9, 8),
    )
    assert len(result["records"]) == 1
    assert result["records"][0]["sale_price"] == 1_250_000.0
    assert result["exceptions"] == []


def test_adapter_failure_is_isolated():
    class BrokenAdapter(CountyAdapter):
        county = "Broken County"
        state = "MI"
        source_system = "fixture"

        def fetch(self, start_date: date, end_date: date):
            raise RuntimeError("synthetic failure")

        def normalize(self, raw: dict) -> DeedRecord:
            raise AssertionError("should not be reached")

    result = run_adapters(
        [BrokenAdapter()],
        date(2021, 1, 1),
        date(2026, 9, 8),
    )
    assert result["records"] == []
    assert len(result["exceptions"]) == 1
    assert "RuntimeError" in result["exceptions"][0]["reason"]
