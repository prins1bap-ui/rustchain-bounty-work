from pathlib import Path
from PIL import Image
import wave, re, sys
root=Path(__file__).resolve().parents[1]
required=['README.md','script.md','assembly.md','metadata.md','SOURCES.md','VERIFY.md','voiceover/ENGINE.md']
errors=[]
for p in required:
    if not (root/p).exists(): errors.append('missing '+p)
vis=sorted((root/'visuals').glob('*.png')); thumbs=sorted((root/'thumbnails').glob('*.png')); wavs=sorted((root/'voiceover').glob('*.wav'))
if len(vis)<7: errors.append(f'visuals={len(vis)} < 7')
if len(thumbs)!=3: errors.append(f'thumbnails={len(thumbs)} != 3')
if len(wavs)!=7: errors.append(f'voiceovers={len(wavs)} != 7')
for p in vis:
    if Image.open(p).size!=(1920,1080): errors.append(f'{p.name} wrong size')
for p in thumbs:
    if Image.open(p).size!=(1280,720): errors.append(f'{p.name} wrong size')
dur=0
for p in wavs:
    with wave.open(str(p),'rb') as w: dur += w.getnframes()/w.getframerate()
script=(root/'script.md').read_text()
words=len(re.findall(r"\b[\w’'-]+\b",script))
print(f'script_words={words}')
print(f'voiceover_sections={len(wavs)}')
print(f'voiceover_duration_seconds={dur:.2f}')
print(f'visuals={len(vis)} at 1920x1080')
print(f'thumbnails={len(thumbs)} at 1280x720')
print('source_lock_present=', '5a9d6a8a190008446d4f6c5ed2358bde532ba325' in (root/'SOURCES.md').read_text())
if dur<180 or dur>480: errors.append(f'duration {dur:.2f}s outside 3–8 min')
if errors:
    print('FAIL'); print('\n'.join(errors)); sys.exit(1)
print('PASS')