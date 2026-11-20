#!/usr/bin/env python3
"""
palette_probe.py - recover an emulator's 64-entry NES palette table.

The NES PPU does not output RGB.  It outputs an index into a palette (the
"$3F00 table"), whose 6-bit value means a voltage level on each of three
channels; how that voltage becomes a colour depends on the TV (composite,
RF) and on the emulator's chosen palette table.  Two emulators can render
identical PPU output with completely different RGB - so before pixels can be
used as a reference, the palette has to be pinned and written down.

This script writes a tiny NES program that fills the screen with each of the
64 palette entries in turn, runs it in the target core, reads the resulting
RGB from the emulator, and prints the table as `nespal.c` / `nespal.json`.
That table becomes the single source of truth for both the oracle and the
GameMaker recreation, so any remaining pixel difference is real.

    ./tools/palette_probe.py --core emulator/out/cores/nestopia_libretro.so
    ./tools/palette_probe.py --core ... --out tools/nestopia_palette

Needs: emulator/out/nesrun (see emulator/build.sh) and python3.
"""

from __future__ import annotations

import argparse
import json
import re
import os
import subprocess
import sys
import tempfile

# Zero-page scratch: $02 holds the palette entry currently on screen.


# --------------------------------------------------------------------------- #
# A small 6502 assembler: enough for the probe program, and far safer than
# hand-computing branch offsets.
# --------------------------------------------------------------------------- #

IMPLIED = {
    "SEI": 0x78, "CLD": 0xD8, "TXS": 0x9A, "DEX": 0xCA, "INX": 0xE8,
    "INY": 0xC8, "RTS": 0x60, "PHA": 0x48, "PLA": 0x68, "TAX": 0xAA,
    "TAY": 0xA8, "TXA": 0x8A, "TYA": 0x98, "CLC": 0x18, "SEC": 0x38,
    "NOP": 0xEA,
}

OPCODES = {
    #           imm    zp     abs
    "LDA": { "imm": 0xA9, "zp": 0xA5, "abs": 0xAD },
    "LDX": { "imm": 0xA2, "zp": 0xA6, "abs": 0xAE },
    "LDY": { "imm": 0xA0, "zp": 0xA4, "abs": 0xAC },
    "STA": {               "zp": 0x85, "abs": 0x8D },
    "STX": {               "zp": 0x86, "abs": 0x8E },
    "STY": {               "zp": 0x84, "abs": 0x8C },
    "INC": {               "zp": 0xE6, "abs": 0xEE },
    "DEC": {               "zp": 0xC6, "abs": 0xCE },
    "CMP": { "imm": 0xC9, "zp": 0xC5, "abs": 0xCD },
    "CPX": { "imm": 0xE0, "zp": 0xE4, "abs": 0xEC },
    "CPY": { "imm": 0xC0, "zp": 0xC4, "abs": 0xCC },
    "AND": { "imm": 0x29, "zp": 0x25, "abs": 0x2D },
    "ORA": { "imm": 0x09, "zp": 0x05, "abs": 0x0D },
    "ADC": { "imm": 0x69, "zp": 0x65, "abs": 0x6D },
    "BIT": {               "zp": 0x24, "abs": 0x2C },
    "JMP": {                              "abs": 0x4C },
    "JSR": {                              "abs": 0x20 },
}

BRANCHES = { "BNE": 0xD0, "BEQ": 0xF0, "BPL": 0x10, "BMI": 0x30,
             "BCC": 0x90, "BCS": 0xB0, "BVC": 0x50, "BVS": 0x70 }


def _assemble_pass(lines, labels: dict, org: int, sizes=None):
    """One pass.  Returns (code, sizes, labels); unresolved labels are an
    error on the pass where they are still missing."""
    out = bytearray()
    new_sizes = []
    new_labels = dict(labels)
    pc = org
    for kind, name, arg in lines:
        if kind == "label":
            new_labels[name] = pc
            new_sizes.append(0)
            continue

        op = name
        if op in IMPLIED and not arg:
            out.append(IMPLIED[op])
            new_sizes.append(1)
            pc += 1
            continue

        if op in BRANCHES:
            target = _operand(arg, new_labels)
            off = target - (pc + 2)
            if not -128 <= off <= 127:
                raise ValueError(f"branch out of range at ${pc:04X}: {op} {arg}")
            out += bytes([BRANCHES[op], off & 0xFF])
            new_sizes.append(2)
            pc += 2
            continue

        if op not in OPCODES:
            raise ValueError(f"unknown mnemonic {op}")

        forms = OPCODES[op]
        if arg.startswith("#"):
            val = _operand(arg[1:], new_labels)
            if "imm" not in forms:
                raise ValueError(f"{op} has no immediate form")
            out += bytes([forms["imm"], val & 0xFF])
            n = 2
        else:
            val = _operand(arg, new_labels)
            if val < 0x100 and "zp" in forms:
                out += bytes([forms["zp"], val & 0xFF])
                n = 2
            else:
                out += bytes([forms["abs"], val & 0xFF, (val >> 8) & 0xFF])
                n = 3
        new_sizes.append(n)
        pc += n
    return bytes(out), new_sizes, new_labels


def _operand(tok: str, labels: dict) -> int:
    t = tok.strip()
    if t.startswith("<"):        # low byte of a label
        return _operand(t[1:], labels) & 0xFF
    if t.startswith(">"):
        return (_operand(t[1:], labels) >> 8) & 0xFF
    if t.startswith("$"):
        return int(t[1:], 16)
    if t.startswith("%"):
        return int(t[1:], 2)
    if t in labels:
        return labels[t]
    if t.lstrip("-").isdigit():
        return int(t, 0)
    raise KeyError(f"unresolved label '{t}'")


def assemble(source: str, org: int = 0x8000) -> bytes:
    """Assemble `source`, iterating until label addresses stop moving."""
    lines = []
    for raw in source.splitlines():
        line = raw.split(";")[0].strip()
        if not line:
            continue
        while ":" in line:
            head, rest = line.split(":", 1)
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", head.strip()):
                break
            lines.append(("label", head.strip(), None))
            line = rest.strip()
            if not line:
                break
        if not line:
            continue
        parts = line.split(None, 1)
        lines.append(("op", parts[0].upper(), parts[1].strip() if len(parts) > 1 else ""))

    labels: dict[str, int] = {}
    code = b""
    for _ in range(8):
        code, _, resolved = _assemble_pass(lines, labels, org)
        if resolved == labels:
            return code
        labels = resolved
    raise ValueError("assembler failed to converge")


PROGRAM = """
        SEI
        CLD
        LDX #$FF
        TXS
        LDA #$00
        STA $2000               ; no NMI: the probe polls the PPU itself
        STA $2001               ; start with rendering off
        STA $2005
        STA $2005

; Clear both nametables to tile 0 with attribute 0, so every background
; pixel uses palette entry $3F00 - the entry under test.
        LDA #$20
        STA $2006
        LDA #$00
        STA $2006
        LDX #$10                ; 16 pages = 4 KiB ($2000-$2FFF)
        LDY #$00
clear:  LDA #$00
        STA $2007
        INY
        BNE clear
        DEX
        BNE clear

        LDA #$00
        STA $02                 ; palette entry under test

; Every frame: wait for vblank to start, then write the palette and enable
; rendering.  Palette writes outside vblank are ignored by the PPU, which
; is why this must be framed by the vblank poll.
frame:  BIT $2002
vw:     BIT $2002
        BPL vw                  ; vblank has just begun

        LDA #$3F
        STA $2006
        LDA #$00
        STA $2006
        LDA $02
        STA $2007               ; $3F00 = entry under test
        LDA #$0F
        STA $2007               ; $3F01
        STA $2007               ; $3F02
        STA $2007               ; $3F03
        LDA #$0A
        STA $2001               ; background on, left column on
        LDA #$00
        STA $2005
        STA $2005

        LDX #$05                ; hold this entry for 5 frames
hold:   BIT $2002
vh:     BIT $2002
        BPL vh
        DEX
        BNE hold

        INC $02
        LDA $02
        CMP #$40
        BNE frame
done:   JMP done
"""


def build_rom() -> bytes:
    """Build a 32 KiB PRG + 32 KiB CHR CNROM image of the palette probe."""
    code = assemble(PROGRAM, 0x8000)
    prg = bytearray(32768)
    prg[0:len(code)] = code
    for vec in (0xFFFA, 0xFFFC, 0xFFFE):        # NMI, RESET, IRQ
        prg[vec - 0x8000] = 0x00
        prg[vec - 0x8000 + 1] = 0x80
    chr_rom = bytearray(32768)                  # tile 0 = zeroes
    header = bytes([0x4E, 0x45, 0x53, 0x1A, 2, 4, 0x30, 0x00] + [0] * 8)
    return header + bytes(prg) + bytes(chr_rom)


def run_probe(nesrun: str, core: str, rom_path: str, frames: int,
              core_vars: list[str] | None = None) -> tuple[str, str]:
    """Capture every frame plus $02 (the entry index) alongside it."""
    outdir = tempfile.mkdtemp(prefix="palprobe_")
    ramfile = os.path.join(outdir, "ram.txt")
    cmd = [nesrun, "--core", core, "--rom", rom_path,
           "--frames", str(frames),
           "--dir", outdir, "--png-every", "1", "--crop", "120,120,8,8",
           "--watch", "CPU:2:1", "--watch-out", ramfile, "--quiet"]
    for kv in core_vars or []:
        cmd += ["--var", kv]
    subprocess.run(cmd, check=True)
    return outdir, ramfile


def sample_png(path: str) -> tuple[int, int, int]:
    """Read the colour of the single-colour crop in `path`."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
    from pngcmp import load_png
    img = load_png(path)
    counts: dict[tuple[int, int, int], int] = {}
    for px in img.px:
        counts[px] = counts.get(px, 0) + 1
    return max(counts, key=counts.get)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--core", required=True, help="path to *_libretro.so")
    ap.add_argument("--rom", default=None, help="reuse an existing probe ROM")
    ap.add_argument("--nesrun", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                     "..", "emulator", "out", "nesrun"))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "nes_palette"))
    ap.add_argument("--keep-rom", action="store_true")
    ap.add_argument("--var", action="append", default=[], metavar="KEY=VALUE",
                    help="core option, e.g. fceumm_palette=yuv-v3 (repeatable)")
    args = ap.parse_args(argv)

    rom_path = args.rom
    if not rom_path:
        rom_path = os.path.join(tempfile.gettempdir(), "nes_palette_probe.nes")
        with open(rom_path, "wb") as f:
            f.write(build_rom())
        print(f"probe rom: {rom_path} ({os.path.getsize(rom_path)} bytes)")

    # 5 frames per entry + warm-up slack; every frame is captured
    outdir, ramfile = run_probe(args.nesrun, args.core, rom_path, 64 * 6 + 40, args.var)

    # Per frame we have the entry index the CPU is displaying ($02) and a
    # picture.  Reading both per frame means duplicate RGB entries in the
    # palette cannot be mistaken for one another.
    entry_of_frame = {}
    for line in open(ramfile):
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "F":
            try:
                entry_of_frame[int(parts[1])] = int(parts[2], 16)
            except ValueError:
                pass

    by_entry: dict[int, tuple[int, int, int]] = {}
    for fname in sorted(os.listdir(outdir)):
        if not fname.endswith(".png"):
            continue
        frame = int(fname[1:7])
        if frame not in entry_of_frame:
            continue
        idx = entry_of_frame[frame]
        if idx < 64:
            # later frames for the same entry are the settled ones
            by_entry[idx] = sample_png(os.path.join(outdir, fname))

    print(f"{len(by_entry)}/64 palette entries observed")
    missing = [i for i in range(64) if i not in by_entry]
    if missing:
        print(f"WARNING: missing entries {missing}", file=sys.stderr)
    table: list[tuple[int, int, int]] = [by_entry.get(i, (0, 0, 0)) for i in range(64)]

    with open(args.out + ".json", "w") as f:
        json.dump({"core": os.path.basename(args.core),
                   "source": "tools/palette_probe.py",
                   "entries": [{"index": i, "hex": "%02X%02X%02X" % c, "rgb": list(c)}
                               for i, c in enumerate(table)]},
                  f, indent=1)
    with open(args.out + ".c", "w") as f:
        f.write(f"/* Generated by tools/palette_probe.py from "
                f"{os.path.basename(args.core)} - do not edit. */\n")
        f.write("static const unsigned char nes_palette[64][3] = {\n")
        for i in range(0, 64, 4):
            row = ", ".join("{%d,%d,%d}" % table[i + k] for k in range(4))
            f.write(f"    {row},   /* ${i:02X} */\n")
        f.write("};\n")
    # Raw 64x3 binary: exactly the format FCEUmm reads as <sysdir>/nes.pal,
    # so a second core can be forced onto the same palette for cross-checks.
    with open(args.out + ".pal", "wb") as f:
        for rgb in table:
            f.write(bytes(rgb))
    print(f"wrote {args.out}.c, {args.out}.json and {args.out}.pal")
    for i in range(0, 64, 4):
        print("  " + "  ".join("$%02X:%02X%02X%02X" % (i + k, *table[i + k]) for k in range(4)))

    import shutil
    shutil.rmtree(outdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
