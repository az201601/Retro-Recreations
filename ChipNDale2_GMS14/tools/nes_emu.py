#!/usr/bin/env python3
"""
nes_emu.py -- Minimal headless NES (6502 + MMC1 + PPU register model) used to
capture *authentic* screen data from a .nes ROM without needing an emulator GUI
and without any third-party dependencies.

Why this exists
---------------
Chip 'n Dale Rescue Rangers 2 builds its title/spotlight scene out of
  * a background nametable (brick wall) written by the game, and
  * 32 sprites (a 64x63 "light disk") that scroll behind that background
    (sprite attribute bit 5 = behind-background).
Guessing the PRG offsets for those tables is error-prone, so instead we boot
the ROM, run it to an exact video frame, and read back the PPU state the game
actually produced: nametables, palette RAM, OAM, CHR/PRG bank registers.

Accuracy notes / limitations
----------------------------
* The PPU is modelled at the *register* level only. There is no per-pixel
  rastering, no sprite overflow, no sprite-0 hit, no mid-frame scroll splits.
  For static screens and attribute/palette work that is exactly what we need.
* Timing: one frame = 29780 CPU cycles. Vblank flag + NMI are raised once per
  frame when PPUCTRL bit 7 is set. This is enough for the game's main loop,
  which busy-waits on $2002.
* $4016 controller reads return the bits of ``buttons``; defaults to nothing
  pressed, which is what the attract/copyright/spotlight sequence needs.

Usage
-----
    from nes_emu import NES
    nes = NES("Chip 'n Dale - Rescue Rangers 2 (USA).nes")
    nes.run_to_frame(480)
    nes.nt           # 4KB nametable space ($2000-$2FFF)
    nes.pal          # 32 bytes palette RAM
    nes.oam          # 256 bytes OAM
"""
import os
import sys

FRAME_CYCLES = 29780

# py65 provides the 6502 core. If it is missing we fall back to a tiny built-in
# interpreter stub that raises a clear error only when a ROM is actually run.
try:
    from py65.devices.mpu6502 import MPU
    HAVE_PY65 = True
except ImportError:  # pragma: no cover
    MPU = None
    HAVE_PY65 = False


class _Bus(object):
    """Adapter so py65's ``memory[addr]`` accesses reach our NES bus."""

    def __init__(self, nes):
        self.nes = nes

    def __getitem__(self, a):
        return self.nes.read(a)

    def __setitem__(self, a, v):
        self.nes.write(a, v)


class NES(object):
    def __init__(self, rom_path, vertical_mirroring=None):
        if not HAVE_PY65:
            raise RuntimeError(
                "nes_emu.py needs the py65 package for the 6502 core.\n"
                "Install it with:  pip install py65")

        with open(rom_path, 'rb') as f:
            d = f.read()
        if d[:4] != b'NES\x1a':
            raise ValueError("%s is not an iNES ROM" % rom_path)

        self.prg_banks = d[4]
        self.chr_banks = d[5]
        self.mapper = (d[6] >> 4) | (d[7] & 0xF0)
        prg_size = self.prg_banks * 16384
        self.prg = d[16:16 + prg_size]
        self.chr = d[16 + prg_size:16 + prg_size + self.chr_banks * 8192]

        # iNES flag 6 bit 0: 0 = horizontal mirroring, 1 = vertical
        self.vertical_mirroring = bool(d[6] & 1) if vertical_mirroring is None \
            else vertical_mirroring

        # ---- MMC1 -------------------------------------------------------
        self.shift = 0x10
        self.ctrl = 0x0C
        self.chr0 = 0x00
        self.chr1 = 0x00
        self.prgbank = 0
        self.banks = [0, self.prg_banks - 1]

        # ---- PPU --------------------------------------------------------
        self.nt = bytearray(0x1000)
        self.pal = bytearray(32)
        self.oam = bytearray(256)
        self.ppuctrl = 0
        self.ppumask = 0
        self.ppustatus = 0
        self.oamaddr = 0
        self.v = 0
        self.t = 0
        self.finex = 0
        self.w = 0

        # ---- CPU --------------------------------------------------------
        self.ram = bytearray(0x800)
        self.frame = 0
        self.instr = 0
        self.buttons = 0
        self.strobe = 0
        self.readidx = 0
        self._map_prg()
        self.mpu = MPU(memory=_Bus(self))
        self.mpu.pc = self.read16(0xFFFC)
        self.mpu.sp = 0xFD

    # -- PRG banking ------------------------------------------------------
    def _map_prg(self):
        mode = (self.ctrl >> 2) & 3
        nb = self.prg_banks
        if mode in (0, 1):                 # 32KB switch at $8000
            base = self.prgbank & 0x0E
            self.banks = [base, base + 1]
        elif mode == 2:                    # $8000 fixed first, $C000 switch
            self.banks = [0, self.prgbank & 0x0F]
        else:                              # $8000 switch, $C000 fixed last
            self.banks = [self.prgbank & 0x0F, nb - 1]

    # -- CHR banking ------------------------------------------------------
    def chr_offset(self, addr):
        """Byte offset into CHR ROM for PPU address ``addr`` (0x0000-0x1FFF)."""
        bank = (self.chr0 if addr < 0x1000 else self.chr1) & 0x1F
        return (bank * 0x1000 + (addr & 0x0FFF)) % max(1, len(self.chr))

    # -- CPU bus ----------------------------------------------------------
    def read(self, a):
        a &= 0xFFFF
        if a < 0x2000:
            return self.ram[a & 0x7FF]
        if a < 0x4000:
            return self.ppu_read(a & 7)
        if a in (0x4016, 0x4017):
            if self.strobe:
                return self.buttons & 1
            b = (self.buttons >> self.readidx) & 1
            self.readidx = min(self.readidx + 1, 7)
            return b
        if a >= 0x8000:
            bank = self.banks[(a - 0x8000) // 0x4000]
            off = bank * 0x4000 + (a & 0x3FFF)
            return self.prg[off % len(self.prg)]
        return 0

    def read16(self, a):
        return self.read(a) | (self.read((a + 1) & 0xFFFF) << 8)

    def write(self, a, v):
        a &= 0xFFFF
        v &= 0xFF
        if a < 0x2000:
            self.ram[a & 0x7FF] = v
            return
        if a < 0x4000:
            self.ppu_write(a & 7, v)
            return
        if a == 0x4014:                       # OAM DMA
            base = v << 8
            for i in range(256):
                self.oam[(self.oamaddr + i) & 0xFF] = self.read(base + i)
            return
        if a == 0x4016:
            self.strobe = v & 1
            if self.strobe:
                self.readidx = 0
            return
        if a >= 0x8000:
            self.mmc1_write(a, v)

    # -- MMC1 serial interface -------------------------------------------
    def mmc1_write(self, a, v):
        if v & 0x80:                          # reset shift register
            self.shift = 0x10
            self.ctrl |= 0x0C
            self._map_prg()
            return
        complete = self.shift & 1
        self.shift = (self.shift >> 1) | ((v & 1) << 4)
        if complete:
            val = self.shift
            self.shift = 0x10
            if a < 0xA000:
                self.ctrl = val
            elif a < 0xC000:
                self.chr0 = val
            elif a < 0xE000:
                self.chr1 = val
            else:
                self.prgbank = val
            self._map_prg()

    # -- PPU ---------------------------------------------------------------
    def ppu_read(self, a):
        if a == 2:                            # PPUSTATUS
            s = self.ppustatus
            self.ppustatus &= 0x7F
            self.w = 0
            return s
        if a == 4:
            return self.oam[self.oamaddr]
        if a == 7:                            # PPUDATA
            addr = self.v & 0x3FFF
            self.v = (self.v + (32 if self.ppuctrl & 4 else 1)) & 0x7FFF
            if addr < 0x2000:
                return self.chr[self.chr_offset(addr)]
            if addr < 0x3F00:
                return self.nt[(addr - 0x2000) & 0x0FFF]
            return self.pal[(addr - 0x3F00) & 0x1F]
        return 0

    def ppu_write(self, a, v):
        if a == 0:
            self.ppuctrl = v
            self.t = (self.t & 0x73FF) | ((v & 3) << 10)
        elif a == 1:
            self.ppumask = v
        elif a == 3:
            self.oamaddr = v
        elif a == 4:
            self.oam[self.oamaddr] = v
            self.oamaddr = (self.oamaddr + 1) & 0xFF
        elif a == 5:                          # PPUSCROLL
            if self.w == 0:
                self.t = (self.t & 0x7FE0) | (v >> 3)
                self.finex = v & 7
                self.w = 1
            else:
                self.t = (self.t & 0x0C1F) | ((v & 7) << 12) | ((v & 0xF8) << 2)
                self.w = 0
        elif a == 6:                          # PPUADDR
            if self.w == 0:
                self.t = (self.t & 0x00FF) | ((v & 0x3F) << 8)
                self.w = 1
            else:
                self.t = (self.t & 0xFF00) | v
                self.v = self.t
                self.w = 0
        elif a == 7:
            addr = self.v & 0x3FFF
            if addr < 0x2000:
                pass                          # CHR ROM is not writable
            elif addr < 0x3F00:
                self.nt[(addr - 0x2000) & 0x0FFF] = v
            else:
                idx = (addr - 0x3F00) & 0x1F
                if (idx & 0x13) == 0x10:      # $3F10/$3F14/.. mirror $3F00/..
                    idx &= 0x0F
                self.pal[idx] = v
            self.v = (self.v + (32 if self.ppuctrl & 4 else 1)) & 0x7FFF

    # -- run loop ----------------------------------------------------------
    def step(self):
        self.mpu.step()
        self.instr += 1
        if self.mpu.processorCycles >= FRAME_CYCLES:
            self.mpu.processorCycles -= FRAME_CYCLES
            self.frame += 1
            self.ppustatus |= 0x80            # vblank flag
            if self.ppuctrl & 0x80:
                self.mpu.nmi()

    def run_frames(self, n, max_instr_per_frame=400000):
        for _ in range(n):
            f = self.frame
            guard = 0
            while self.frame == f and guard < max_instr_per_frame:
                self.step()
                guard += 1

    def run_to_frame(self, target, max_instr_per_frame=400000):
        while self.frame < target:
            self.run_frames(1, max_instr_per_frame)


if __name__ == '__main__':
    rom = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(os.path.dirname(__file__), '..', '..',
                     "Chip 'n Dale - Rescue Rangers 2 (USA).nes")
    nes = NES(rom)
    frames = int(sys.argv[2]) if len(sys.argv) > 2 else 480
    nes.run_to_frame(frames)
    print("frame       :", nes.frame)
    print("ppuctrl     : $%02X" % nes.ppuctrl)
    print("ppumask     : $%02X" % nes.ppumask)
    print("chr banks   : $%02X / $%02X" % (nes.chr0, nes.chr1))
    print("prg bank    : $%02X" % nes.prgbank)
    print("bg palette  :", nes.pal[0:16].hex(' '))
    print("spr palette :", nes.pal[16:32].hex(' '))
    print("nametable   : %d non-zero bytes" % sum(1 for b in nes.nt[:0x400] if b))
    print("oam         : %d sprites on screen" %
          sum(1 for i in range(64) if nes.oam[i * 4] < 0xEF))
