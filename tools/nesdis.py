#!/usr/bin/env python3
"""
nesdis.py - 6502 disassembler with recursive code tracing for the Gradius ROM.

    ./tools/nesdis.py --rom "Gradius (USA).nes" --out docs/disassembly

Why a tracer and not a linear sweep: half of a NES PRG bank is data (level
layouts, palettes, sine tables, enemy scripts).  A linear sweep disassembles
data as instructions and produces pages of nonsense, which makes the listing
useless for porting.  So we start at the reset/NMI/IRQ vectors and follow
control flow (JSR, JMP, every branch), marking each byte as code or data.
Whatever is never reached is left as data, which is exactly the bias we want:
a false data byte costs one table to hand-read, a false instruction costs a
wrong port.

Output:
    docs/disassembly/bank0.asm    traced code, data as .byte runs
    docs/disassembly/bank1.asm
    docs/disassembly/xref.txt     JSR targets (candidate functions) + callers
    docs/disassembly/trace.json   machine-readable map for other tools
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# --------------------------------------------------------------------------- #
# 6502 opcode table: opcode -> (mnemonic, addressing mode)
# --------------------------------------------------------------------------- #

MODES = ("imp", "acc", "imm", "zp", "zpx", "zpy", "abs", "absx", "absy",
         "ind", "indx", "indy", "rel")

OPS: dict[int, tuple[str, str]] = {}


def _def(opc, name, mode):
    OPS[opc] = (name, mode)


for opc, name, mode in [
    (0x00, "BRK", "imp"), (0x01, "ORA", "indx"), (0x05, "ORA", "zp"),
    (0x06, "ASL", "zp"), (0x08, "PHP", "imp"), (0x09, "ORA", "imm"),
    (0x0A, "ASL", "acc"), (0x0D, "ORA", "abs"), (0x0E, "ASL", "abs"),
    (0x10, "BPL", "rel"), (0x11, "ORA", "indy"), (0x15, "ORA", "zpx"),
    (0x16, "ASL", "zpx"), (0x18, "CLC", "imp"), (0x19, "ORA", "absy"),
    (0x1D, "ORA", "absx"), (0x1E, "ASL", "absx"),
    (0x20, "JSR", "abs"), (0x21, "AND", "indx"), (0x24, "BIT", "zp"),
    (0x25, "AND", "zp"), (0x26, "ROL", "zp"), (0x28, "PLP", "imp"),
    (0x29, "AND", "imm"), (0x2A, "ROL", "acc"), (0x2C, "BIT", "abs"),
    (0x2D, "AND", "abs"), (0x2E, "ROL", "abs"), (0x30, "BMI", "rel"),
    (0x31, "AND", "indy"), (0x35, "AND", "zpx"), (0x36, "ROL", "zpx"),
    (0x38, "SEC", "imp"), (0x39, "AND", "absy"), (0x3D, "AND", "absx"),
    (0x3E, "ROL", "absx"),
    (0x40, "RTI", "imp"), (0x41, "EOR", "indx"), (0x45, "EOR", "zp"),
    (0x46, "LSR", "zp"), (0x48, "PHA", "imp"), (0x49, "EOR", "imm"),
    (0x4A, "LSR", "acc"), (0x4C, "JMP", "abs"), (0x4D, "EOR", "abs"),
    (0x4E, "LSR", "abs"), (0x50, "BVC", "rel"), (0x51, "EOR", "indy"),
    (0x55, "EOR", "zpx"), (0x56, "LSR", "zpx"), (0x58, "CLI", "imp"),
    (0x59, "EOR", "absy"), (0x5D, "EOR", "absx"), (0x5E, "LSR", "absx"),
    (0x60, "RTS", "imp"), (0x61, "ADC", "indx"), (0x65, "ADC", "zp"),
    (0x66, "ROR", "zp"), (0x68, "PLA", "imp"), (0x69, "ADC", "imm"),
    (0x6A, "ROR", "acc"), (0x6C, "JMP", "ind"), (0x6D, "ADC", "abs"),
    (0x6E, "ROR", "abs"), (0x70, "BVS", "rel"), (0x71, "ADC", "indy"),
    (0x75, "ADC", "zpx"), (0x76, "ROR", "zpx"), (0x78, "SEI", "imp"),
    (0x79, "ADC", "absy"), (0x7D, "ADC", "absx"), (0x7E, "ROR", "absx"),
    (0x81, "STA", "indx"), (0x84, "STY", "zp"), (0x85, "STA", "zp"),
    (0x86, "STX", "zp"), (0x88, "DEY", "imp"), (0x8A, "TXA", "imp"),
    (0x8C, "STY", "abs"), (0x8D, "STA", "abs"), (0x8E, "STX", "abs"),
    (0x90, "BCC", "rel"), (0x91, "STA", "indy"), (0x94, "STY", "zpx"),
    (0x95, "STA", "zpx"), (0x96, "STX", "zpy"), (0x98, "TYA", "imp"),
    (0x99, "STA", "absy"), (0x9A, "TXS", "imp"), (0x9D, "STA", "absx"),
    (0xA0, "LDY", "imm"), (0xA1, "LDA", "indx"), (0xA2, "LDX", "imm"),
    (0xA4, "LDY", "zp"), (0xA5, "LDA", "zp"), (0xA6, "LDX", "zp"),
    (0xA8, "TAY", "imp"), (0xA9, "LDA", "imm"), (0xAA, "TAX", "imp"),
    (0xAC, "LDY", "abs"), (0xAD, "LDA", "abs"), (0xAE, "LDX", "abs"),
    (0xB0, "BCS", "rel"), (0xB1, "LDA", "indy"), (0xB4, "LDY", "zpx"),
    (0xB5, "LDA", "zpx"), (0xB6, "LDX", "zpy"), (0xB8, "CLV", "imp"),
    (0xB9, "LDA", "absy"), (0xBA, "TSX", "imp"), (0xBC, "LDY", "absx"),
    (0xBD, "LDA", "absx"), (0xBE, "LDX", "absy"),
    (0xC0, "CPY", "imm"), (0xC1, "CMP", "indx"), (0xC4, "CPY", "zp"),
    (0xC5, "CMP", "zp"), (0xC6, "DEC", "zp"), (0xC8, "INY", "imp"),
    (0xC9, "CMP", "imm"), (0xCA, "DEX", "imp"), (0xCC, "CPY", "abs"),
    (0xCD, "CMP", "abs"), (0xCE, "DEC", "abs"), (0xD0, "BNE", "rel"),
    (0xD1, "CMP", "indy"), (0xD5, "CMP", "zpx"), (0xD6, "DEC", "zpx"),
    (0xD8, "CLD", "imp"), (0xD9, "CMP", "absy"), (0xDD, "CMP", "absx"),
    (0xDE, "DEC", "absx"),
    (0xE0, "CPX", "imm"), (0xE1, "SBC", "indx"), (0xE4, "CPX", "zp"),
    (0xE5, "SBC", "zp"), (0xE6, "INC", "zp"), (0xE8, "INX", "imp"),
    (0xE9, "SBC", "imm"), (0xEA, "NOP", "imp"), (0xEC, "CPX", "abs"),
    (0xED, "SBC", "abs"), (0xEE, "INC", "abs"), (0xF0, "BEQ", "rel"),
    (0xF1, "SBC", "indy"), (0xF5, "SBC", "zpx"), (0xF6, "INC", "zpx"),
    (0xF8, "SED", "imp"), (0xF9, "SBC", "absy"), (0xFD, "SBC", "absx"),
    (0xFE, "INC", "absx"),
]:
    _def(opc, name, mode)

# unofficial opcodes - their size matters for the sweep even if we never emit them
for opc in range(256):
    if opc not in OPS:
        OPS[opc] = ("???", "imp")

SIZE = {"imp": 1, "acc": 1, "imm": 2, "zp": 2, "zpx": 2, "zpy": 2,
        "abs": 3, "absx": 3, "absy": 3, "ind": 3, "indx": 2, "indy": 2,
        "rel": 2}


class Space:
    """A 64 KiB view of the CPU address space.

    The cart is CNROM: $C000-$FFFF is fixed to PRG bank 1 while
    $8000-$BFFF is switchable.  A single view therefore pins bank 1 high and
    swaps which bank sits low, and tracing is run once per view so that code
    in either bank gets found.
    """

    def __init__(self, name: str, low_name: str, low: bytes, fixed: bytes):
        self.name = name
        self.low_name = low_name
        self.data: dict[int, int] = {}
        for i, b in enumerate(low):
            self.data[0x8000 + i] = b
        for i, b in enumerate(fixed):
            self.data[0xC000 + i] = b
        self.code = bytearray(0x10000)        # 1 = instruction start
        self.code_bytes = bytearray(0x10000)
        self.src = {}                          # addr -> (bank name, offset)
        for i in range(0x4000):
            self.src[0x8000 + i] = (low_name, i)
            self.src[0xC000 + i] = ("bank1", i)
        self.labels: dict[int, str] = {}
        self.xref: dict[int, set[int]] = {}

    def byte(self, addr: int) -> int:
        return self.data[addr]

    def in_bank(self, addr: int) -> bool:
        return addr in self.data


def decode(bank: Space, addr: int):
    """Return (mnemonic, mode, operand, size) or None for an invalid opcode."""
    opc = bank.byte(addr)
    name, mode = OPS[opc]
    if name == "???":
        return None
    size = SIZE[mode]
    if not bank.in_bank(addr + size - 1):
        return None
    if mode in ("imm", "zp", "zpx", "zpy", "indx", "indy", "rel"):
        operand = bank.byte(addr + 1)
    elif mode in ("abs", "absx", "absy", "ind"):
        operand = bank.byte(addr + 1) | (bank.byte(addr + 2) << 8)
    else:
        operand = None
    return name, mode, operand, size


def format_operand(name: str, mode: str, operand, addr: int, size: int,
                   labels: dict[int, str]) -> str:
    def lab(v):
        return labels.get(v, "$%04X" % v)

    if mode == "imp":
        return ""
    if mode == "acc":
        return "A"
    if mode == "imm":
        return "#$%02X" % operand
    if mode == "zp":
        return lab(operand)
    if mode == "zpx":
        return "%s,X" % lab(operand)
    if mode == "zpy":
        return "%s,Y" % lab(operand)
    if mode == "abs":
        return lab(operand)
    if mode == "absx":
        return "%s,X" % lab(operand)
    if mode == "absy":
        return "%s,Y" % lab(operand)
    if mode == "ind":
        return "(%s)" % lab(operand)
    if mode == "indx":
        return "(%s,X)" % lab(operand)
    if mode == "indy":
        return "(%s),Y" % lab(operand)
    if mode == "rel":
        target = (addr + size + ((operand ^ 0x80) - 0x80)) & 0xFFFF
        return lab(target)
    return "?"


# --------------------------------------------------------------------------- #
# Recursive tracing
# --------------------------------------------------------------------------- #

BRANCHES = {"BPL", "BMI", "BVC", "BVS", "BCC", "BCS", "BNE", "BEQ"}
STOPS = {"RTS", "RTI", "BRK"}


def trace(bank: Space, entries, max_instructions: int = 4_000_000) -> int:
    """Mark every instruction reachable from `entries`.

    One shared work queue for all entry points: seeding hundreds of addresses
    (the ROM dispatches through jump tables, so call targets in data are not
    otherwise discoverable) then re-walking from each would be quadratic.
    """
    work = [e for e in entries if bank.in_bank(e)]
    seen_entries: set[int] = set()
    count = 0

    while work:
        addr = work.pop()
        while True:
            if count > max_instructions:
                return count
            if not bank.in_bank(addr) or addr in seen_entries:
                break
            ins = decode(bank, addr)
            if ins is None:
                break                    # invalid opcode: we fell into data
            name, mode, operand, size = ins

            seen_entries.add(addr)
            for i in range(size):
                bank.code[addr + i] = 1
            count += 1

            if name == "JSR":
                bank.xref.setdefault(operand, set()).add(addr)
                bank.labels.setdefault(operand, "sub_%04X" % operand)
                work.append(operand)
            elif name == "JMP" and mode == "abs":
                target = operand
                if target == addr:
                    break                # tight self-jump: idle loop
                bank.xref.setdefault(target, set()).add(addr)
                if bank.in_bank(target):
                    addr = target
                    continue
                break
            elif name in BRANCHES:
                target = (addr + size + ((operand ^ 0x80) - 0x80)) & 0xFFFF
                bank.xref.setdefault(target, set()).add(addr)
                if bank.in_bank(target):
                    work.append(target)
            elif name in STOPS:
                break
            elif name == "JMP" and mode == "ind":
                node = operand & 0xFF   # indirect jump through RAM/JT: opaque
                bank.labels.setdefault(node, "jmp_ind_%02X" % node)
                break

            addr += size
    return count


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #

def emit_listing(space: Space, path: str, which: str) -> None:
    """Write the traced listing for one region: 'low' ($8000-$BFFF) or 'high'."""
    lo, hi = (0x8000, 0xC000) if which == "low" else (0xC000, 0x10000)
    bank_name = space.low_name if which == "low" else "bank1"
    lines = [f"; {bank_name}: ${lo:04X}-${hi - 1:04X}  (CPU view: low bank = {space.low_name})",
             "; generated by tools/nesdis.py - traced code, everything else left as data",
             ""]
    i = lo
    while i < hi:
        if space.code[i]:
            ins = decode(space, i)
            if ins:
                name, mode, operand, size = ins
                raw = " ".join("%02X" % space.data[i + k] for k in range(size))
                text = format_operand(name, mode, operand, i, size, space.labels)
                label = ""
                if i in space.labels:
                    label = space.labels[i] + ":"
                note = ""
                if i in space.xref:
                    note = "   ; <- " + ", ".join("$%04X" % s for s in sorted(space.xref[i])[:4])
                lines.append(f"{label:<12s} {i:04X}  {raw:<9s} {name} {text}{note}")
                i += size
                continue
        j = i
        while j < hi and not space.code[j]:
            j += 1
        for k in range(i, j, 16):
            piece = [space.data[a] for a in range(k, min(k + 16, j))]
            lines.append("             %04X  " % k + " ".join("%02X" % b for b in piece))
            lines.append("                        .byte " + ",".join("$%02X" % b for b in piece))
        i = j
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", default="Gradius (USA).nes")
    ap.add_argument("--out", default="docs/disassembly")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--seed", action="append", default=[], metavar="ADDR",
                    help="extra trace entry point (hex), repeatable; needed for "
                         "code reached only through jump tables")
    args = ap.parse_args(argv)

    rom = open(args.rom, "rb").read()
    prg_size = rom[4] * 16384
    prg = rom[16:16 + prg_size]
    count = prg_size // 0x4000
    banks = [prg[i * 0x4000:(i + 1) * 0x4000] for i in range(count)]
    fixed = banks[-1]                      # $C000-$FFFF is bank 1 on CNROM

    os.makedirs(args.out, exist_ok=True)
    report = {"rom": os.path.basename(args.rom), "prg_size": prg_size,
              "mapper": 3, "views": []}

    # One trace per possible low-bank mapping, merging what is found.
    merged = Space("merged", "bank0", banks[0], fixed)
    for low in range(max(1, count - 1)):
        view = Space(f"view{low}", f"bank{low}", banks[low], fixed)
        vecs = {}
        for name, off in (("NMI", 0xFFFA), ("RESET", 0xFFFC), ("IRQ", 0xFFFE)):
            vecs[name] = fixed[off - 0xC000] | (fixed[off - 0xC000 + 1] << 8)
        # the bank-1 code that the vectors enter is identical in every view,
        # so trace it once per view and let the merge dedupe
        seeds = [int(x, 16) for x in args.seed]
        total = trace(view, list(vecs.values()) + seeds)
        for a in range(0x10000):
            if view.code[a]:
                merged.code[a] = 1
        merged.labels.update({a: l for a, l in view.labels.items() if a not in merged.labels})
        for a, callers in view.xref.items():
            merged.xref.setdefault(a, set()).update(callers)
        report["views"].append({
            "low_bank": low,
            "vectors": {k: "0x%04X" % v for k, v in vecs.items()},
            "instructions": total,
        })
        if not args.quiet:
            print(f"view: low=bank{low}  vectors " +
                  ", ".join(f"{k}=${v:04X}" for k, v in vecs.items()) +
                  f"  -> {total} instructions")

    emit_listing(merged, os.path.join(args.out, "bank1.asm"), "high")
    # low region: emit every bank separately, using the merged code map where
    # it applies to that bank
    for b in range(max(1, count - 1)):
        view = Space(f"view{b}", f"bank{b}", banks[b], fixed)
        for a in range(0x8000, 0xC000):
            view.code[a] = merged.code[a]
        view.labels = merged.labels
        view.xref = merged.xref
        emit_listing(view, os.path.join(args.out, f"bank{b}_low.asm"), "low")

    # Machine-readable instruction list: every analysis (RAM map, call graph,
    # RAM-watch design) reads this rather than re-parsing the listing text.
    insns = []
    for a in range(0x8000, 0x10000):
        if not merged.code[a]:
            continue
        ins = decode(merged, a)
        if not ins:
            continue
        name, mode, operand, size = ins
        target = None
        if mode == "rel":
            target = (a + size + ((operand ^ 0x80) - 0x80)) & 0xFFFF
        elif mode in ("abs", "absx", "absy") and name in ("JSR", "JMP", "BRA"):
            target = operand
        insns.append({
            "addr": "0x%04X" % a, "bank": merged.src[a][0],
            "bytes": "".join("%02X" % merged.data[a + k] for k in range(size)),
            "op": name, "mode": mode,
            "operand": operand, "target": target,
            "text": format_operand(name, mode, operand, a, size, merged.labels),
        })
    with open(os.path.join(args.out, "instructions.json"), "w") as f:
        json.dump({"count": len(insns), "instructions": insns}, f, indent=0)

    high_code = sum(merged.code[0xC000:0x10000])
    low_code = sum(merged.code[0x8000:0xC000])
    report["high_code_bytes"] = high_code
    report["low_code_bytes"] = low_code
    report["subroutines"] = {("0x%04X" % a): len(c)
                             for a, c in sorted(merged.xref.items())}
    with open(os.path.join(args.out, "trace.json"), "w") as f:
        json.dump(report, f, indent=1)

    with open(os.path.join(args.out, "xref.txt"), "w") as f:
        f.write("JSR/branch targets and their callers\n\n")
        for target in sorted(merged.xref):
            callers = ", ".join("$%04X" % s for s in sorted(merged.xref[target])[:8])
            f.write(f"${target:04X} <- {callers}\n")

    if not args.quiet:
        print(f"code found: ${high_code} bytes at $C000+, {low_code} bytes at $8000+")
        print(f"wrote {args.out}/bank1.asm, bank*_low.asm, xref.txt, trace.json,"
              f" instructions.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
