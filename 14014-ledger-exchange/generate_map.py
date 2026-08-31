#!/usr/bin/env python3
"""Generate the original RustChain Ledger Exchange arena map for bounty #14014."""

from __future__ import annotations

import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "pk3_build"
MAPS = BUILD / "maps"
TEX = BUILD / "textures" / "rustchain_ledger"
NAME = "rustchain_ledger_exchange"

FLOOR = "rustchain_ledger/floor"
WALL = "rustchain_ledger/wall"
TRIM = "rustchain_ledger/trim"
GLOW = "rustchain_ledger/glow"
CAULK = "common/caulk"


def face(a, b, c, tex, scale=0.25):
    return f"( {a[0]} {a[1]} {a[2]} ) ( {b[0]} {b[1]} {b[2]} ) ( {c[0]} {c[1]} {c[2]} ) {tex} 0 0 0 {scale} {scale} 0 0 0"


def box(x1, y1, z1, x2, y2, z2, top=FLOOR, side=WALL, bottom=CAULK):
    lines = ["{"]
    lines.append(face((x2,y1,z2),(x1,y1,z2),(x1,y2,z2),top))
    lines.append(face((x2,y2,z1),(x1,y2,z1),(x1,y1,z1),bottom))
    lines.append(face((x2,y2,z1),(x2,y2,z2),(x1,y2,z2),side))
    lines.append(face((x1,y1,z1),(x1,y1,z2),(x2,y1,z2),side))
    lines.append(face((x2,y1,z1),(x2,y1,z2),(x2,y2,z2),side))
    lines.append(face((x1,y2,z1),(x1,y2,z2),(x1,y1,z2),side))
    lines.append("}")
    return "\n".join(lines)


def entity(classname, origin, **kv):
    lines = ["{", f'"classname" "{classname}"', f'"origin" "{origin[0]} {origin[1]} {origin[2]}"']
    for k, v in kv.items():
        lines.append(f'"{k}" "{v}"')
    lines.append("}")
    return "\n".join(lines)


def tga(path: Path, width: int, height: int, pixel_fn):
    path.parent.mkdir(parents=True, exist_ok=True)
    header = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, width, height, 24, 0x20)
    data = bytearray()
    for y in range(height):
        for x in range(width):
            r, g, b = pixel_fn(x, y, width, height)
            data += bytes((b & 255, g & 255, r & 255))
    path.write_bytes(header + data)


def make_textures():
    # Steel grid floor with cyan ledger traces.
    def floor_px(x,y,w,h):
        grid = (x % 16 in (0,1) or y % 16 in (0,1))
        trace = ((x + 2*y) % 31 in (0,1))
        if trace: return (16, 168, 184)
        if grid: return (58, 70, 76)
        return (29 + (x//8+y//8)%2*4, 34, 38)
    def wall_px(x,y,w,h):
        seam = (x % 32 in (0,1) or y % 32 in (0,1))
        rivet = ((x%32-4)**2 + (y%32-4)**2 < 4)
        if rivet: return (188, 118, 28)
        if seam: return (82, 88, 91)
        return (43, 47, 50)
    def trim_px(x,y,w,h):
        stripe = ((x+y)//8)%2
        return (210,120,18) if stripe else (35,42,47)
    def glow_px(x,y,w,h):
        d = abs(y-h/2)/(h/2)
        return (15, int(160*(1-d)+30), int(220*(1-d)+40))
    for name, fn in (("floor",floor_px),("wall",wall_px),("trim",trim_px),("glow",glow_px)):
        tga(TEX / f"{name}.tga", 64, 64, fn)


def make_levelshot():
    # Deterministic top-down schematic levelshot: room, four exchange desks,
    # central clearing ring and crossed routes. It is a preview, not a fake runtime screenshot.
    def px(x,y,w,h):
        nx = (x-w/2)/(w/2); ny = (y-h/2)/(h/2)
        base = (17,22,25)
        if abs(nx) > .93 or abs(ny) > .93: return (202,114,18)
        if abs(nx) < .055 or abs(ny) < .075: base = (18,112,130)
        r = math.hypot(nx, ny)
        if .20 < r < .25: base = (218,135,22)
        for cx, cy in ((-.52,-.42),(.52,-.42),(-.52,.42),(.52,.42)):
            if abs(nx-cx)<.15 and abs(ny-cy)<.12: base = (63,73,78)
        # spawn-node glints
        for cx, cy in ((-.75,0),(.75,0),(0,-.72),(0,.72)):
            if (nx-cx)**2+(ny-cy)**2 < .0015: base=(220,230,235)
        return base
    tga(MAPS / f"{NAME}.tga", 512, 384, px)


def make_map():
    MAPS.mkdir(parents=True, exist_ok=True)
    world = ["{", '"classname" "worldspawn"', '"message" "RustChain Ledger Exchange"', '"author" "prins1bap-ui"',
             '"_description" "A cross-route DM/CA arena styled as a physical transaction matching floor."', '"_ambient" "34"']
    # Sealed arena shell: interior x +/-1024, y +/-768, z 0..384.
    world += [
        box(-1024,-768,-64,1024,768,0,FLOOR,WALL),
        box(-1024,-768,384,1024,768,448,WALL,WALL),
        box(-1088,-768,0,-1024,768,384,WALL,WALL),
        box(1024,-768,0,1088,768,384,WALL,WALL),
        box(-1024,768,0,1024,832,384,WALL,WALL),
        box(-1024,-832,0,1024,-768,384,WALL,WALL),
    ]
    # Central settlement ring represented by a low octagonal-ish cross of four blocks.
    world += [
        box(-224,-224,0,224,-176,28,GLOW,TRIM),
        box(-224,176,0,224,224,28,GLOW,TRIM),
        box(-224,-176,0,-176,176,28,GLOW,TRIM),
        box(176,-176,0,224,176,28,GLOW,TRIM),
        box(-72,-72,0,72,72,96,GLOW,TRIM),
    ]
    # Four exchange desks create distinct corner duels while preserving cross-flow.
    for x1,y1,x2,y2 in ((-760,-520,-500,-390),(500,-520,760,-390),(-760,390,-500,520),(500,390,760,520)):
        world.append(box(x1,y1,0,x2,y2,112,TRIM,WALL))
    # Mid-lane cover nodes, offset so neither sightline is fully blocked.
    for x,y in ((-520,0),(520,0),(0,-390),(0,390)):
        world.append(box(x-64,y-64,0,x+64,y+64,150,GLOW,WALL))
    # Raised side ledgers create simple vertical combat without enclosing rooms.
    world += [
        box(-1000,-210,0,-790,210,96,FLOOR,TRIM),
        box(790,-210,0,1000,210,96,FLOOR,TRIM),
    ]
    world.append("}")

    ents = []
    for origin, angle in [((-820,-600,32),45),((820,600,32),225),((-820,600,32),315),((820,-600,32),135),
                          ((-650,0,32),0),((650,0,32),180),((0,-590,32),90),((0,590,32),270)]:
        ents.append(entity("info_player_deathmatch", origin, angle=str(angle)))
    for origin in ((0,0,112),(-420,0,32),(420,0,32),(0,-300,32),(0,300,32)):
        ents.append(entity("light", origin, light="450", _color="0.10 0.80 0.95"))
    # Common Xonotic pickup classnames; compile remains valid even if server config replaces them.
    ents += [
        entity("weapon_shotgun",(-330,-300,32)),
        entity("weapon_machinegun",(330,300,32)),
        entity("item_health_medium",(-330,300,32)),
        entity("item_armor_medium",(330,-300,32)),
    ]
    (MAPS / f"{NAME}.map").write_text("\n".join(world + ents) + "\n", encoding="utf-8")
    (MAPS / f"{NAME}.mapinfo").write_text(
        "title RustChain Ledger Exchange\n"
        "description Cross-route RustChain DM/CA arena with a central settlement ring, exchange desks, and side ledgers.\n"
        "author prins1bap-ui\n"
        "has weapons\n"
        "gametype dm pointlimit=30 timelimit=15\n"
        "gametype ca pointlimit=10 timelimit=15 teams=2\n",
        encoding="utf-8",
    )


def main():
    make_textures()
    make_levelshot()
    make_map()
    print("generated map source, mapinfo, four textures, and 512x384 schematic levelshot")


if __name__ == "__main__":
    main()
