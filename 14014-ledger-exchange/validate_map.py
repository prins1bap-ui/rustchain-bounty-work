#!/usr/bin/env python3
"""Structural validation for the Ledger Exchange #14014 package."""
from __future__ import annotations
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "pk3_build"
MAPS = BUILD / "maps"
NAME = "rustchain_ledger_exchange"


def tga_dims(path: Path):
    data = path.read_bytes()[:18]
    if len(data) != 18:
        raise AssertionError(f"short TGA header: {path}")
    vals = struct.unpack("<BBBHHBHHHHBB", data)
    return vals[8], vals[9], vals[10]


def main():
    map_path = MAPS / f"{NAME}.map"
    mapinfo = MAPS / f"{NAME}.mapinfo"
    shot = MAPS / f"{NAME}.tga"
    bsp = MAPS / f"{NAME}.bsp"
    text = map_path.read_text(encoding="utf-8")
    assert '"classname" "worldspawn"' in text
    assert text.count('"classname" "info_player_deathmatch"') >= 8
    assert text.count('"classname" "light"') >= 5
    assert "RustChain Ledger Exchange" in text
    assert text.count("{") == text.count("}")
    info = mapinfo.read_text(encoding="utf-8")
    assert "gametype dm" in info and "gametype ca" in info
    w,h,bpp = tga_dims(shot)
    assert (w,h,bpp) == (512,384,24), (w,h,bpp)
    for tex in (BUILD / "textures" / "rustchain_ledger").glob("*.tga"):
        assert tga_dims(tex) == (64,64,24)
    if bsp.exists():
        assert bsp.stat().st_size > 4096, bsp.stat().st_size
    files = [p for p in BUILD.rglob("*") if p.is_file()]
    manifest = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    (ROOT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"validated map package ({len(files)} files); BSP present={bsp.exists()}")

if __name__ == "__main__":
    main()
