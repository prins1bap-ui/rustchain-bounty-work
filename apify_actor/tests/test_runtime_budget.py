import asyncio
import importlib
import sys
import types


class _Log:
    def __init__(self):
        self.messages = []

    def info(self, message, *args):
        self.messages.append(message % args if args else message)


class _ChargeResult:
    charged_count = 1
    event_charge_limit_reached = False


class _PricingInfo:
    is_pay_per_event = False


class _ChargingManager:
    def get_pricing_info(self):
        return _PricingInfo()


class _FakeActor:
    def __init__(self):
        self.log = _Log()
        self.pushes = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get_input(self):
        return {"urls": ["one.test", "two.test"]}

    async def push_data(self, data, charged_event_name=None):
        self.pushes.append((data, charged_event_name))
        return _ChargeResult()

    def get_charging_manager(self):
        return _ChargingManager()


def _load_main(fake_actor):
    fake_apify = types.ModuleType("apify")
    fake_apify.Actor = fake_actor
    sys.modules["apify"] = fake_apify
    sys.modules.pop("src.main", None)
    return importlib.import_module("src.main")


def test_wallclock_budget_stops_before_next_network_request(monkeypatch):
    fake = _FakeActor()
    module = _load_main(fake)
    calls = []

    def audit(url, **kwargs):
        calls.append(url)
        return {
            "status": "SUCCESS",
            "requestedUrl": url,
            "contentType": "text/html",
        }

    ticks = iter([100.0, 100.0, 701.0])
    monkeypatch.setattr(module, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(module, "audit_url", audit)

    asyncio.run(module.main())

    assert calls == ["one.test"]
    assert len(fake.pushes) == 1
    assert fake.pushes[0][1] == "website-audit"
    assert any("wall-clock safety budget reached" in message for message in fake.log.messages)
