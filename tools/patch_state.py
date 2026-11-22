#!/usr/bin/env python3
"""
patch_state.py -- patch CPU RAM inside a Nestopia savestate (poor man's
Game Genie). Lets us poke game-state variables and observe the effect.

    from patch_state import patch_ram, ram_snapshot
    new = patch_ram(state_bytes, {0x41: 0, 0x98: 1})
"""
from __future__ import annotations

import struct

from nest_state import parse_state, cpu_ram


def _ram_chunk_offset(buf: bytes) -> int:
    """Offset of the CPU RAM chunk's data (after tag+size+flag)."""
    sig = b"RAM\x00" + struct.pack("<I", 2049) + b"\x00"
    i = buf.find(sig)
    if i < 0:
        raise ValueError("CPU RAM chunk not found")
    return i + len(sig)


def patch_ram(buf: bytes, patches: dict[int, int]) -> bytes:
    b = bytearray(buf)
    base = _ram_chunk_offset(buf)
    for addr, val in patches.items():
        b[base + (addr & 0x7FF)] = val & 0xFF
    return bytes(b)


def ram_snapshot(buf: bytes) -> bytes:
    return cpu_ram(parse_state(buf))


if __name__ == "__main__":
    import sys
    data = open(sys.argv[1], "rb").read()
    out = sys.argv[2]
    patches = {}
    for spec in sys.argv[3:]:
        a, v = spec.split("=")
        patches[int(a.replace("$", ""), 16)] = int(v.replace("$", ""), 16)
    open(out, "wb").write(patch_ram(data, patches))
    print(f"patched {patches} -> {out}")
