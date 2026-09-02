from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / 'visuals'
T = ROOT / 'thumbnails'
V.mkdir(exist_ok=True); T.mkdir(exist_ok=True)

BG=(15,18,22); FG=(239,241,245); MUTED=(169,178,189); ACC=(246,190,60); ACC2=(112,190,255); GRID=(46,52,60)

def font(size, bold=False):
    candidates = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'
    ]
    for p in candidates:
        if Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default()

def frame(title, subtitle=''):
    im=Image.new('RGB',(1920,1080),BG); d=ImageDraw.Draw(im)
    for x in range(0,1920,120): d.line((x,0,x,1080),fill=GRID,width=1)
    for y in range(0,1080,120): d.line((0,y,1920,y),fill=GRID,width=1)
    d.text((90,70),title,font=font(66,True),fill=FG)
    if subtitle: d.text((94,155),subtitle,font=font(30),fill=MUTED)
    return im,d

def pill(d,xy,text,accent=ACC):
    x,y,w,h=xy; d.rounded_rectangle((x,y,x+w,y+h),24,fill=(25,30,36),outline=accent,width=4)
    box=d.textbbox((0,0),text,font=font(34,True)); tw=box[2]-box[0]; th=box[3]-box[1]
    d.text((x+(w-tw)/2,y+(h-th)/2-4),text,font=font(34,True),fill=FG)

im,d=frame('OLD HARDWARE, DIFFERENT INCENTIVE','Proof-of-Antiquity rewards authenticated age, not compute speed')
pill(d,(180,340,660,230),'PowerBook G4 (2003)\n2.5× reward weight',ACC)
pill(d,(1080,340,660,230),'Modern x86-64\n1.0× baseline',ACC2)
d.text((590,690),'NOT A SPEED BENCHMARK',font=font(54,True),fill=ACC)
d.text((600,770),'Protocol multipliers ≠ guaranteed profit',font=font(34),fill=FG)
im.save(V/'01_hook.png')

im,d=frame('PUBLISHED MULTIPLIER EXAMPLE','The protocol chooses what scarcity to reward')
for x,label,val in [(200,'PowerPC G4','2.5×'),(730,'PowerPC G5','2.0×'),(1260,'Modern x86','1.0×')]:
    d.rounded_rectangle((x,320,x+460,700),30,fill=(24,29,35),outline=ACC if x<1000 else ACC2,width=4)
    d.text((x+45,390),label,font=font(40,True),fill=FG); d.text((x+120,520),val,font=font(72,True),fill=ACC if x<1000 else ACC2)
d.text((390,820),'Reward weight, not raw compute throughput',font=font(44,True),fill=FG)
im.save(V/'02_multiplier.png')

im,d=frame('RIP-200: ONE CPU = ONE VOTE','Deterministic round-robin participation for validated hardware')
centers=[(330,500),(700,500),(1070,500),(1440,500)]
for i,(x,y) in enumerate(centers,1):
    d.ellipse((x-110,y-110,x+110,y+110),fill=(26,32,39),outline=ACC2,width=5); d.text((x-28,y-38),str(i),font=font(72,True),fill=FG)
    if i<4: d.line((x+115,y,x+250,y),fill=ACC,width=7)
d.text((415,760),'Identity admits the device. Antiquity weights the reward.',font=font(40,True),fill=FG)
im.save(V/'03_round_robin.png')

im,d=frame('SIX REQUIRED HARDWARE-FINGERPRINT CHECKS','Whitepaper §4')
checks=['Clock-skew / oscillator drift','Cache timing fingerprint','SIMD unit identity','Thermal-drift entropy','Instruction-path jitter','Anti-emulation behavior']
for i,t in enumerate(checks):
    col=i%2; row=i//2; x=150+col*860; y=285+row*210
    d.rounded_rectangle((x,y,x+760,y+150),24,fill=(25,30,36),outline=ACC2,width=3)
    d.text((x+38,y+47),f'{i+1}. {t}',font=font(33,True),fill=FG)
d.text((480,925),'Retro platforms can add ROM fingerprinting',font=font(34),fill=ACC)
im.save(V/'04_six_checks.png')

im,d=frame('CROSS-VALIDATE THE CLAIM','A payload label alone is not the proof')
pill(d,(140,360,430,180),'Claimed\narchitecture',ACC2); pill(d,(745,260,430,180),'Timing + cache\nbehavior',ACC); pill(d,(745,510,430,180),'SIMD + thermal\nbehavior',ACC); pill(d,(1350,360,430,180),'Validated\nhardware identity',ACC2)
d.line((570,450,745,350),fill=FG,width=5); d.line((570,450,745,600),fill=FG,width=5); d.line((1175,350,1350,450),fill=FG,width=5); d.line((1175,600,1350,450),fill=FG,width=5)
im.save(V/'05_cross_validation.png')

im,d=frame('ANTIQUITY MULTIPLIERS','Published README values • reward weight only')
rows=[('PowerPC G4','2.5×'),('PS3 Cell BE','2.2×'),('PowerPC G5','2.0×'),('RISC-V','1.4×'),('Apple Silicon M1','1.2×'),('Modern x86-64','1.0×'),('Modern ARM NAS/SBC','0.0005×')]
y=250
for i,(a,b) in enumerate(rows):
    d.rectangle((300,y,1620,y+92),fill=(24,29,35) if i%2==0 else (20,25,30)); d.text((350,y+24),a,font=font(33,True),fill=FG); d.text((1390,y+20),b,font=font(39,True),fill=ACC if b!='1.0×' else ACC2); y+=100
d.text((390,970),'Protocol multipliers are not speed or profit guarantees.',font=font(34,True),fill=ACC)
im.save(V/'06_multiplier_table.png')

im,d=frame('MINER ATTESTATION FLOW','Documented REST interaction')
steps=[('1','POST /attest/challenge'),('2','POST /attest/submit'),('3','Hardware validation'),('4','Epoch reward process')]
for i,(n,t) in enumerate(steps):
    x=150+i*440; d.rounded_rectangle((x,390,x+360,580),26,fill=(25,30,36),outline=ACC2,width=4); d.text((x+25,425),n,font=font(58,True),fill=ACC); d.text((x+95,430),t,font=font(26,True),fill=FG)
    if i<3: d.line((x+360,485,x+430,485),fill=FG,width=6)
d.text((380,760),'Identity proof first. Reward logic second.',font=font(46,True),fill=FG)
im.save(V/'07_attestation_flow.png')

im,d=frame('COMMAND EXAMPLE — NO FABRICATED OUTPUT','Endpoints documented in the technical whitepaper')
d.rounded_rectangle((190,260,1730,830),30,fill=(8,10,12),outline=(70,78,88),width=4)
lines=['# Inspect public network state','curl https://rustchain.org/epoch','curl https://rustchain.org/api/miners','','# Miner attestation uses documented endpoints','POST /attest/challenge','POST /attest/submit']
y=330
for s in lines:
    d.text((260,y),s,font=font(36),fill=ACC if s.startswith('#') else FG); y+=65
d.text((420,900),'Illustrative command frame; no response data is invented.',font=font(32,True),fill=MUTED)
im.save(V/'08_terminal_example.png')

im,d=frame('THE EXPERIMENT','Can authenticated age become an economically relevant resource?')
pill(d,(180,340,450,200),'Deterministic\nparticipation',ACC2); pill(d,(735,340,450,200),'Hardware\nfingerprinting',ACC); pill(d,(1290,340,450,200),'Antiquity\nreward weight',ACC2)
d.text((290,730),'Interesting mechanism ≠ proven economic outcome',font=font(52,True),fill=FG)
d.text((470,820),'Measure it. Do not market around the unknowns.',font=font(34),fill=ACC)
im.save(V/'09_experiment.png')

im,d=frame('VERIFY EVERY CLAIM','Source-locked to a public RustChain commit')
d.text((220,350),'Scottcjn/Rustchain',font=font(62,True),fill=FG); d.text((220,450),'README.md',font=font(46),fill=ACC2); d.text((220,530),'docs/WHITEPAPER.md',font=font(46),fill=ACC2)
d.rounded_rectangle((200,680,1720,820),20,fill=(25,30,36),outline=ACC,width=3)
d.text((250,720),'commit 5a9d6a8a190008446d4f6c5ed2358bde532ba325',font=font(31,True),fill=FG)
im.save(V/'10_sources.png')

def thumb(name, headline, sub, left='2.5×', right='1.0×'):
    im=Image.new('RGB',(1280,720),BG); d=ImageDraw.Draw(im)
    d.rectangle((0,0,1280,720),outline=ACC,width=10)
    d.text((55,55),headline,font=font(62,True),fill=FG)
    d.text((58,145),sub,font=font(30,True),fill=MUTED)
    d.rounded_rectangle((80,285,555,565),28,fill=(25,30,36),outline=ACC,width=5); d.text((180,340),'2003 G4',font=font(42,True),fill=FG); d.text((205,420),left,font=font(72,True),fill=ACC)
    d.rounded_rectangle((725,285,1200,565),28,fill=(25,30,36),outline=ACC2,width=5); d.text((805,340),'MODERN x86',font=font(42,True),fill=FG); d.text((875,420),right,font=font(72,True),fill=ACC2)
    d.text((360,625),'REWARD WEIGHT • NOT SPEED',font=font(30,True),fill=FG); im.save(T/name)
thumb('thumbnail.png','WHY OLD HARDWARE OUTRANKS NEW','RustChain • Proof of Antiquity')
thumb('thumbnail-alt-1.png','A 2003 POWERBOOK GETS 2.5×','Six checks decide whether it is real')
thumb('thumbnail-alt-2.png','PROOF OF ANTIQUITY, EXPLAINED','One CPU = one vote • age weights rewards')