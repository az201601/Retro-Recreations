#!/usr/bin/env python3
"""
dis6502.py -- 6502 disassembler over the CnD RR2 ROM with MMC1 bank mapping.

    .venv/bin/python tools/dis6502.py $C003 $C080        # CPU range (uses bank from savestate or default mapping)
    .venv/bin/python tools/dis6502.py --bank 3 $8000 $8100   # force PRG bank for $8000 window

Default mapping: MMC1 mode 3 -> $8000 window = PRG bank 3, $C000 = fixed bank 7.
"""
import sys

from py65.disassembler import Disassembler
from py65.devices.mpu6502 import MPU

ROM = "/home/user/Retro-Recreations/Chip 'n Dale - Rescue Rangers 2 (USA).nes"


def load_prg():
    rom = open(ROM, "rb").read()
    return rom[16:16 + 8 * 16384]


def build_mem(prg, bank8000=3):
    mem = bytearray(0x10000)
    mem[0x8000:0xC000] = prg[bank8000 * 16384:(bank8000 + 1) * 16384]
    mem[0xC000:0x10000] = prg[7 * 16384:8 * 16384]
    return mem


def disasm(mem, start, end):
    mpu = MPU()
    mpu.memory = list(mem)
    d = Disassembler(mpu)
    pc = start
    lines = []
    while pc < end:
        out = d.instruction_at(pc)
        if out is None:
            lines.append((pc, 1, f"???"))
            pc += 1
            continue
        length, text = out
        lines.append((pc, length, text))
        pc += length if length else 1
    return lines


def main():
    args = sys.argv[1:]
    bank = 3
    if args and args[0] == "--bank":
        bank = int(args[1])
        args = args[2:]
    start = int(args[0].replace("$", ""), 16)
    end = int(args[1].replace("$", ""), 16)
    mem = build_mem(load_prg(), bank)
    for a, l, t in disasm(mem, start, end):
        raw = mem[a:a + l].hex()
        print(f"{a:04X}  {raw:<10s} {t}")


if __name__ == "__main__":
    main()
