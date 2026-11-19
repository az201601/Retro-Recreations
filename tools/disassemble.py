#!/usr/bin/env python3
"""
6502 disassembler for Chip 'n Dale Rescue Rangers 2 (USA) - Mapper 1 (MMC1).

Usage:
    python3 disassemble.py [--bank N] [--start ADDR] [--length N] [--follow]

Without --follow it linearly disassembles the fixed bank ($C000-$FFFF).
With --follow it follows control flow from the reset vector, tracking
MMC1 register writes so bank switches are annotated.
"""

import argparse
import sys

# ---------------------------------------------------------------------------
# Opcode table: (mnemonic, addressing mode, base cycles)
# ---------------------------------------------------------------------------
# Modes: imp, acc, imm, zp, zpx, zpy, abs, abx, aby, ind, izx, izy, rel
OPS = {}
def op(code, mn, mode, cyc):
    OPS[code] = (mn, mode, cyc)

# ALU group (ORA/AND/EOR/ADC/STA/LDA/CMP/SBC) - regular pattern
alu = ['ORA', 'AND', 'EOR', 'ADC', 'STA', 'LDA', 'CMP', 'SBC']
alu_modes = ['izx', 'zp', 'imm', 'abs', 'izy', 'zpx', 'aby', 'abx']
alu_cyc = [6, 3, 2, 4, 5, 3, 4, 4]
for i, mn in enumerate(alu):
    for j, mode in enumerate(alu_modes):
        if mn == 'STA' and mode == 'imm':
            continue
        op((i << 5) | (j << 2) | 1, mn, mode, alu_cyc[j])

# Shifts / rotates / inc / dec
sh = ['ASL', 'ROL', 'LSR', 'ROR', 'STX', 'LDX', 'DEC', 'INC']
sh_modes = ['imm', 'zp', 'acc', 'abs', None, 'zpx', None, 'abx']
sh_cyc = [2, 5, 2, 6, 0, 6, 0, 7]
for i, mn in enumerate(sh):
    for j, mode in enumerate(sh_modes):
        if mode is None:
            continue
        if mn in ('STX', 'LDX') and mode in ('acc', 'imm') and mn == 'STX':
            continue
        if mn == 'LDX' and mode == 'imm':
            op((i << 5) | (j << 2) | 2, mn, mode, 2)
            continue
        if mn in ('STX', 'LDX') and j == 5:
            # STX/LDX use zpy instead of zpx
            op((i << 5) | (j << 2) | 2, mn, 'zpy', 4 if mn == 'STX' else 4)
            continue
        if mn in ('STX', 'LDX') and j == 7:
            op((i << 5) | (j << 2) | 2, mn, 'aby' if mn == 'LDX' else 'abx', 4)
            continue
        if mn in ('DEC', 'INC') and mode == 'acc':
            continue
        op((i << 5) | (j << 2) | 2, mn, mode, sh_cyc[j])

# Single byte / misc
misc = {
    0x00: ('BRK', 'imp', 7), 0x08: ('PHP', 'imp', 3), 0x18: ('CLC', 'imp', 2),
    0x28: ('PLP', 'imp', 4), 0x38: ('SEC', 'imp', 2), 0x40: ('RTI', 'imp', 6),
    0x48: ('PHA', 'imp', 3), 0x58: ('CLI', 'imp', 2), 0x60: ('RTS', 'imp', 6),
    0x68: ('PLA', 'imp', 4), 0x78: ('SEI', 'imp', 2), 0x88: ('DEY', 'imp', 2),
    0x8A: ('TXA', 'imp', 2), 0x98: ('TYA', 'imp', 2), 0x9A: ('TXS', 'imp', 2),
    0xA8: ('TAY', 'imp', 2), 0xAA: ('TAX', 'imp', 2), 0xB8: ('CLV', 'imp', 2),
    0xBA: ('TSX', 'imp', 2), 0xC8: ('INY', 'imp', 2), 0xCA: ('DEX', 'imp', 2),
    0xD8: ('CLD', 'imp', 2), 0xE8: ('INX', 'imp', 2), 0xEA: ('NOP', 'imp', 2),
    0xF8: ('SED', 'imp', 2),
    0x10: ('BPL', 'rel', 2), 0x30: ('BMI', 'rel', 2), 0x50: ('BVC', 'rel', 2),
    0x70: ('BVS', 'rel', 2), 0x90: ('BCC', 'rel', 2), 0xB0: ('BCS', 'rel', 2),
    0xD0: ('BNE', 'rel', 2), 0xF0: ('BEQ', 'rel', 2),
    0x20: ('JSR', 'abs', 6), 0x4C: ('JMP', 'abs', 3), 0x6C: ('JMP', 'ind', 5),
    0x24: ('BIT', 'zp', 3), 0x2C: ('BIT', 'abs', 4),
    0x84: ('STY', 'zp', 3), 0x94: ('STY', 'zpx', 4), 0x8C: ('STY', 'abs', 4),
    0xA0: ('LDY', 'imm', 2), 0xA4: ('LDY', 'zp', 3), 0xB4: ('LDY', 'zpx', 4),
    0xAC: ('LDY', 'abs', 4), 0xBC: ('LDY', 'abx', 4),
    0xC0: ('CPY', 'imm', 2), 0xC4: ('CPY', 'zp', 3), 0xCC: ('CPY', 'abs', 4),
    0xE0: ('CPX', 'imm', 2), 0xE4: ('CPX', 'zp', 3), 0xEC: ('CPX', 'abs', 4),
}
for code, v in misc.items():
    OPS[code] = v

MODE_LEN = {'imp': 1, 'acc': 1, 'imm': 2, 'zp': 2, 'zpx': 2, 'zpy': 2,
            'abs': 3, 'abx': 3, 'aby': 3, 'ind': 3, 'izx': 2, 'izy': 2, 'rel': 2}

def fmt_operand(mode, operand_bytes, addr):
    if mode == 'imp':
        return ''
    if mode == 'acc':
        return 'A'
    if mode == 'imm':
        return '#$%02X' % operand_bytes[0]
    if mode == 'zp':
        return '$%02X' % operand_bytes[0]
    if mode == 'zpx':
        return '$%02X,X' % operand_bytes[0]
    if mode == 'zpy':
        return '$%02X,Y' % operand_bytes[0]
    if mode == 'abs':
        return '$%04X' % (operand_bytes[0] | (operand_bytes[1] << 8))
    if mode == 'abx':
        return '$%04X,X' % (operand_bytes[0] | (operand_bytes[1] << 8))
    if mode == 'aby':
        return '$%04X,Y' % (operand_bytes[0] | (operand_bytes[1] << 8))
    if mode == 'ind':
        return '($%04X)' % (operand_bytes[0] | (operand_bytes[1] << 8))
    if mode == 'izx':
        return '($%02X,X)' % operand_bytes[0]
    if mode == 'izy':
        return '($%02X),Y' % operand_bytes[0]
    if mode == 'rel':
        off = operand_bytes[0]
        if off >= 0x80:
            off -= 0x100
        return '$%04X' % (addr + 2 + off)
    return '???'

class Rom:
    def __init__(self, path):
        with open(path, 'rb') as f:
            data = f.read()
        assert data[:4] == b'NES\x1a', 'Not an iNES file'
        self.prg_banks = data[4]
        self.chr_banks = data[5]
        self.mapper = ((data[7] >> 4) << 4) | (data[6] >> 4)
        self.prg = data[16:16 + self.prg_banks * 0x4000]
        self.chr = data[16 + self.prg_banks * 0x4000:
                        16 + (self.prg_banks * 0x4000) + self.chr_banks * 0x2000]
        # MMC1 state
        self.mmc1_shift = 0
        self.mmc1_shift_count = 0
        self.mmc1_control = 0
        self.mmc1_chr0 = 0
        self.mmc1_chr1 = 0
        self.mmc1_prg = 0

    def prg_read(self, addr):
        """Read CPU address $8000-$FFFF through current MMC1 mapping."""
        if addr >= 0xC000:
            bank = self.prg_banks - 1  # fixed bank
            return self.prg[bank * 0x4000 + (addr - 0xC000)]
        bank = self.mmc1_prg & 0x0F
        if self.mmc1_control & 0x08:
            bank &= 0x0F
        else:
            bank &= 0x0E  # 32KB mode: even banks only
        return self.prg[bank * 0x4000 + (addr - 0x8000)]

    def mmc1_write(self, addr, value):
        """Feed a write into the MMC1 shift register; commit on 5th write."""
        if value & 0x80:
            self.mmc1_shift = 0
            self.mmc1_shift_count = 0
            self.mmc1_control |= 0x0C  # reset also sets PRG/CHR mode bits
            return
        self.mmc1_shift |= (value & 1) << self.mmc1_shift_count
        self.mmc1_shift_count += 1
        if self.mmc1_shift_count == 5:
            v = self.mmc1_shift
            if addr < 0xA000:
                self.mmc1_control = v
            elif addr < 0xC000:
                self.mmc1_chr0 = v
            elif addr < 0xE000:
                self.mmc1_chr1 = v
            else:
                self.mmc1_prg = v
            self.mmc1_shift = 0
            self.mmc1_shift_count = 0

    def disasm_at(self, addr, max_len=1):
        """Disassemble one instruction at CPU address addr. Returns (text, length, next_addr, info)."""
        opcode = self.prg_read(addr)
        if opcode not in OPS:
            return ('.byte $%02X' % opcode, 1, addr + 1, None)
        mn, mode, cyc = OPS[opcode]
        ln = MODE_LEN[mode]
        ob = [self.prg_read(addr + i) for i in range(1, ln)]
        operand = fmt_operand(mode, ob, addr)
        text = mn + (' ' + operand if operand else '')
        info = {'mnemonic': mn, 'mode': mode, 'cycles': cyc, 'operand_bytes': ob}
        return (text, ln, addr + ln, info)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rom', default="Chip 'n Dale - Rescue Rangers 2 (USA).nes")
    ap.add_argument('--start', type=lambda x: int(x, 0), default=0xFFE0)
    ap.add_argument('--length', type=int, default=64)
    ap.add_argument('--follow', action='store_true',
                    help='Follow control flow, tracking MMC1 writes')
    args = ap.parse_args()

    rom = Rom(args.rom)
    print('; Mapper %d (MMC1), PRG %d x 16KB, CHR %d x 8KB' %
          (rom.mapper, rom.prg_banks, rom.chr_banks))
    print('; Reset vector: $%04X' % (rom.prg_read(0xFFFC) | (rom.prg_read(0xFFFD) << 8)))

    if not args.follow:
        addr = args.start
        end = addr + args.length
        while addr < end:
            text, ln, nxt, info = rom.disasm_at(addr)
            raw = ' '.join('%02X' % rom.prg_read(addr + i) for i in range(ln))
            print('$%04X: %-8s %s' % (addr, raw, text))
            addr = nxt
        return

    # Follow mode: simple recursive traversal from start address.
    visited = set()
    work = [args.start]
    # Track MMC1 state along the linear path from reset (approximation:
    # state is whatever the last linear writes set; branches share it).
    while work:
        addr = work.pop()
        while addr not in visited and 0x8000 <= addr <= 0xFFFF:
            visited.add(addr)
            text, ln, nxt, info = rom.disasm_at(addr)
            raw = ' '.join('%02X' % rom.prg_read(addr + i) for i in range(ln))
            print('$%04X: %-8s %s' % (addr, raw, text))
            # Detect MMC1 writes: STA/STX/STY/INC/DEC to $8000-$FFFF
            if info and info['mnemonic'] in ('STA', 'STX', 'STY', 'INC', 'DEC', 'ASL', 'LSR', 'ROL', 'ROR'):
                ob = info['operand_bytes']
                if info['mode'] in ('abs', 'abx', 'aby') and len(ob) == 2:
                    target = ob[0] | (ob[1] << 8)
                    if target >= 0x8000:
                        # Value written is unknown statically for RMW; mark it.
                        print(';   ^^ MMC1 write to $%04X (value depends on runtime state)' % target)
                        if info['mnemonic'] in ('STA', 'STX', 'STY'):
                            rom.mmc1_write(target, 0)  # placeholder; real value unknown
            if info and info['mnemonic'] in ('JMP', 'JSR') and info['mode'] == 'abs':
                ob = info['operand_bytes']
                dest = ob[0] | (ob[1] << 8)
                if info['mnemonic'] == 'JMP':
                    addr = dest
                    continue
                work.append(dest)
            if info and info['mode'] == 'rel':
                ob = info['operand_bytes']
                off = ob[0] - 0x100 if ob[0] >= 0x80 else ob[0]
                work.append(addr + 2 + off)
            if info and info['mnemonic'] in ('RTS', 'RTI', 'BRK'):
                break
            addr = nxt

if __name__ == '__main__':
    main()
