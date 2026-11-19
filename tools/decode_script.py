#!/usr/bin/env python3
"""
Decode Chip 'n Dale Rescue Rangers 2 type-1 script bytecode (the VM at $DB90).

Scripts are executed by type-1 objects (see docs/05_vm_opcodes.md). The VM
runs with PRG bank 4 mapped at $8000-$BFFF, so script addresses in that range
are read from bank 4 unless --bank says otherwise. Addresses $C000-$FFFF read
from the fixed bank.

Usage:
    python3 tools/decode_script.py --start 0xF2DB [--bank 4] [--steps 200]
"""

import argparse

# opcode -> (total instruction size in bytes, mnemonic, operand format)
# formats: none, u8, ptr, cnt_ptr, cond_ptr, pad_ptr, val_ptr, idx_val, u8_u8, u8x4, u8x3
OPS = {
    0x00: (1, "END", "none"),          # kill self
    0x01: (1, "YIELD", "none"),        # end this frame
    0x02: (2, "WAIT", "u8"),           # $029C = frames
    0x03: (3, "JSRN", "ptr"),          # native jump, resume script next frame
    0x04: (4, "SPAWN", "type_ptr"),    # type, script ptr
    0x05: (3, "CALLN", "ptr"),         # native call, continue same frame
    0x06: (3, "JUMP", "ptr"),          # script jump
    0x07: (3, "GOSUB", "ptr"),         # script call (return stack $0278)
    0x08: (1, "RET", "none"),
    0x09: (4, "LOOPA", "cnt_ptr"),     # counter $02CC
    0x0A: (4, "LOOPB", "cnt_ptr"),     # counter $02D8
    0x0B: (3, "CJ_Z", "ptr"),          # jump if flag byte zero
    0x0C: (3, "CJ_C", "ptr"),
    0x0D: (3, "CJ_M", "ptr"),
    0x0E: (3, "CJ_NZ", "ptr"),
    0x0F: (3, "CJ_NC", "ptr"),
    0x10: (3, "CJ_NM", "ptr"),
    0x11: (5, "PADJ", "pad_ptr"),      # if ($38+idx)&mask == 0 jump
    0x12: (0, "SWITCH", "special"),    # variable length - stops decoder
    0x13: (4, "WRITE", "val_ptr"),     # byte -> (addr)
    0x14: (3, "SET1D", "idx_val"),     # $1D,X = value (CHR bank shadows)
    0x15: (1, "CLRLA", "none"),
    0x16: (1, "CLRLB", "none"),
    0x17: (2, "SOUND", "u8"),          # $CE20/$CE31 sound request
    0x18: (1, "MOVE_YLD", "none"),     # apply velocity, yield
    0x19: (1, "MOVE", "none"),         # apply velocity, continue
    0x1A: (1, "PHYS", "none"),         # gravity/physics step
    0x1B: (1, "E41B", "none"),
    0x1C: (1, "E412", "none"),
    0x1D: (2, "SET32C", "u8"),
    0x1E: (2, "SET338", "u8"),
    0x1F: (1, "FLG_1F", "none"),       # $0344 &= $BF
    0x20: (1, "FLG_20", "none"),       # $0344 |= $40
    0x21: (1, "FLG_21", "none"),       # $0344 &= $7F
    0x22: (1, "FLG_22", "none"),       # $0344 |= $80
    0x23: (1, "FLG_23", "none"),       # $0344 ^= $40
    0x24: (1, "FLG_24", "none"),       # $0344 ^= $80
    0x25: (3, "SETX", "u8_u8"),        # $0314,$0320
    0x26: (3, "SETY", "u8_u8"),        # $02FC,$0308
    0x27: (2, "ADDX", "u8"),           # signed add to X
    0x28: (2, "ADDY", "u8"),           # signed add to Y
    0x29: (2, "SETVX", "u8"),          # $0350 (nibble-packed velocity)
    0x2A: (2, "SETVY", "u8"),          # $035C
    0x2B: (1, "INCVX", "none"),
    0x2C: (1, "INCVY", "none"),
    0x2D: (1, "DECVX", "none"),
    0x2E: (1, "DECVY", "none"),
    0x2F: (2, "SETANIM", "u8"),        # $0380, clears velocity/subpos
    0x30: (2, "SET398", "u8"),
    0x31: (2, "SET3A4", "u8"),
    0x32: (3, "SETSUB", "u8_u8"),      # $03B0,$03BC subpixels
    0x33: (2, "SET3C8", "u8"),
    0x34: (2, "SET3D4", "u8"),
    0x35: (2, "SET344", "u8"),
    0x36: (2, "SET3E0", "u8"),
    0x37: (2, "SETSTATE", "u8"),       # $40 = value, fade-exit via $D039
    0x38: (3, "TIMER0", "u8_u8"),      # $C1B0
    0x39: (3, "TIMER1", "u8_u8"),      # $C1BF
    0x3A: (3, "LOADC44D", "ptr"),      # nametable/screen loader ($C44D)
    0x3B: (3, "LOADC625", "ptr"),      # ($C625)
    0x3C: (3, "IN3C", "u8_u8"),        # input helper $C5CE
    0x3D: (3, "IN3D", "u8_u8"),        # input helper $C5F8
    0x3E: (5, "TEXTCTL", "u8x4"),      # $55,$54,$52,$53
    0x3F: (4, "MSGCTL", "u8x3"),       # $4E,$4F,$57; $4D=4
}

NOTES = {
    0xE4E0: "link last spawned slot to current object ($03E0)",
    0xDAFD: "post-spawn helper",
}


def fmt_ops(fmt, ops):
    if fmt == "none" or not ops:
        return ""
    if fmt == "u8":
        return "$%02X (%d)" % (ops[0], ops[0])
    if fmt == "ptr":
        p = ops[0] | (ops[1] << 8)
        note = NOTES.get(p, "")
        return "$%04X%s" % (p, ("  ; " + note) if note else "")
    if fmt == "type_ptr":
        p = ops[1] | (ops[2] << 8)
        return "type $%02X, $%04X" % (ops[0], p)
    if fmt == "cnt_ptr":
        p = ops[1] | (ops[2] << 8)
        return "count $%02X (%d), $%04X" % (ops[0], ops[0], p)
    if fmt == "pad_ptr":
        p = ops[2] | (ops[3] << 8)
        return "idx $%02X, mask $%02X, $%04X" % (ops[0], ops[1], p)
    if fmt == "val_ptr":
        p = ops[1] | (ops[2] << 8)
        return "$%02X -> $%04X" % (ops[0], p)
    if fmt == "idx_val":
        return "idx $%02X, $%02X" % (ops[0], ops[1])
    return " ".join("$%02X" % b for b in ops)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", default="Chip 'n Dale - Rescue Rangers 2 (USA).nes")
    ap.add_argument("--start", type=lambda x: int(x, 0), required=True)
    ap.add_argument("--bank", type=int, default=4,
                    help="PRG bank mapped at $8000-$BFFF (VM default: 4)")
    ap.add_argument("--steps", type=int, default=200)
    args = ap.parse_args()

    with open(args.rom, "rb") as f:
        data = f.read()
    prg = data[16:16 + data[4] * 0x4000]

    def rd(addr):
        if addr >= 0xC000:
            return prg[0x1C000 + (addr - 0xC000)]
        return prg[args.bank * 0x4000 + (addr - 0x8000)]

    addr = args.start
    for _ in range(args.steps):
        op = rd(addr)
        if op not in OPS:
            print("$%04X: ?? %02X  (unknown opcode, stop)" % (addr, op))
            break
        size, mn, fmt = OPS[op]
        if fmt == "special":
            print("$%04X: %02X  %s (variable length, stop)" % (addr, op, mn))
            break
        raw = " ".join("%02X" % rd(addr + i) for i in range(size))
        ops = [rd(addr + i) for i in range(1, size)]
        print("$%04X: %-14s %s %s" % (addr, raw, mn, fmt_ops(fmt, ops)))
        addr += size
        if op in (0x00, 0x37):
            break


if __name__ == "__main__":
    main()
