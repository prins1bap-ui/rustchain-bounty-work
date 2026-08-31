#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess, math, shutil

OUT = Path(__file__).resolve().parent / "assets"
OUT.mkdir(parents=True, exist_ok=True)

BG = (14, 17, 20)
CREAM = (244, 233, 205)
GREEN = (99, 214, 140)
ORANGE = (244, 145, 76)
GOLD = (240, 194, 93)
MUTED = (153, 165, 171)
WHITE = (249, 250, 251)

FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)

def fit_text(draw, text, max_width, start=72, minimum=28, bold=True):
    for size in range(start, minimum - 1, -2):
        f = font(size, bold)
        if draw.textbbox((0,0), text, font=f)[2] <= max_width:
            return f
    return font(minimum, bold)

def center(draw, text, y, width, f, fill=WHITE):
    box = draw.textbbox((0,0), text, font=f)
    x = (width - (box[2]-box[0])) // 2
    draw.text((x,y), text, font=f, fill=fill)

def wrap(draw, text, f, max_width):
    words = text.split()
    lines=[]; line=""
    for w in words:
        test = (line+" "+w).strip()
        if draw.textbbox((0,0), test, font=f)[2] <= max_width:
            line=test
        else:
            if line: lines.append(line)
            line=w
    if line: lines.append(line)
    return lines

def draw_terminal(draw, x, y, w, h, glow=GREEN):
    draw.rounded_rectangle((x,y,x+w,y+h), radius=28, fill=(29,34,39), outline=glow, width=4)
    draw.rectangle((x+36,y+48,x+w-36,y+h-46), fill=(6,15,10), outline=(54,79,61), width=3)
    for i, t in enumerate(["> pip install clawrtc", "> hardware: detected", "> dry-run: ready"]):
        draw.text((x+58,y+78+i*54), t, font=font(28, False), fill=glow if i != 1 else CREAM)
    draw.rectangle((x+w*0.38,y+h,x+w*0.62,y+h+28), fill=(70,74,76))
    draw.rounded_rectangle((x+w*0.27,y+h+24,x+w*0.73,y+h+48), 10, fill=(89,91,90))

def draw_chip(draw, x, y, size, label="CPU"):
    draw.rounded_rectangle((x,y,x+size,y+size), radius=22, fill=(31,36,42), outline=GOLD, width=5)
    pad=20
    for i in range(4):
        off=pad+i*(size-2*pad)//3
        draw.line((x-18,y+off,x,y+off), fill=GOLD, width=5)
        draw.line((x+size,y+off,x+size+18,y+off), fill=GOLD, width=5)
        draw.line((x+off,y-18,x+off,y), fill=GOLD, width=5)
        draw.line((x+off,y+size,x+off,y+size+18), fill=GOLD, width=5)
    f=font(max(24,size//5), True)
    center(draw,label,y+size//2-f.size//2 if hasattr(f,'size') else y+size//2-20, int(2*x+size), f, CREAM)

def base_landscape(title, kicker):
    im=Image.new("RGB",(1200,675),BG); d=ImageDraw.Draw(im)
    d.rounded_rectangle((42,38,1158,637),34,outline=(50,61,67),width=3)
    d.text((74,65), kicker.upper(), font=font(25,True), fill=ORANGE)
    tf=fit_text(d,title,1030,64,38,True)
    d.text((74,110),title,font=tf,fill=CREAM)
    return im,d

def save_meme_1():
    im,d=base_landscape("Your closet might be holding a blockchain node.","OLD HARDWARE, NEW JOB")
    draw_terminal(d,120,245,430,230)
    d.text((655,275),"DUSTY LAPTOP",font=font(31,True),fill=MUTED)
    d.text((655,325),"→",font=font(62,True),fill=ORANGE)
    d.text((735,330),"DRY-RUN",font=font(42,True),fill=GREEN)
    d.text((655,410),"Start with what you already own.",font=font(27),fill=WHITE)
    d.text((655,458),"pip install clawrtc",font=font(29,True),fill=GOLD)
    im.save(OUT/"meme_01_closet_node.png")

def save_meme_2():
    im,d=base_landscape("In RustChain, older hardware can earn the bigger multiplier.","PROOF OF ANTIQUITY")
    cards=[("PowerPC G4","2.5×",GREEN),("PowerPC G5","2.0×",GOLD),("Modern","1.0×",MUTED)]
    x=90
    for name,mult,c in cards:
        d.rounded_rectangle((x,250,x+300,505),28,fill=(28,33,38),outline=c,width=5)
        d.text((x+30,285),name,font=font(30,True),fill=CREAM)
        d.text((x+54,355),mult,font=font(72,True),fill=c)
        d.text((x+30,455),"reward weight",font=font(24),fill=MUTED)
        x+=360
    d.text((89,555),"Old ≠ obsolete. Physical continuity is the feature.",font=font(30,True),fill=WHITE)
    im.save(OUT/"meme_02_multiplier_scorecard.png")

def save_meme_3():
    im,d=base_landscape("Replace it—or give it one more job?","REUSE BEFORE REPLACE")
    d.rounded_rectangle((80,250,515,525),28,fill=(39,31,31),outline=ORANGE,width=4)
    d.text((125,280),"UPGRADE CYCLE",font=font(35,True),fill=ORANGE)
    d.text((125,350),"buy → replace → discard",font=font(29),fill=CREAM)
    d.text((125,410),"old hardware = waste?",font=font(28),fill=MUTED)
    d.rounded_rectangle((685,250,1120,525),28,fill=(24,39,30),outline=GREEN,width=4)
    d.text((725,280),"RUSTCHAIN",font=font(35,True),fill=GREEN)
    d.text((725,350),"prove → preserve → use",font=font(29),fill=CREAM)
    d.text((725,410),"old hardware = identity",font=font(28),fill=WHITE)
    center(d,"→",338,1200,font(72,True),GOLD)
    im.save(OUT/"meme_03_reuse_before_replace.png")

def save_meme_4():
    im,d=base_landscape("A GPU farm is not the only way to join a network.","ONE MACHINE IS A START")
    draw_chip(d,150,285,190,"CPU")
    d.text((410,292),"1 physical machine",font=font(40,True),fill=CREAM)
    d.text((410,355),"+ hardware fingerprint",font=font(34),fill=GREEN)
    d.text((410,410),"+ dry-run first",font=font(34),fill=GOLD)
    d.text((410,482),"= a real compatibility check",font=font(34,True),fill=WHITE)
    im.save(OUT/"meme_04_one_machine.png")

def save_meme_5():
    im,d=base_landscape("2009 called. It wants a second career.","VINTAGE COMPUTING")
    draw_terminal(d,120,245,430,230)
    d.text((660,275),"NEW JOB TITLE:",font=font(28,True),fill=ORANGE)
    d.text((660,325),"RustChain node",font=font(47,True),fill=GREEN)
    d.text((660,405),"First interview question:",font=font(25),fill=MUTED)
    d.text((660,445),"Can you pass the dry-run?",font=font(30,True),fill=CREAM)
    d.text((660,500),"No purchase required.",font=font(25),fill=WHITE)
    im.save(OUT/"meme_05_second_career.png")

VIDEO_W, VIDEO_H = 720, 1280

def video_frame(lines, subline, progress, accent, idx):
    im=Image.new("RGB",(VIDEO_W,VIDEO_H),BG); d=ImageDraw.Draw(im)
    # animated horizon/grid
    y0=910
    for i in range(7):
        y=y0+i*52
        d.line((0,y,VIDEO_W,y),fill=(25,45,35),width=2)
    for i in range(-5,6):
        x=VIDEO_W//2 + i*92
        d.line((VIDEO_W//2,y0,x,VIDEO_H),fill=(25,45,35),width=2)
    # status chip
    d.rounded_rectangle((44,54,676,126),22,fill=(27,32,36),outline=accent,width=3)
    d.text((70,76),f"RUSTCHAIN // STAGE 1 // {idx:02d}",font=font(24,True),fill=accent)
    # simple retro computer
    bob=int(math.sin(progress*math.pi*2)*7)
    draw_terminal(d,145,175+bob,430,260,accent)
    y=565
    for n,line in enumerate(lines):
        f=fit_text(d,line,620,56,34,True)
        center(d,line,y,VIDEO_W,f,CREAM if n==0 else WHITE)
        y+=90
    sf=fit_text(d,subline,620,34,24,False)
    center(d,subline,1045,VIDEO_W,sf,accent)
    # progress bar
    d.rounded_rectangle((70,1165,650,1185),10,fill=(46,52,56))
    d.rounded_rectangle((70,1165,70+int(580*progress),1185),10,fill=accent)
    d.text((70,1210),"rustchain.org",font=font(24,True),fill=MUTED)
    return im

def make_video(name, scenes, duration, accent, idx):
    fps=12
    frames=OUT/(name+"_frames")
    frames.mkdir(exist_ok=True)
    total=int(duration*fps)
    for i in range(total):
        p=i/(total-1)
        scene=min(int(p*len(scenes)),len(scenes)-1)
        local=(p*len(scenes))-scene
        lines,sub=scenes[scene]
        frame=video_frame(lines,sub,local,accent,idx)
        frame.save(frames/f"frame_{i:04d}.png", optimize=True)
    subprocess.run([
        "ffmpeg","-y","-loglevel","error","-framerate",str(fps),
        "-i",str(frames/"frame_%04d.png"),"-c:v","libx264","-pix_fmt","yuv420p",
        "-movflags","+faststart","-crf","23",str(OUT/(name+".mp4"))
    ],check=True)
    shutil.rmtree(frames)

save_meme_1(); save_meme_2(); save_meme_3(); save_meme_4(); save_meme_5()

make_video("short_01_closet_laptop",[
    (["That old laptop", "in your closet?"],"It may still have a job.") ,
    (["Proof of Antiquity", "rewards real hardware"],"Older hardware can carry a higher multiplier."),
    (["Start safely", "with a dry-run"],"pip install clawrtc")
],10,GREEN,1)

make_video("short_02_upgrade_rebellion",[
    (["The upgrade cycle says", "REPLACE IT"],"Newer. Faster. Again."),
    (["Proof of Antiquity says", "PROVE IT"],"Physical continuity counts."),
    (["G4 2.5×  •  G5 2.0×", "Modern 1.0×"],"Vintage hardware gets the twist."),
    (["Use what you own", "before buying more"],"rustchain.org")
],12,ORANGE,2)

make_video("short_03_one_machine",[
    (["You don't need", "a GPU farm"],"One physical machine is a start."),
    (["Run the fingerprint", "see what passes"],"Dry-run before mining."),
    (["Keep old hardware", "useful longer"],"pip install clawrtc")
],9,GOLD,3)

print("generated", len(list(OUT.iterdir())), "assets")
