#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: instrument_blastem.py <genesis.c> <marker_addr>")

path = Path(sys.argv[1])
marker = int(sys.argv[2], 0) & 0xFFFFFF
# bench_marker is u32. Small marker values live in the low 16 bits at +2 on 68000.
watch_off = (marker + 2) & 0xFFFF
s = path.read_text()

if '#include <stdio.h>' not in s:
    if '#include <string.h>\n' in s:
        s = s.replace('#include <string.h>\n', '#include <string.h>\n#include <stdio.h>\n', 1)
    else:
        s = '#include <stdio.h>\n' + s

anchor = 'static memmap_chunk base_map[] = {\n'
if anchor not in s:
    raise SystemExit('BlastEm Genesis base_map not found')

helpers = f'''/* RTC bounty #16517 measurement shim.
 * Genesis work RAM is normally direct-mapped by BlastEm's JIT, so generic
 * m68k_write_16 hooks do not see these writes. For this measurement build,
 * route RAM writes through callbacks while leaving reads direct-mapped.
 * The callbacks preserve RAM semantics and only emit the marker low word.
 */
static void *rtc_ram_write16(uint32_t address, void *vcontext, uint16_t value)
{{
    m68k_context *context = (m68k_context *)vcontext;
    genesis_context *gen = (genesis_context *)current_system;
    uint32_t off = address & 0xFFFF;
    gen->work_ram[off >> 1] = value;
    if (off == 0x{watch_off:04X}) {{
        fprintf(stderr, "RTCWATCH value=0x%04X master_cycles=%u\\n", (unsigned)value, (unsigned)context->cycles);
        fflush(stderr);
    }}
    return context;
}}

static void *rtc_ram_write8(uint32_t address, void *vcontext, uint8_t value)
{{
    m68k_context *context = (m68k_context *)vcontext;
    genesis_context *gen = (genesis_context *)current_system;
    uint32_t off = address & 0xFFFF;
    /* 68000 byte addressing is swapped within host uint16_t storage. */
    ((uint8_t *)gen->work_ram)[off ^ 1] = value;
    return context;
}}

'''
s = s.replace(anchor, helpers + anchor, 1)
old = '{0xE00000, 0x1000000, 0xFFFF, .flags = MMAP_READ | MMAP_WRITE | MMAP_CODE},'
new = '{0xE00000, 0x1000000, 0xFFFF, .flags = MMAP_READ | MMAP_CODE, .write_16 = rtc_ram_write16, .write_8 = rtc_ram_write8},'
if old not in s:
    raise SystemExit('BlastEm Genesis work-RAM map entry not found')
s = s.replace(old, new, 1)
path.write_text(s)
print(f'instrumented {path}: marker=0x{marker:06X}, low-word offset=0x{watch_off:04X}')
