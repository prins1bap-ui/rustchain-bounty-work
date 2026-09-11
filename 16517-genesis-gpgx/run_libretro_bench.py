#!/usr/bin/env python3
import argparse, ctypes, json, pathlib, re, sys

RETRO_MEMORY_SYSTEM_RAM = 2

class RetroGameInfo(ctypes.Structure):
    _fields_ = [
        ("path", ctypes.c_char_p),
        ("data", ctypes.c_void_p),
        ("size", ctypes.c_size_t),
        ("meta", ctypes.c_char_p),
    ]

ENV = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_uint, ctypes.c_void_p)
VIDEO = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_size_t)
AUDIO = ctypes.CFUNCTYPE(None, ctypes.c_int16, ctypes.c_int16)
AUDIO_BATCH = ctypes.CFUNCTYPE(ctypes.c_size_t, ctypes.POINTER(ctypes.c_int16), ctypes.c_size_t)
INPUT_POLL = ctypes.CFUNCTYPE(None)
INPUT_STATE = ctypes.CFUNCTYPE(ctypes.c_int16, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint)

def parse_symbols(path):
    out = {}
    for line in pathlib.Path(path).read_text(errors="replace").splitlines():
        for name in ("bench_marker", "bench_expert", "bench_status", "bench_ntok", "bench_tok"):
            if name not in line:
                continue
            m = re.search(r"(?:0x)?([0-9A-Fa-f]{6,8})", line)
            if m:
                out[name] = int(m.group(1), 16)
                break
    missing = [k for k in ("bench_marker", "bench_expert", "bench_status", "bench_ntok", "bench_tok") if k not in out]
    if missing:
        raise RuntimeError(f"missing symbols: {missing}")
    return out

def be16(buf, off):
    return (buf[off] << 8) | buf[off + 1]

def be32(buf, off):
    return (be16(buf, off) << 16) | be16(buf, off + 2)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--core", required=True)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--symbols", required=True)
    ap.add_argument("--max-frames", type=int, default=36000)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    syms = parse_symbols(args.symbols)
    offs = {k: (v & 0xFFFF) for k, v in syms.items()}
    core = ctypes.CDLL(str(pathlib.Path(args.core).resolve()))

    @ENV
    def env_cb(cmd, data):
        # The benchmark needs no frontend services. Unsupported optional
        # environment commands are deliberately rejected, as libretro permits.
        return False
    @VIDEO
    def video_cb(data, width, height, pitch):
        return None
    @AUDIO
    def audio_cb(left, right):
        return None
    @AUDIO_BATCH
    def audio_batch_cb(data, frames):
        return frames
    @INPUT_POLL
    def input_poll_cb():
        return None
    @INPUT_STATE
    def input_state_cb(port, device, index, ident):
        return 0

    core.retro_set_environment.argtypes = [ENV]
    core.retro_set_video_refresh.argtypes = [VIDEO]
    core.retro_set_audio_sample.argtypes = [AUDIO]
    core.retro_set_audio_sample_batch.argtypes = [AUDIO_BATCH]
    core.retro_set_input_poll.argtypes = [INPUT_POLL]
    core.retro_set_input_state.argtypes = [INPUT_STATE]
    core.retro_load_game.argtypes = [ctypes.POINTER(RetroGameInfo)]
    core.retro_load_game.restype = ctypes.c_bool
    core.retro_get_memory_data.argtypes = [ctypes.c_uint]
    core.retro_get_memory_data.restype = ctypes.c_void_p
    core.retro_get_memory_size.argtypes = [ctypes.c_uint]
    core.retro_get_memory_size.restype = ctypes.c_size_t

    core.retro_set_environment(env_cb)
    core.retro_set_video_refresh(video_cb)
    core.retro_set_audio_sample(audio_cb)
    core.retro_set_audio_sample_batch(audio_batch_cb)
    core.retro_set_input_poll(input_poll_cb)
    core.retro_set_input_state(input_state_cb)
    core.retro_init()

    rom = pathlib.Path(args.rom).read_bytes()
    rom_buf = ctypes.create_string_buffer(rom)
    gi = RetroGameInfo(None, ctypes.cast(rom_buf, ctypes.c_void_p), len(rom), None)
    if not core.retro_load_game(ctypes.byref(gi)):
        raise RuntimeError("retro_load_game returned false")

    ram_ptr = core.retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM)
    ram_size = int(core.retro_get_memory_size(RETRO_MEMORY_SYSTEM_RAM))
    if not ram_ptr or ram_size < 0x10000:
        raise RuntimeError(f"system RAM unavailable/too small: ptr={ram_ptr} size={ram_size}")
    ram = (ctypes.c_uint8 * ram_size).from_address(ram_ptr)

    marker_seen = []
    done_frame = None
    for frame in range(args.max_frames):
        core.retro_run()
        marker = be32(ram, offs["bench_marker"])
        if not marker_seen or marker_seen[-1] != marker:
            marker_seen.append(marker)
        if marker == 4:
            done_frame = frame + 1
            break

    status = int(ram[offs["bench_status"]])
    ntok = int(ram[offs["bench_ntok"]])
    expert = be16(ram, offs["bench_expert"])
    tokens = [int(ram[offs["bench_tok"] + i]) for i in range(min(ntok, 64))]
    result = {
        "done_frame": done_frame,
        "ram_size": ram_size,
        "symbols": {k: f"0x{v:08X}" for k, v in syms.items()},
        "offsets": {k: f"0x{v:04X}" for k, v in offs.items()},
        "marker_transitions": marker_seen,
        "status": status,
        "ntok": ntok,
        "expert": expert,
        "tokens": tokens,
    }
    pathlib.Path(args.out).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

    core.retro_unload_game()
    core.retro_deinit()

    if done_frame is None:
        print("FAIL: benchmark did not reach marker=4", file=sys.stderr)
        return 2
    if status != 0x5A:
        print(f"FAIL: bench_status=0x{status:02X}, expected 0x5A", file=sys.stderr)
        return 3
    if ntok < 16:
        print(f"FAIL: only {ntok} tokens, need >=16", file=sys.stderr)
        return 4
    print("EXECUTION_QA=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
