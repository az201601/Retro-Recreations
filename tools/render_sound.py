#!/usr/bin/env python3
"""
Render Chip 'n Dale Rescue Rangers 2 sound-engine output to WAV files.

Instead of reverse-engineering the sequence data format, this executes the
game's real bank-6 sound engine ($8000 tick, $8200 start dispatcher) and the
real fixed-bank request routines ($CE20/$CE31) on a small 6502 core, records
every write to the NES APU registers ($4000-$4017), and synthesizes audio
from that register timeline (pulse/triangle/noise/DMC, standard NES mixing).

Sound-request interface (traced; see docs/08_sound_engine.md):
  $CE20(A=id): ids $01-$78 queue into $F0 (+$B6 unless id >= $79);
               ids $79-$7F are engine control codes handled by $8200's
               jump table at $8220 ($7F = full reset/stop at $8274).
  $CE31(A=id): the VM SOUND opcode's path for ids $22-$78 (priority gate).
  Engine $832E: sequence pointer table $87B5 (id*2); header bits $30 pick
               music channels 0-3 (bits clear) or SFX channels 4-5 (set).

Usage:
  python3 tools/render_sound.py [--id $74 ...] [--outdir extracted/sounds]
  python3 tools/render_sound.py --timeline   (state-1 consistency check)
"""

import argparse
import json
import os
import struct
import sys
import wave

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from disassemble import OPS  # opcode -> (mnemonic, mode, cycles); decode only

ROM_PATH = "Chip 'n Dale - Rescue Rangers 2 (USA).nes"
CPU_FREQ = 1789773.0
FRAME_RATE = 60.0988          # NTSC, docs/01_rom_analysis.md
SAMPLE_RATE = 44100

LEN_TABLE = [10, 254, 20, 2, 40, 4, 80, 6, 160, 8, 60, 10, 14, 12, 26, 14,
             12, 16, 24, 18, 48, 20, 96, 22, 192, 24, 72, 26, 16, 28, 32, 30]
NOISE_PERIOD = [4, 8, 16, 32, 64, 96, 128, 160, 202, 254, 380, 508, 762,
                1016, 2034, 4068]
DMC_RATE = [428, 380, 340, 320, 286, 254, 226, 214, 190, 160, 142, 128,
            106, 84, 72, 54]
DUTY_SEQ = [[0, 1, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 0, 0, 0],
            [1, 0, 0, 1, 1, 1, 1, 1]]
TRI_SEQ = [15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0,
           0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]


class CpuError(Exception):
    pass


class CPU:
    """Official-opcode 6502 (binary ADC/SBC only, like the NES 2A03)."""

    def __init__(self, read, write):
        self.read = read
        self.write = write
        self.reset()

    def reset(self):
        self.a = self.x = self.y = 0
        self.sp = 0xFF
        self.pc = 0
        self.n = self.v = self.d = self.i = self.z = self.c = False
        self.i = True
        self.steps = 0

    # -- flags / stack -------------------------------------------------
    def nz(self, v):
        self.n = bool(v & 0x80)
        self.z = (v & 0xFF) == 0
        return v & 0xFF

    def push(self, v):
        self.write(0x100 + self.sp, v & 0xFF)
        self.sp = (self.sp - 1) & 0xFF

    def pop(self):
        self.sp = (self.sp + 1) & 0xFF
        return self.read(0x100 + self.sp)

    def push16(self, v):
        self.push(v >> 8)
        self.push(v & 0xFF)

    def pop16(self):
        lo = self.pop()
        return lo | (self.pop() << 8)

    def get_p(self):
        return ((0x80 if self.n else 0) | (0x40 if self.v else 0) | 0x20 |
                (0x08 if self.d else 0) | (0x04 if self.i else 0) |
                (0x02 if self.z else 0) | (0x01 if self.c else 0))

    def set_p(self, p):
        self.n = bool(p & 0x80)
        self.v = bool(p & 0x40)
        self.d = bool(p & 0x08)
        self.i = bool(p & 0x04)
        self.z = bool(p & 0x02)
        self.c = bool(p & 0x01)

    # -- addressing ----------------------------------------------------
    def addr(self, mode):
        pc = self.pc
        if mode == 'imm':
            self.pc += 1
            return pc
        if mode == 'zp':
            a = self.read(pc)
            self.pc += 1
            return a
        if mode == 'zpx':
            a = (self.read(pc) + self.x) & 0xFF
            self.pc += 1
            return a
        if mode == 'zpy':
            a = (self.read(pc) + self.y) & 0xFF
            self.pc += 1
            return a
        if mode in ('abs', 'abx', 'aby', 'ind'):
            lo = self.read(pc)
            hi = self.read(pc + 1)
            self.pc += 2
            a = lo | (hi << 8)
            if mode == 'abx':
                a = (a + self.x) & 0xFFFF
            elif mode == 'aby':
                a = (a + self.y) & 0xFFFF
            elif mode == 'ind':  # JMP only; reproduce the page-wrap bug
                a = self.read(a) | (self.read((a & 0xFF00) |
                                              ((a + 1) & 0xFF)) << 8)
            return a
        if mode == 'izx':
            zp = (self.read(pc) + self.x) & 0xFF
            self.pc += 1
            return self.read(zp) | (self.read((zp + 1) & 0xFF) << 8)
        if mode == 'izy':
            zp = self.read(pc)
            self.pc += 1
            base = self.read(zp) | (self.read((zp + 1) & 0xFF) << 8)
            return (base + self.y) & 0xFFFF
        raise CpuError('bad mode %r at $%04X' % (mode, pc))

    # -- execution -----------------------------------------------------
    def run_until(self, sentinel, max_steps):
        steps = 0
        while self.pc != sentinel:
            self.step()
            steps += 1
            if steps > max_steps:
                raise CpuError('runaway: >%d steps (pc=$%04X)' %
                               (max_steps, self.pc))
        return steps

    def step(self):
        pc0 = self.pc
        op = self.read(self.pc)
        self.pc += 1
        info = OPS.get(op)
        if info is None:
            raise CpuError('unofficial opcode $%02X at $%04X' % (op, pc0))
        mn, mode, _cyc = info
        self.steps += 1

        if mn in ('LDA', 'LDX', 'LDY', 'ADC', 'SBC', 'AND', 'ORA', 'EOR',
                  'CMP', 'CPX', 'CPY', 'BIT'):
            a = self.addr(mode)
            v = self.read(a)
            if mn == 'LDA':
                self.a = self.nz(v)
            elif mn == 'LDX':
                self.x = self.nz(v)
            elif mn == 'LDY':
                self.y = self.nz(v)
            elif mn == 'AND':
                self.a = self.nz(self.a & v)
            elif mn == 'ORA':
                self.a = self.nz(self.a | v)
            elif mn == 'EOR':
                self.a = self.nz(self.a ^ v)
            elif mn == 'ADC':
                t = self.a + v + (1 if self.c else 0)
                self.v = bool(~(self.a ^ v) & (self.a ^ t) & 0x80)
                self.c = t > 0xFF
                self.a = self.nz(t)
            elif mn == 'SBC':
                t = self.a + (v ^ 0xFF) + (1 if self.c else 0)
                self.v = bool((self.a ^ t) & (self.a ^ v) & 0x80)
                self.c = t > 0xFF
                self.a = self.nz(t)
            elif mn == 'CMP':
                self._cmp(self.a, v)
            elif mn == 'CPX':
                self._cmp(self.x, v)
            elif mn == 'CPY':
                self._cmp(self.y, v)
            elif mn == 'BIT':
                self.z = (self.a & v) == 0
                self.n = bool(v & 0x80)
                self.v = bool(v & 0x40)
            return

        if mn in ('STA', 'STX', 'STY'):
            a = self.addr(mode)
            self.write(a, {'STA': self.a, 'STX': self.x, 'STY': self.y}[mn])
            return

        if mn in ('ASL', 'LSR', 'ROL', 'ROR', 'INC', 'DEC'):
            if mode == 'acc':
                self.a = self._shift(mn, self.a)
            else:
                a = self.addr(mode)
                self.write(a, self._shift(mn, self.read(a)))
            return

        if mn in ('BPL', 'BMI', 'BVC', 'BVS', 'BCC', 'BCS', 'BNE', 'BEQ'):
            off = self.read(self.pc)
            self.pc += 1
            cond = {'BPL': not self.n, 'BMI': self.n, 'BVC': not self.v,
                    'BVS': self.v, 'BCC': not self.c, 'BCS': self.c,
                    'BNE': not self.z, 'BEQ': self.z}[mn]
            if cond:
                if off >= 0x80:
                    off -= 0x100
                self.pc = (self.pc + off) & 0xFFFF
            return

        if mn == 'JMP':
            self.pc = self.addr(mode)
            return
        if mn == 'JSR':
            a = self.addr('abs')
            self.push16((self.pc - 1) & 0xFFFF)
            self.pc = a
            return
        if mn == 'RTS':
            self.pc = (self.pop16() + 1) & 0xFFFF
            return
        if mn == 'RTI':
            self.set_p(self.pop())
            self.pc = self.pop16()
            return
        if mn == 'BRK':
            raise CpuError('BRK executed at $%04X' % pc0)

        if mn == 'PHA':
            self.push(self.a)
        elif mn == 'PLA':
            self.a = self.nz(self.pop())
        elif mn == 'PHP':
            self.push(self.get_p() | 0x10)
        elif mn == 'PLP':
            self.set_p(self.pop())
        elif mn == 'TAX':
            self.x = self.nz(self.a)
        elif mn == 'TAY':
            self.y = self.nz(self.a)
        elif mn == 'TXA':
            self.a = self.nz(self.x)
        elif mn == 'TYA':
            self.a = self.nz(self.y)
        elif mn == 'TSX':
            self.x = self.nz(self.sp)
        elif mn == 'TXS':
            self.sp = self.x
        elif mn == 'INX':
            self.x = self.nz(self.x + 1)
        elif mn == 'INY':
            self.y = self.nz(self.y + 1)
        elif mn == 'DEX':
            self.x = self.nz(self.x - 1)
        elif mn == 'DEY':
            self.y = self.nz(self.y - 1)
        elif mn == 'CLC':
            self.c = False
        elif mn == 'SEC':
            self.c = True
        elif mn == 'CLI':
            self.i = False
        elif mn == 'SEI':
            self.i = True
        elif mn == 'CLV':
            self.v = False
        elif mn == 'CLD':
            self.d = False
        elif mn == 'SED':
            self.d = True
        elif mn == 'NOP':
            pass
        else:
            raise CpuError('unimplemented mnemonic %s at $%04X' % (mn, pc0))

    def _cmp(self, reg, v):
        self.c = reg >= v
        self.nz((reg - v) & 0xFF)

    def _shift(self, mn, v):
        if mn == 'ASL':
            self.c = bool(v & 0x80)
            return self.nz(v << 1)
        if mn == 'LSR':
            self.c = bool(v & 0x01)
            return self.nz(v >> 1)
        if mn == 'ROL':
            c = 1 if self.c else 0
            self.c = bool(v & 0x80)
            return self.nz((v << 1) | c)
        if mn == 'ROR':
            c = 0x80 if self.c else 0
            self.c = bool(v & 0x01)
            return self.nz((v >> 1) | c)
        if mn == 'INC':
            return self.nz(v + 1)
        if mn == 'DEC':
            return self.nz(v - 1)
        raise CpuError(mn)


SENTINEL = 0x0100  # stack page; only ever a pushed return address


class Machine:
    """NES memory map: 2KB RAM, bank 6 at $8000, fixed bank 7 at $C000."""

    def __init__(self, rom_path=ROM_PATH):
        with open(rom_path, 'rb') as f:
            data = f.read()
        prg = data[16:16 + data[4] * 0x4000]
        self.bank6 = prg[6 * 0x4000:7 * 0x4000]
        self.fixed = prg[7 * 0x4000:8 * 0x4000]
        self.ram = bytearray(0x800)
        self.tick = 0
        self.apu_log = []          # (tick, addr, value)
        self.bad_writes = {}       # addr -> count for off-map writes
        self.cpu = CPU(self.read, self.write)

    def read(self, addr):
        if addr < 0x2000:
            return self.ram[addr & 0x7FF]
        if addr < 0x8000:
            return 0
        if addr < 0xC000:
            return self.bank6[addr - 0x8000]
        return self.fixed[addr - 0xC000]

    def write(self, addr, v):
        if addr < 0x2000:
            self.ram[addr & 0x7FF] = v
        elif 0x4000 <= addr < 0x4020:
            self.apu_log.append((self.tick, addr, v))
        elif addr < 0x4000 or addr >= 0x8000:
            self.bad_writes[addr] = self.bad_writes.get(addr, 0) + 1
        # $4020-$7FFF writes ignored (expansion area, unused on this cart)

    def call(self, addr, a=0):
        cpu = self.cpu
        cpu.a = a
        cpu.x = 0
        cpu.y = 0
        cpu.push16(SENTINEL - 1)
        cpu.pc = addr
        return cpu.run_until(SENTINEL, 500000)

    def sound_tick(self):
        steps = self.call(0x8000)
        # NMI wrapper ($C058-$C067): a finished music id in $B7 is
        # re-requested (looping BGM) once no music channel is active.
        b7 = self.ram[0xB7]
        if b7 and (self.ram[0xF1] & 0x0F) == 0:
            self.ram[0xB6] = b7
            self.ram[0xF0] = b7
            self.ram[0xB7] = 0
        self.tick += 1
        return steps

    def request(self, sound_id):
        """Request exactly as the game does (VM/native dispatch rule)."""
        if 0x22 <= sound_id <= 0x78:
            self.call(0xCE31, a=sound_id)   # VM SOUND path (priority gate)
        else:
            self.call(0xCE20, a=sound_id)   # native path

    def cold_init(self):
        """Zeroed-RAM first tick self-initializes the engine (id 0)."""
        self.sound_tick()
        self.sound_tick()


# ---------------------------------------------------------------------
# APU synthesis
# ---------------------------------------------------------------------

class Apu:
    def __init__(self, read_mem):
        self.read_mem = read_mem
        self.reg = [0] * 0x18       # $4000-$4017
        self.pulse = [self._pulse(), self._pulse()]
        self.tri_step = 0
        self.tri_timer = 0.0
        self.tri_linear = 0
        self.tri_reload = False
        self.tri_length = 0
        self.noise_lfsr = 1
        self.noise_timer = 0.0
        self.noise_env = self._env()
        self.noise_length = 0
        self.dmc = {'out': 0, 'addr': 0xC000, 'left': 0, 'bits': 0,
                    'shift': 0, 'timer': 0.0, 'active': False}
        self.cycles = 0.0
        self.qf_acc = 0.0
        self.hf_acc = 0.0

    @staticmethod
    def _env():
        return {'decay': 0, 'divider': 0, 'start': False}

    @staticmethod
    def _pulse():
        return {'phase': 0.0, 'length': 0, 'env': {'decay': 0, 'divider': 0,
                                                  'start': False}}

    # -- register writes ------------------------------------------------
    def write(self, addr, v):
        off = addr - 0x4000
        self.reg[off] = v
        if addr in (0x4003, 0x4007):
            p = self.pulse[(addr - 0x4000) >> 2]
            if self.reg[0x15] & (1 << ((addr - 0x4000) >> 2)):
                p['length'] = LEN_TABLE[v >> 3]
            p['env']['start'] = True
            p['phase'] = 0.0
        elif addr == 0x400B:
            if self.reg[0x15] & 0x04:
                self.tri_length = LEN_TABLE[v >> 3]
            self.tri_reload = True
        elif addr == 0x400F:
            if self.reg[0x15] & 0x08:
                self.noise_length = LEN_TABLE[v >> 3]
            self.noise_env['start'] = True
        elif addr == 0x4011:
            self.dmc['out'] = v & 0x7F
        elif addr == 0x4015:
            for i in range(2):
                if not (v & (1 << i)):
                    self.pulse[i]['length'] = 0
            if not (v & 0x04):
                self.tri_length = 0
            if not (v & 0x08):
                self.noise_length = 0
            d = self.dmc
            if v & 0x10:
                if d['left'] == 0:
                    d['addr'] = 0xC000 + (self.reg[0x12] << 6)
                    d['left'] = (self.reg[0x13] << 4) + 1
                    d['active'] = True
            else:
                d['left'] = 0
                d['active'] = False

    # -- frame-counter clocks (approx. 240 Hz / 120 Hz) ------------------
    def _clock_quarter(self):
        for i, p in enumerate(self.pulse):
            self._clock_env(p['env'], self.reg[i * 4])
        self._clock_env(self.noise_env, self.reg[0x0C])
        if self.tri_reload:
            self.tri_linear = self.reg[0x08] & 0x7F
        elif self.tri_linear > 0:
            self.tri_linear -= 1
        if not (self.reg[0x08] & 0x80):
            self.tri_reload = False

    def _clock_half(self):
        for i, p in enumerate(self.pulse):
            if not (self.reg[i * 4] & 0x20) and p['length'] > 0:
                p['length'] -= 1
        if not (self.reg[0x08] & 0x80) and self.tri_length > 0:
            self.tri_length -= 1
        if not (self.reg[0x0C] & 0x20) and self.noise_length > 0:
            self.noise_length -= 1

    @staticmethod
    def _clock_env(env, ctrl):
        if env['start']:
            env['start'] = False
            env['decay'] = 15
            env['divider'] = ctrl & 0x0F
        elif env['divider'] == 0:
            env['divider'] = ctrl & 0x0F
            if env['decay'] > 0:
                env['decay'] -= 1
            elif ctrl & 0x20:
                env['decay'] = 15
        else:
            env['divider'] -= 1

    @staticmethod
    def _vol(env, ctrl):
        if ctrl & 0x10:
            return ctrl & 0x0F
        return env['decay']

    # -- sample generation ------------------------------------------------
    def samples(self, count):
        out = []
        dt = CPU_FREQ / SAMPLE_RATE
        for _ in range(count):
            self.qf_acc += dt
            self.hf_acc += dt
            while self.qf_acc >= 7457.0:
                self.qf_acc -= 7457.0
                self._clock_quarter()
            while self.hf_acc >= 14914.0:
                self.hf_acc -= 14914.0
                self._clock_half()
            out.append(self._mix(dt))
        return out

    def _mix(self, dt):
        r = self.reg
        pvol = []
        for i, p in enumerate(self.pulse):
            base = i * 4
            period = r[base + 2] | ((r[base + 3] & 0x07) << 8)
            vol = self._vol(p['env'], r[base])
            if p['length'] == 0 or period < 8 or not (r[0x15] & (1 << i)):
                vol = 0
            else:
                sweep = r[base + 1]
                if sweep & 0x80:
                    shift = sweep & 0x07
                    delta = period >> shift
                    target = period - delta if (sweep & 0x08) else \
                        period + delta
                    if target > 0x7FF:
                        vol = 0
            p['phase'] = (p['phase'] + dt / (2.0 * (period + 1))) % 8.0 \
                if period >= 8 else p['phase']
            duty = DUTY_SEQ[(r[base] >> 6) & 3][int(p['phase']) & 7]
            pvol.append(vol if duty else 0)
        psum = pvol[0] + pvol[1]
        pulse_out = 95.88 / ((8128.0 / psum) + 100.0) if psum else 0.0

        # triangle
        tperiod = r[0x0A] | ((r[0x0B] & 0x07) << 8)
        tri_val = 0.0
        if (r[0x15] & 0x04) and self.tri_length > 0 and self.tri_linear > 0 \
                and tperiod >= 2:
            self.tri_timer -= dt
            while self.tri_timer <= 0:
                self.tri_timer += (tperiod + 1)
                self.tri_step = (self.tri_step + 1) & 31
            tri_val = TRI_SEQ[self.tri_step]
        # noise
        nvol = self._vol(self.noise_env, r[0x0C])
        if self.noise_length == 0 or not (r[0x15] & 0x08):
            nvol = 0
        nperiod = NOISE_PERIOD[r[0x0E] & 0x0F]
        self.noise_timer -= dt
        while self.noise_timer <= 0:
            self.noise_timer += nperiod
            l = self.noise_lfsr
            tap = (l >> 6) & 1 if (r[0x0E] & 0x80) else (l >> 1) & 1
            fb = (l & 1) ^ tap
            self.noise_lfsr = (l >> 1) | (fb << 14)
        noise_val = nvol if (self.noise_lfsr & 1) == 0 else 0
        # DMC
        d = self.dmc
        if d['active'] and d['left'] >= 0:
            d['timer'] -= dt
            while d['timer'] <= 0:
                d['timer'] += DMC_RATE[r[0x10] & 0x0F]
                if d['bits'] == 0:
                    if d['left'] > 0:
                        d['shift'] = self.read_mem(d['addr'])
                        d['addr'] = 0x8000 if d['addr'] >= 0xFFFF else \
                            d['addr'] + 1
                        d['left'] -= 1
                        d['bits'] = 8
                    elif r[0x10] & 0x40:
                        d['addr'] = 0xC000 + (r[0x12] << 6)
                        d['left'] = (r[0x13] << 4) + 1
                    else:
                        d['active'] = False
                        break
                if d['bits'] > 0:
                    if d['shift'] & 1:
                        if d['out'] <= 125:
                            d['out'] += 2
                    elif d['out'] >= 2:
                        d['out'] -= 2
                    d['shift'] >>= 1
                    d['bits'] -= 1
        tnd_in = tri_val / 8227.0 + noise_val / 12241.0 + d['out'] / 22638.0
        tnd_out = 159.79 / ((1.0 / tnd_in) + 100.0) if tnd_in > 0 else 0.0
        v = (pulse_out + tnd_out) * 0.9
        return max(-1.0, min(1.0, v))


def render_sound(sound_id, max_seconds=20.0):
    """Render one sound id in isolation (fresh engine, as at boot).

    Returns (machine, init_writes, per_tick): init_writes are the APU
    writes from the cold-init ticks (they seed $4015 etc.), per_tick the
    writes of each tick after the request. Ticking stops once the
    engine's channel-active mask $F1 has been all-clear for 20 ticks
    after having been active (the engine keeps refreshing control
    registers every tick even when idle, so write counts can't detect
    the end; $F1 can).
    """
    m = Machine()
    m.cold_init()
    init_writes = [(a, v) for (_t, a, v) in m.apu_log]
    m.apu_log.clear()
    m.request(sound_id)
    max_ticks = int(max_seconds * FRAME_RATE)
    per_tick = []
    active_seen = False
    quiet = 0
    for t in range(max_ticks):
        start = len(m.apu_log)
        m.sound_tick()
        per_tick.append([(a, v) for (_t, a, v) in m.apu_log[start:]])
        if m.ram[0xF1] & 0x3F:
            active_seen = True
            quiet = 0
        elif active_seen:
            quiet += 1
            if quiet >= 20:
                break
        elif t >= 120:
            break  # control code / never started (e.g. $7F reset)
    return m, init_writes, per_tick


def synth_wav(init_writes, per_tick, read_mem):
    apu = Apu(read_mem)
    for addr, v in init_writes:
        apu.write(addr, v)
    samples = []
    acc = 0.0
    per_frame = SAMPLE_RATE / FRAME_RATE
    for writes in per_tick:
        for addr, v in writes:
            apu.write(addr, v)
        acc += per_frame
        n = int(acc)
        acc -= n
        samples.extend(apu.samples(n))
    return samples


def trim(samples, tail_ms=80):
    last = -1
    for i, s in enumerate(samples):
        if abs(s) > 0.0004:
            last = i
    if last < 0:
        return []
    keep = min(len(samples), last + int(SAMPLE_RATE * tail_ms / 1000))
    return samples[:keep]


def write_wav(path, samples):
    frames = b''.join(struct.pack('<h', int(max(-1.0, min(1.0, s)) * 32000))
                      for s in samples)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(frames)


def stats(name, per_tick, samples, machine):
    nw = sum(len(t) for t in per_tick)
    regs = {}
    periods = []
    for tick in per_tick:
        for a, v in tick:
            regs[a] = regs.get(a, 0) + 1
            if a in (0x4003, 0x4007):
                pass
    peak = max((abs(s) for s in samples), default=0.0)
    print('%s: ticks=%d apu_writes=%d regs=%s peak=%.3f dur=%.2fs bad=%s' %
          (name, len(per_tick), nw,
           {hex(k): v for k, v in sorted(regs.items())}, peak,
           len(samples) / SAMPLE_RATE,
           {hex(k): v for k, v in machine.bad_writes.items()}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--id', action='append', dest='ids',
                    help='sound id, e.g. 0x74 (repeatable)')
    ap.add_argument('--outdir', default='extracted/sounds')
    ap.add_argument('--timeline', action='store_true',
                    help='state-1 sequence consistency check (no files)')
    ap.add_argument('--max-seconds', type=float, default=20.0)
    args = ap.parse_args()

    if args.timeline:
        # Boot-fresh engine; $7F at frame 0, $74 at 464, $73 at 614,
        # exactly as the state-1 script/native code request them.
        m = Machine()
        m.cold_init()
        m.apu_log.clear()
        sched = {0: 0x7F, 464: 0x74, 614: 0x73}
        timeline = []
        for t in range(674 + 300):
            if t in sched:
                m.request(sched[t])
            timeline.append(t)
            m.sound_tick()
        writes = {}
        for (tick, a, v) in m.apu_log:
            writes.setdefault(tick - 2, []).append((a, v))  # -2 init ticks
        for sid, at in ((0x74, 464), (0x73, 614)):
            _m2, _iw, iso = render_sound(sid)
            seg = [writes.get(at + i, []) for i in range(len(iso))]
            iso_trim = iso[:]
            while iso_trim and not iso_trim[-1]:
                iso_trim.pop()
            seg_trim = seg[:len(iso_trim)]
            same = seg_trim == iso_trim
            print('timeline $%02X @%d: isolated ticks=%d, match=%s' %
                  (sid, at, len(iso_trim), same))
            if not same:
                for i, (s, q) in enumerate(zip(seg_trim, iso_trim)):
                    if s != q:
                        print('  first diff at +%d: timeline=%s iso=%s' %
                              (i, s, q))
                        break
        return

    ids = [int(s, 0) for s in (args.ids or ['0x7F', '0x74', '0x73'])]
    os.makedirs(args.outdir, exist_ok=True)
    meta = {}
    for sid in ids:
        m, init_writes, per_tick = render_sound(sid, args.max_seconds)
        samples = trim(synth_wav(init_writes, per_tick, m.read))
        name = 'snd_%02x' % sid
        if samples:
            path = os.path.join(args.outdir, name + '.wav')
            write_wav(path, samples)
        else:
            path = None
        stats('%s ($%02X)' % (name, sid), per_tick, samples, m)
        meta[name] = {'id': sid, 'path': path,
                      'seconds': len(samples) / SAMPLE_RATE,
                      'ticks': len(per_tick)}
    with open(os.path.join(args.outdir, 'sounds.json'), 'w') as f:
        json.dump(meta, f, indent=1)


if __name__ == '__main__':
    main()
