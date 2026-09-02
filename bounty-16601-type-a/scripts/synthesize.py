from pathlib import Path
import re, subprocess
root=Path(__file__).resolve().parents[1]
for old in (root/'voiceover').glob('*.wav'):
    old.unlink()
text=(root/'script.md').read_text()
parts=re.split(r'\n## ', text)[1:]
names=['hook','consensus','checks','multipliers','flow','interpretation','close']
if len(parts) != len(names):
    raise SystemExit(f'expected 7 script sections, found {len(parts)}')
for i,(part,name) in enumerate(zip(parts,names),1):
    lines=part.splitlines()
    body=' '.join(x.strip() for x in lines[1:] if x.strip())
    body=re.sub(r'[`*_#]','',body)
    subprocess.run(['espeak','-s','145','-w',str(root/'voiceover'/f'{i:02d}_{name}.wav'),body],check=True)