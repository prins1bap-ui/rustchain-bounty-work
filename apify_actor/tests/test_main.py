import asyncio
import importlib
import sys
import types
from decimal import Decimal

import pytest


class _Log:
    def __init__(self):
        self.messages = []

    def info(self, message, *args):
        self.messages.append(message % args if args else message)


class _ChargeResult:
    def __init__(self, charged_count, event_charge_limit_reached=False):
        self.charged_count = charged_count
        self.event_charge_limit_reached = event_charge_limit_reached


class _PricingInfo:
    def __init__(self, *, is_pay_per_event=False, per_event_prices=None):
        self.is_pay_per_event = is_pay_per_event
        self.per_event_prices = per_event_prices or {}


class _ChargingManager:
    def __init__(self, pricing_info):
        self.pricing_info = pricing_info

    def get_pricing_info(self):
        return self.pricing_info


class _Dataset:
    def __init__(self):
        self.pushes = []

    async def push_data(self, data):
        self.pushes.append(data)


class _FakeActor:
    def __init__(self):
        self.input = {"urls": ["one.test", "two.test"]}
        self.pushes = []
        self.log = _Log()
        self.results = [
            _ChargeResult(1, event_charge_limit_reached=True),
        ]
        self.error_dataset = _Dataset()
        self.opened_aliases = []
        self.pricing_info = _PricingInfo(is_pay_per_event=False)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get_input(self):
        return self.input

    async def push_data(self, data, charged_event_name=None):
        self.pushes.append((data, charged_event_name))
        if charged_event_name is None:
            return None
        return self.results.pop(0)

    async def open_dataset(self, *, alias=None, **kwargs):
        self.opened_aliases.append(alias)
        return self.error_dataset

    def get_charging_manager(self):
        return _ChargingManager(self.pricing_info)


def _load_main(fake_actor):
    fake_apify = types.ModuleType("apify")
    fake_apify.Actor = fake_actor
    sys.modules["apify"] = fake_apify
    sys.modules.pop("src.main", None)
    module = importlib.import_module("src.main")
    return module


def test_budget_boundary_counts_last_charged_success(monkeypatch):
    fake = _FakeActor()
    module = _load_main(fake)

    calls = []

    def audit(url, **kwargs):
        calls.append(url)
        return {"status": "SUCCESS", "requestedUrl": url}

    monkeypatch.setattr(module, "audit_url", audit)
    asyncio.run(module.main())

    assert calls == ["one.test"]
    assert len(fake.pushes) == 1
    assert fake.pushes[0][1] == "website-audit"
    assert any("Completed: 1 successful audit(s), 0 error record(s)." in m for m in fake.log.messages)


def test_errors_go_to_aliased_dataset_not_billable_default_dataset(monkeypatch):
    fake = _FakeActor()
    fake.input = {"urls": ["bad.test"]}
    fake.results = []
    module = _load_main(fake)

    monkeypatch.setattr(
        module,
        "audit_url",
        lambda url, **kwargs: {"status": "ERROR", "requestedUrl": url, "errorCode": "HTTP_404"},
    )
    asyncio.run(module.main())

    assert fake.pushes == []
    assert fake.opened_aliases == ["errors"]
    assert len(fake.error_dataset.pushes) == 1
    assert fake.error_dataset.pushes[0]["errorCode"] == "HTTP_404"
    assert any("Completed: 0 successful audit(s), 1 error record(s)." in m for m in fake.log.messages)


def test_ppe_pricing_guard_accepts_exact_custom_price_without_synthetic_charges():
    fake = _FakeActor()
    fake.pricing_info = _PricingInfo(
        is_pay_per_event=True,
        per_event_prices={"website-audit": Decimal("0.001")},
    )
    module = _load_main(fake)

    module._assert_safe_pricing_configuration()


def test_ppe_pricing_guard_rejects_default_dataset_synthetic_charge():
    fake = _FakeActor()
    fake.pricing_info = _PricingInfo(
        is_pay_per_event=True,
        per_event_prices={
            "website-audit": Decimal("0.001"),
            "apify-default-dataset-item": Decimal("0.0001"),
        },
    )
    module = _load_main(fake)

    with pytest.raises(RuntimeError, match="apify-default-dataset-item"):
        module._assert_safe_pricing_configuration()


def test_ppe_pricing_guard_rejects_actor_start_charge():
    fake = _FakeActor()
    fake.pricing_info = _PricingInfo(
        is_pay_per_event=True,
        per_event_prices={
            "website-audit": Decimal("0.001"),
            "apify-actor-start": Decimal("0.001"),
        },
    )
    module = _load_main(fake)

    with pytest.raises(RuntimeError, match="apify-actor-start"):
        module._assert_safe_pricing_configuration()


def test_ppe_pricing_guard_rejects_wrong_custom_price():
    fake = _FakeActor()
    fake.pricing_info = _PricingInfo(
        is_pay_per_event=True,
        per_event_prices={"website-audit": Decimal("0.002")},
    )
    module = _load_main(fake)

    with pytest.raises(RuntimeError, match="exactly \\$0.001"):
        module._assert_safe_pricing_configuration()
