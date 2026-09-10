#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: instrument_blastem.py <m68k_util.c> <watch_addr>")

path = Path(sys.argv[1])
watch = sys.argv[2]
s = path.read_text()

if '#include <stdio.h>' not in s:
    # Put stdio with the other standard headers if possible.
    if '#include <string.h>\n' in s:
        s = s.replace('#include <string.h>\n', '#include <string.h>\n#include <stdio.h>\n', 1)
    else:
        s = '#include <stdio.h>\n' + s

# Current BlastEm has changed this helper over time. Anchor on the function
# and the address calculation rather than one exact adjacent-line sequence.
fn = re.search(r'void\s+m68k_write_16\s*\(m68k_context\s*\*\s*context\s*\)\s*\{', s)
if not fn:
    raise SystemExit('BlastEm m68k_write_16 function not found')

start = fn.end()
next_fn = re.search(r'\n(?:void|uint\w*|int\w*|static)\s+\w+\s*\(', s[start:])
end = start + (next_fn.start() if next_fn else len(s) - start)
body = s[start:end]

addr_re = re.compile(r'(?P<indent>[ \t]*)int32_t\s+address\s*=\s*context->scratch2\s*&\s*context->opts->gen\.address_mask\s*;')
m = addr_re.search(body)
if not m:
    raise SystemExit('BlastEm m68k_write_16 address calculation not found')

indent = m.group('indent')
instrument = (
    f"\n{indent}if ((address & 0xFFFFFF) == {watch}) {{\n"
    f"{indent}\tfprintf(stderr, \"RTCWATCH value=0x%04X master_cycles=%u\\n\", "
    f"(unsigned)(context->scratch1 & 0xFFFF), (unsigned)context->cycles);\n"
    f"{indent}\tfflush(stderr);\n"
    f"{indent}}}"
)
insert_at = start + m.end()
s = s[:insert_at] + instrument + s[insert_at:]
path.write_text(s)
print(f'instrumented {path} for marker write address {watch}')
