#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parent; BUILD=ROOT/'pk3_build'; MAPS=BUILD/'maps'; NAME='rustchain_antiquity_relay'
def dims(p):
    d=p.read_bytes()[:18]; assert len(d)==18; v=struct.unpack('<BBBHHBHHHHBB',d); return v[8],v[9],v[10]
def main():
    mp=MAPS/f'{NAME}.map'; info=MAPS/f'{NAME}.mapinfo'; shot=MAPS/f'{NAME}.tga'; bsp=MAPS/f'{NAME}.bsp'
    t=mp.read_text(); assert '"classname" "worldspawn"' in t; assert t.count('"classname" "info_player_deathmatch"')>=8; assert t.count('"classname" "light"')>=5; assert t.count('{')==t.count('}'); assert 'Antiquity Relay Yard' in t
    i=info.read_text(); assert 'gametype dm' in i and 'gametype ca' in i; assert dims(shot)==(512,384,24)
    for p in (BUILD/'textures'/'rustchain_relay').glob('*.tga'): assert dims(p)==(64,64,24)
    if bsp.exists(): assert bsp.stat().st_size>4096
    fs=[p for p in BUILD.rglob('*') if p.is_file()]; m={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(fs)}; (ROOT/'MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n')
    print(f'validated Antiquity Relay Yard ({len(fs)} files); BSP present={bsp.exists()}')
if __name__=='__main__': main()
