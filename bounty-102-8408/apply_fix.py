#!/usr/bin/env python3
"""Apply RustChain #8408 offline dry-run fix to the audited upstream checkout."""
from pathlib import Path
import subprocess
import sys
import textwrap

EXPECTED_BASE = "aa584b344a766f6c0f8613ba7198d1cc7ffbae35"


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected source block exactly once, found {count}")
    return text.replace(old, new, 1)


def apply(repo):
    repo = Path(repo).resolve()
    miner_path = repo / "miners/linux/rustchain_linux_miner.py"
    fp_path = repo / "miners/linux/fingerprint_checks.py"
    docs_path = repo / "docs/sprint/miner-setup-guide.md"
    test_path = repo / "tests/test_linux_miner_offline_dry_run.py"

    for path in (miner_path, fp_path, docs_path):
        if not path.is_file():
            raise RuntimeError(f"required upstream file missing: {path}")

    head = subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip()
    if head != EXPECTED_BASE:
        raise RuntimeError(
            f"unexpected HEAD {head}; expected {EXPECTED_BASE}; re-audit before applying"
        )

    miner = miner_path.read_text(encoding="utf-8")
    fp = fp_path.read_text(encoding="utf-8")
    docs = docs_path.read_text(encoding="utf-8")

    miner = replace_once(
        miner,
        "                 persist_key=True):",
        "                 persist_key=True, offline=False):",
        "LocalMiner constructor",
    )
    miner = replace_once(
        miner,
        "        self.show_payload = show_payload\n",
        "        self.show_payload = show_payload\n        self.offline = offline\n",
        "offline state",
    )
    miner = replace_once(
        miner,
        "            passed, results = validate_all_checks()\n",
        "            passed, results = validate_all_checks(\n"
        "                skip_network_probes=self.offline\n"
        "            )\n",
        "fingerprint wiring",
    )
    miner = replace_once(
        miner,
        "        # Optional health probe (read-only)\n        try:\n",
        "        if self.offline:\n"
        "            print(\"[DRY-RUN] Network probes: SKIPPED (--offline)\")\n"
        "            print(\"[DRY-RUN] Next real steps would be: attest -> enroll -> mine loop\")\n"
        "            return True\n\n"
        "        # Optional health probe (read-only)\n        try:\n",
        "offline health gate",
    )
    miner = replace_once(
        miner,
        "    parser.add_argument(\"--verbose\", action=\"store_true\", help=\"Enable verbose output showing API endpoints, headers, and response details\")\n",
        "    parser.add_argument(\n"
        "        \"--offline\",\n"
        "        action=\"store_true\",\n"
        "        help=\"With --dry-run, skip all outbound network probes (cloud metadata and node health)\",\n"
        "    )\n"
        "    parser.add_argument(\"--verbose\", action=\"store_true\", help=\"Enable verbose output showing API endpoints, headers, and response details\")\n",
        "offline CLI option",
    )
    miner = replace_once(
        miner,
        "    args = parser.parse_args(argv)\n\n    miner = LocalMiner(\n",
        "    args = parser.parse_args(argv)\n"
        "    if args.offline and not args.dry_run:\n"
        "        parser.error(\"--offline requires --dry-run\")\n\n"
        "    miner = LocalMiner(\n",
        "offline CLI validation",
    )
    miner = replace_once(
        miner,
        "        persist_key=not args.dry_run,\n    )\n",
        "        persist_key=not args.dry_run,\n        offline=args.offline,\n    )\n",
        "offline constructor wiring",
    )

    fp = replace_once(
        fp,
        "def check_anti_emulation() -> Tuple[bool, Dict]:\n",
        "def check_anti_emulation(skip_network_probes: bool = False) -> Tuple[bool, Dict]:\n",
        "anti-emulation signature",
    )
    start_marker = "    # --- Cloud metadata endpoint check ---\n"
    end_marker = "    # --- systemd-detect-virt (Linux only) ---\n"
    if fp.count(start_marker) != 1 or fp.count(end_marker) != 1:
        raise RuntimeError("cloud metadata marker mismatch")
    start = fp.index(start_marker)
    end = fp.index(end_marker, start)
    cloud_block = fp[start:end]
    guarded = (
        "    # Network-backed metadata probes are optional for offline preflight.\n"
        "    if not skip_network_probes:\n" + textwrap.indent(cloud_block, "    ")
    )
    fp = fp[:start] + guarded + fp[end:]
    fp = replace_once(
        fp,
        '        "is_likely_vm": len(vm_indicators) > 0,\n',
        '        "is_likely_vm": len(vm_indicators) > 0,\n'
        '        "network_metadata_probes_skipped": bool(skip_network_probes),\n',
        "probe evidence marker",
    )
    fp = replace_once(
        fp,
        "def validate_all_checks(include_rom_check: bool = True) -> Tuple[bool, Dict]:\n",
        "def validate_all_checks(\n"
        "    include_rom_check: bool = True,\n"
        "    skip_network_probes: bool = False,\n"
        ") -> Tuple[bool, Dict]:\n",
        "validator signature",
    )
    fp = replace_once(
        fp,
        '        ("anti_emulation", "Anti-Emulation Checks", check_anti_emulation),\n',
        '        (\n'
        '            "anti_emulation",\n'
        '            "Anti-Emulation Checks",\n'
        '            lambda: check_anti_emulation(skip_network_probes=skip_network_probes),\n'
        '        ),\n',
        "validator anti-emulation wiring",
    )

    docs = replace_once(
        docs,
        "safest compatibility check because it prints hardware detection, fingerprint\nstatus, and node health without enrolling or mining.\n",
        "normal compatibility check because it prints hardware detection, fingerprint\n"
        "status, and a read-only node health probe without enrolling or mining. Add\n"
        "`--offline` for a fully local preflight with no outbound HTTP requests.\n",
        "offline docs explanation",
    )
    docs = replace_once(
        docs,
        "python3 rustchain_linux_miner.py --dry-run --show-payload\n```\n",
        "python3 rustchain_linux_miner.py --dry-run --show-payload\n\n"
        "# Fully local: keep local checks; skip cloud metadata and node health\n"
        "python3 rustchain_linux_miner.py --dry-run --offline --show-payload\n```\n",
        "offline docs command",
    )

    miner_path.write_text(miner, encoding="utf-8")
    fp_path.write_text(fp, encoding="utf-8")
    docs_path.write_text(docs, encoding="utf-8")

    source_test = Path(__file__).with_name("test_linux_miner_offline_dry_run.py")
    if test_path.exists():
        raise RuntimeError(f"refusing to overwrite existing test: {test_path}")
    test_path.write_text(source_test.read_text(encoding="utf-8"), encoding="utf-8")

    print("Applied RustChain #8408 offline dry-run fix")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_fix.py /path/to/Scottcjn/Rustchain")
    apply(sys.argv[1])
