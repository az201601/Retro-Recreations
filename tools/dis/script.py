#!/usr/bin/env python3
"""Lists the object scripts of the game (the byte code run by the interpreter in bank 7 at $DB90, one script per object slot).
usage: script.py BANK START [END]      e.g.  script.py 4 8093 80F0     (stops at END, or after 60 lines)
Each object slot X has: script pointer $0284,X / $0290,X, wait counter $029C,X, a call stack, two loop counters
($02CC,X and $02D8,X) and the saved CPU flags of the last machine-code call ($02A8,X)."""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROM = open(os.path.join(ROOT, "Chip 'n Dale - Rescue Rangers 2 (USA).nes"), 'rb').read()
# opcode: (text, argument bytes).  a = byte, w = address
OPS = {0x00: ('END (flags = $80)', ''), 0x01: ('FRAME', ''), 0x02: ('WAIT %d', 'a'), 0x03: ('GOTO CODE $%04X', 'w'), 0x04: ('SPAWN flag $%02X script $%04X', 'aw'),
       0x05: ('CALL CODE $%04X', 'w'), 0x06: ('JUMP $%04X', 'w'), 0x07: ('CALL $%04X', 'w'), 0x08: ('RETURN', ''),
       0x09: ('LOOP1 %d times -> $%04X', 'aw'), 0x0A: ('LOOP2 %d times -> $%04X', 'aw'),
       0x0B: ('IF Z=0 -> $%04X', 'w'), 0x0C: ('IF C=0 -> $%04X', 'w'), 0x0D: ('IF N=0 -> $%04X', 'w'), 0x0E: ('IF Z=1 -> $%04X', 'w'),
       0x0F: ('IF C=1 -> $%04X', 'w'), 0x10: ('IF N=1 -> $%04X', 'w'), 0x11: ('IF pad[%d] & $%02X == 0 -> $%04X', 'aaw'), 0x12: ('SWITCH on [$%04X]', 'w'),
       0x13: ('POKE $%02X -> [$%04X]', 'aw'), 0x14: ('POKE zp[$1D+$%02X] = $%02X', 'aa'), 0x15: ('LOOP1 = 0', ''), 0x16: ('LOOP2 = 0', ''),
       0x17: ('SOUND $%02X', 'a'), 0x18: ('MOVE, FRAME', ''), 0x19: ('MOVE', ''), 0x1A: ('ARC MOVE', ''), 0x1B: ('CODE $E41B', ''), 0x1C: ('CODE $E412', ''),
       0x1D: ('TYPE = $%02X', 'a'), 0x1E: ('CEL = %d', 'a'), 0x1F: ('FACE LEFT', ''), 0x20: ('FACE RIGHT', ''), 0x21: ('VFLIP OFF', ''), 0x22: ('VFLIP ON', ''),
       0x23: ('TURN ROUND', ''), 0x24: ('VFLIP TOGGLE', ''), 0x25: ('X = $%04X', 'w'), 0x26: ('Y = $%04X', 'w'), 0x27: ('X += %d', 's'), 0x28: ('Y += %d', 's'),
       0x29: ('XV = $%02X', 'a'), 0x2A: ('YV = $%02X', 'a'), 0x2B: ('XV += 1', ''), 0x2C: ('YV += 1', ''), 0x2D: ('XV -= 1', ''), 0x2E: ('YV -= 1', ''),
       0x2F: ('SPEED = $%02X, velocities = 0', 'a'), 0x30: ('[$398] = $%02X', 'a'), 0x31: ('[$3A4] = $%02X', 'a'), 0x32: ('BOX = %d, %d', 'aa'),
       0x33: ('[$3C8] = $%02X', 'a'), 0x34: ('[$3D4] = $%02X', 'a'), 0x35: ('ATTR = $%02X', 'a'), 0x36: ('[$3E0] = $%02X', 'a'), 0x37: ('[$40] = $%02X, CODE $D039', 'a'),
       0x38: ('CODE $C1B0 X=$%02X A=$%02X', 'aa'), 0x39: ('CODE $C1BF X=$%02X A=$%02X', 'aa'), 0x3A: ('CODE $C44D ($%04X)', 'w'), 0x3B: ('CODE $C625 ($%04X)', 'w'),
       0x3C: ('CODE $C5CE X=$%02X A=$%02X', 'aa'), 0x3D: ('CODE $C5F8 X=$%02X A=$%02X', 'aa'), 0x3E: ('[$55,$54,$52,$53] = $%02X,$%02X,$%02X,$%02X', 'aaaa'),
       0x3F: ('[$4E,$4F,$57] = $%02X,$%02X,$%02X; ...', 'aaa')}
def rd(bank, a): return ROM[16 + (7 if a >= 0xC000 else bank) * 0x4000 + (a & 0x3FFF)]
def lst(bank, pc, end=None, maxn=60):
    out = []
    while (end is None and len(out) < maxn) or (end is not None and pc < end):
        o = rd(bank, pc)
        if o not in OPS: out.append('%04X  ?? $%02X' % (pc, o)); pc += 1; continue
        t, args = OPS[o]; p = pc + 1; v = []
        for k in args:
            if k == 'w': v.append(rd(bank, p) | rd(bank, p + 1) << 8); p += 2
            elif k == 's': b = rd(bank, p); v.append(b - 256 if b > 127 else b); p += 1
            else: v.append(rd(bank, p)); p += 1
        out.append('%04X  %s' % (pc, t % tuple(v))); pc = p
        if end is None and o in (0x00, 0x06, 0x08, 0x03): out.append('')
    return out
if __name__ == '__main__':
    a = sys.argv; print('\n'.join(lst(int(a[1]), int(a[2], 16), int(a[3], 16) if len(a) > 3 else None)))
