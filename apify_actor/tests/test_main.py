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
    def __init__(self, charged_count, event_charge_limit_reached=False):
        self.charged_count = charged_count
        self.event_charge_limit_reached = event_charge_limit_reached


class _FakeActor:
    def __init__(self):
        self.input = {"urls": ["one.test", "two.test"]}
        self.pushes = []
        self.log = _Log()
        self.results = [
            _ChargeResult(1, event_charge_limit_reached=True),
        ]

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


def test_errors_are_pushed_without_custom_charge_event(monkeypatch):
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

    assert len(fake.pushes) == 1
    assert fake.pushes[0][1] is None
    assert any("Completed: 0 successful audit(s), 1 error record(s)." in m for m in fake.log.messages)
