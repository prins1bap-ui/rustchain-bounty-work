#!/usr/bin/env python3
"""Generate the original Antiquity Relay Yard Xonotic arena for bounty #14014."""
from __future__ import annotations
import math, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parent; BUILD=ROOT/'pk3_build'; MAPS=BUILD/'maps'; TEX=BUILD/'textures'/'rustchain_relay'; NAME='rustchain_antiquity_relay'
FLOOR='rustchain_relay/floor'; WALL='rustchain_relay/wall'; TRIM='rustchain_relay/trim'; GLOW='rustchain_relay/glow'; CAULK='common/caulk'
def face(a,b,c,t,s=.25): return f'( {a[0]} {a[1]} {a[2]} ) ( {b[0]} {b[1]} {b[2]} ) ( {c[0]} {c[1]} {c[2]} ) {t} 0 0 0 {s} {s} 0 0 0'
def box(x1,y1,z1,x2,y2,z2,top=FLOOR,side=WALL,bottom=CAULK):
    return '\n'.join(['{',face((x2,y1,z2),(x1,y1,z2),(x1,y2,z2),top),face((x2,y2,z1),(x1,y2,z1),(x1,y1,z1),bottom),face((x2,y2,z1),(x2,y2,z2),(x1,y2,z2),side),face((x1,y1,z1),(x1,y1,z2),(x2,y1,z2),side),face((x2,y1,z1),(x2,y1,z2),(x2,y2,z2),side),face((x1,y2,z1),(x1,y2,z2),(x1,y1,z2),side),'}'])
def ent(c,o,**kv):
    a=['{',f'"classname" "{c}"',f'"origin" "{o[0]} {o[1]} {o[2]}"']; a += [f'"{k}" "{v}"' for k,v in kv.items()]; return '\n'.join(a+['}'])
def tga(path,w,h,fn):
    path.parent.mkdir(parents=True,exist_ok=True); hdr=struct.pack('<BBBHHBHHHHBB',0,0,2,0,0,0,0,0,w,h,24,0x20); d=bytearray()
    for y in range(h):
        for x in range(w):
            r,g,b=fn(x,y,w,h); d += bytes((b&255,g&255,r&255))
    path.write_bytes(hdr+d)
def textures():
    def floor(x,y,w,h):
        rail=(x%24 in (0,1) or y%24 in (0,1)); return (24,134,150) if rail else (31+(x//12+y//12)%2*5,37,40)
    def wall(x,y,w,h):
        band=y%32<4; bolt=((x%32-8)**2+(y%32-8)**2<5); return (190,105,22) if bolt else ((65,70,72) if band else (40,44,46))
    def trim(x,y,w,h): return (190,104,20) if ((x//8)%2)==0 else (24,31,35)
    def glow(x,y,w,h): return (10,120+int(90*(1-abs(y-h/2)/(h/2))),200)
    for n,f in [('floor',floor),('wall',wall),('trim',trim),('glow',glow)]: tga(TEX/f'{n}.tga',64,64,f)
def levelshot():
    def px(x,y,w,h):
        nx=(x-w/2)/(w/2); ny=(y-h/2)/(h/2); c=(16,21,24)
        if abs(nx)>.94 or abs(ny)>.94: return (195,105,20)
        # two long relay lanes and offset bridge
        if abs(ny-.36)<.08 or abs(ny+.36)<.08: c=(18,102,118)
        if abs(nx)<.10 and abs(ny)<.72: c=(45,52,56)
        if abs(nx-.48)<.12 and abs(ny)<.17: c=(202,120,22)
        if abs(nx+.48)<.12 and abs(ny)<.17: c=(202,120,22)
        for cx,cy in [(-.78,-.36),(.78,.36),(-.78,.36),(.78,-.36),(0,-.72),(0,.72)]:
            if (nx-cx)**2+(ny-cy)**2<.0018: c=(230,235,238)
        return c
    tga(MAPS/f'{NAME}.tga',512,384,px)
def build():
    MAPS.mkdir(parents=True,exist_ok=True); world=['{','"classname" "worldspawn"','"message" "RustChain Antiquity Relay Yard"','"author" "prins1bap-ui"','"_description" "Two-lane relay-yard arena with offset bridge, vintage compute bays and central transfer spine."','"_ambient" "32"']
    # shell interior +/-1100 x +/-700
    world += [box(-1100,-700,-64,1100,700,0),box(-1100,-700,420,1100,700,484,WALL,WALL),box(-1164,-700,0,-1100,700,420,WALL,WALL),box(1100,-700,0,1164,700,420,WALL,WALL),box(-1100,700,0,1100,764,420,WALL,WALL),box(-1100,-764,0,1100,-700,420,WALL,WALL)]
    # parallel relay lanes, asymmetric raised platforms
    world += [box(-1000,-350,0,1000,-235,48,GLOW,TRIM),box(-1000,235,0,1000,350,48,GLOW,TRIM),box(-125,-230,0,125,230,120,FLOOR,TRIM),box(390,-180,0,640,180,92,TRIM,WALL),box(-700,-160,0,-430,160,148,FLOOR,TRIM)]
    # cover fins along lanes
    for x,y in [(-780,-300),(-250,-300),(300,-300),(820,-300),(-820,300),(-300,300),(250,300),(780,300)]: world.append(box(x-45,y-55,0,x+45,y+55,130,GLOW,WALL))
    # corner compute bays
    for x1,y1,x2,y2 in [(-1020,-620,-780,-500),(780,-620,1020,-500),(-1020,500,-780,620),(780,500,1020,620)]: world.append(box(x1,y1,0,x2,y2,95,TRIM,WALL))
    world.append('}')
    es=[]
    for o,a in [((-930,-420,32),20),((930,420,32),200),((-930,420,32),340),((930,-420,32),160),((-620,-70,32),0),((620,70,32),180),((0,-570,32),90),((0,570,32),270)]: es.append(ent('info_player_deathmatch',o,angle=str(a)))
    for o in [(0,0,160),(-520,0,190),(520,0,150),(0,-300,80),(0,300,80)]: es.append(ent('light',o,light='480',_color='0.12 0.78 0.95'))
    es += [ent('weapon_shotgun',(-360,-50,32)),ent('weapon_machinegun',(360,50,32)),ent('item_health_medium',(-60,500,32)),ent('item_armor_medium',(60,-500,32))]
    (MAPS/f'{NAME}.map').write_text('\n'.join(world+es)+'\n')
    (MAPS/f'{NAME}.mapinfo').write_text('title RustChain Antiquity Relay Yard\ndescription Two-lane DM/CA relay yard with asymmetric vertical platforms and a central transfer spine.\nauthor prins1bap-ui\nhas weapons\ngametype dm pointlimit=30 timelimit=15\ngametype ca pointlimit=10 timelimit=15 teams=2\n')
def main(): textures(); levelshot(); build(); print('generated Antiquity Relay Yard source package')
if __name__=='__main__': main()
