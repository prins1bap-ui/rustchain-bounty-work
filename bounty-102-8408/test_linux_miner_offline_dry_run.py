# SPDX-License-Identifier: MIT
import importlib.util
from pathlib import Path
import urllib.request

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MINER_PATH = REPO_ROOT / "miners" / "linux" / "rustchain_linux_miner.py"
FP_PATH = REPO_ROOT / "miners" / "linux" / "fingerprint_checks.py"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_offline_flag_requires_dry_run():
    miner = _load(MINER_PATH, "linux_miner_offline_cli")
    with pytest.raises(SystemExit) as exc:
        miner.main(["--offline"])
    assert exc.value.code == 2


def test_main_threads_offline_mode_without_key_persistence(monkeypatch):
    miner = _load(MINER_PATH, "linux_miner_offline_main")
    seen = {}

    class FakeMiner:
        def __init__(self, **kwargs):
            seen.update(kwargs)

        def dry_run(self):
            seen["dry_run_called"] = True
            return True

        def mine(self):
            raise AssertionError("offline dry-run must not mine")

    monkeypatch.setattr(miner, "LocalMiner", FakeMiner)

    assert miner.main(["--dry-run", "--offline"]) == 0
    assert seen["offline"] is True
    assert seen["persist_key"] is False
    assert seen["dry_run_called"] is True


def test_offline_dry_run_skips_node_health(monkeypatch, capsys):
    miner = _load(MINER_PATH, "linux_miner_offline_health")
    instance = object.__new__(miner.LocalMiner)
    instance.offline = True
    instance.verbose = False
    instance.show_payload = False
    instance.node_url = "https://rustchain.org"
    instance.wallet = "RTC-test-wallet"
    instance.hw_info = {}
    instance.fingerprint_data = {"checks": {}, "all_passed": True}
    instance.fingerprint_passed = True

    monkeypatch.setattr(miner, "FINGERPRINT_AVAILABLE", True)
    instance._get_hw_info = lambda: instance.hw_info.update(
        {
            "hostname": "offline-test",
            "cpu": "test-cpu",
            "cores": 4,
            "memory_gb": 8,
            "macs": [],
            "serial": None,
        }
    )
    instance._get = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("offline dry-run attempted node HTTP")
    )

    assert instance.dry_run() is True
    output = capsys.readouterr().out
    assert "Network probes: SKIPPED (--offline)" in output
    assert "Health probe: HTTP" not in output


def test_anti_emulation_offline_skips_link_local_metadata(monkeypatch):
    fp = _load(FP_PATH, "linux_fp_offline")
    attempted = []

    def forbidden_urlopen(request, *args, **kwargs):
        attempted.append(getattr(request, "full_url", str(request)))
        raise AssertionError("offline fingerprint check attempted HTTP")

    monkeypatch.setattr(urllib.request, "urlopen", forbidden_urlopen)

    _passed, data = fp.check_anti_emulation(skip_network_probes=True)

    assert attempted == []
    assert data["network_metadata_probes_skipped"] is True
