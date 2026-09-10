#!/usr/bin/env bash
set -euo pipefail
sudo apt-get update
sudo apt-get install -y git make gcc g++ python3 libsdl2-dev libglew-dev zlib1g-dev libpng-dev libgtk-3-dev libzstd-dev
rm -rf genesis blastem

git clone https://github.com/Scottcjn/legend-of-elya-genesis.git genesis
cd genesis
git rev-parse HEAD | tee ../GENESIS_HEAD.txt
cd ..

git clone --depth 1 https://github.com/libretro/blastem.git blastem
cd blastem
git rev-parse HEAD | tee ../BLASTEM_HEAD.txt
make -j2
cd ..

mkdir -p evidence
find genesis/bench genesis/host genesis/tools genesis/mamework -maxdepth 3 -type f 2>/dev/null | sort > evidence/benchmark-files.txt || true
grep -RInE 'bench_marker|bench_status|bench_ntok|bench_tok|Call me Sophia Elya|220579814|142972761' genesis/bench genesis/host genesis/tools genesis/mamework genesis/docs 2>/dev/null | head -400 > evidence/benchmark-grep.txt || true
grep -RInE 'cycle|cycles|debugger|breakpoint|watchpoint|trace' blastem/*.c blastem/*.h 2>/dev/null | head -800 > evidence/blastem-debugger-grep.txt || true

python3 - <<'PY'
from pathlib import Path
text=Path('evidence/blastem-debugger-grep.txt').read_text(errors='ignore').lower()
found={k:text.count(k) for k in ['cycle','debugger','breakpoint','watchpoint','trace']}
Path('evidence/feasibility.txt').write_text(str(found)+'\n')
print(found)
if found['cycle']==0 or (found['breakpoint']+found['watchpoint']+found['trace'])==0:
    raise SystemExit('FAIL_CLOSED: BlastEm source probe did not expose a defensible emulator-native timing/control path')
PY
