#!/usr/bin/env python3
"""
nest_state.py -- walk Nestopia savestates.

Format (NO_COMPRESSION as used by the libretro core):
    chunk  = id:u32 (ascii tag little-endian, e.g. b"REG\\0") + size:u32 + payload
    nested = a payload that itself contains chunks

High-level chunks: NST wrapper -> NFO, CPU (REG,BUS,RAM,FRM,CLK...),
PPU (REG,PAL,OAM,NMT,...), IMG (board/mapper incl. CHR banking), PRT (input).

Gives us everything the libretro API hides: CPU registers (PC!),
palette RAM, OAM, nametables, mapper registers.
"""
from __future__ import annotations

import struct
import sys


def _tag(cid: int) -> str:
    return struct.pack("<I", cid).rstrip(b"\x00").decode("latin1")


def _is_ascii_tag(cid: int) -> bool:
    b = struct.pack("<I", cid)
    return b[0] != 0 and all((32 <= x < 127) or x in (0, 0x1A) for x in b)


def _parse(buf: bytes, off: int, end: int):
    """Parse chunk chain in [off,end). Returns (nodes, consumed_end).
    node = (tag, payload_or_None, children_or_None)"""
    nodes = []
    start = off
    while off + 8 <= end:
        cid, size = struct.unpack_from("<II", buf, off)
        if not _is_ascii_tag(cid):
            break
        poff = off + 8
        pend = poff + size
        if pend > end:
            break
        children, _ = _parse(buf, poff, pend)
        # children are containers iff they exactly tile the payload
        covered = 0
        for _, payload, ch in children:
            covered += 8 + (len(payload) if payload is not None else _size_of(ch))
        if children and poff + covered == pend:
            nodes.append((_tag(cid), None, children))
        else:
            nodes.append((_tag(cid), buf[poff:pend], None))
        off = pend
    return nodes, off


def _size_of(children) -> int:
    total = 0
    for _, payload, ch in children:
        total += 8 + (len(payload) if payload is not None else _size_of(ch))
    return total


def parse_state(buf: bytes):
    """-> (tag, payload, children) for the top NST chunk"""
    nodes, _ = _parse(buf, 0, len(buf))
    return nodes[0] if nodes else None


def _index(children):
    return {tag: (payload, ch) for tag, payload, ch in children}


def find(node, *path):
    """Navigate (tag,payload,children) tree by tag path; return dict index or payload."""
    _, _, children = node
    idx = _index(children)
    for i, p in enumerate(path):
        if p not in idx:
            return None
        payload, ch = idx[p]
        if i == len(path) - 1:
            return payload if payload is not None else _index(ch)
        node = (p, payload, ch)
        _, _, children = node
        idx = _index(children)
    return idx


def decompress_chunk(payload):
    """Compress() chunks: 1 byte flag (0=raw,1=zlib) + data."""
    if payload is None:
        return None
    if payload[0] == 0:
        return payload[1:]
    if payload[0] == 1:
        import zlib
        return zlib.decompress(payload[1:])
    return payload  # not a compressed chunk (plain Write) -> raw


def cpu_regs(state):
    reg = find(state, "CPU", "REG")
    if isinstance(reg, dict):
        reg = reg.get("REG")
    if reg is None:
        return None
    data = reg if isinstance(reg, (bytes, bytearray)) else reg[0]
    pc, sp, a, x, y, f = struct.unpack("<HBBBBB", data[:7])
    return dict(pc=pc, sp=sp, a=a, x=x, y=y, f=f)


def cpu_ram(state):
    ram = find(state, "CPU", "RAM")
    if isinstance(ram, dict):
        ram = ram.get("RAM")
    data = ram if isinstance(ram, (bytes, bytearray)) else (ram[0] if ram else None)
    return decompress_chunk(data)


def ppu_dump(state):
    out = {}
    idx = find(state, "PPU")
    if isinstance(idx, dict):
        for key, want in (("PAL", "palette"), ("OAM", "oam"), ("NMT", "nametable")):
            if key in idx and idx[key][0] is not None:
                out[want] = decompress_chunk(idx[key][0])
    return out


def pretty(state, depth=0):
    tag, payload, children = state
    n = len(payload) if payload is not None else "-"
    print("  " * depth + f"{tag}  ({n})")
    if children:
        for ch in children:
            pretty(ch, depth + 1)


if __name__ == "__main__":
    buf = open(sys.argv[1], "rb").read()
    state = parse_state(buf)
    pretty(state)
    regs = cpu_regs(state)
    print("CPU:", {k: (hex(v) if k in ("pc", "f") else v) for k, v in regs.items()} if regs else None)
    ram = cpu_ram(state)
    print("CPU RAM:", len(ram) if ram else 0, "bytes")
    for k, v in ppu_dump(state).items():
        print(f"PPU {k}: {len(v)} bytes")
