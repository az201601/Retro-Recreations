#!/usr/bin/env python3
"""
nes_render.py -- render a NES frame from Nestopia savestate internals.

Uses the savestate's nametables, palette RAM, OAM and mapper bank registers
plus the ROM's CHR-ROM to reproduce exactly what the PPU displays. Lets us
verify every extracted asset pixel-for-pixel against the emulator's own
output, and gives clean access to tile indices / palettes / sprite layouts.
"""
from __future__ import annotations

import struct
import sys

import numpy as np

sys.path.insert(0, "/home/user/Retro-Recreations/tools")
from nest_state import parse_state, find, ppu_dump, cpu_regs  # noqa: E402

ROM_PATH = "/home/user/Retro-Recreations/Chip 'n Dale - Rescue Rangers 2 (USA).nes"
PAL_PATH = "/tmp/nestopia/palettes/Composite Direct (FBX).pal"


def load_rom(path=ROM_PATH):
    rom = open(path, "rb").read()
    prg = rom[16:16 + 8 * 16384]
    chr_rom = rom[16 + 8 * 16384:16 + 8 * 16384 + 16 * 8192]
    return prg, chr_rom


def master_palette(path=PAL_PATH):
    data = open(path, "rb").read()
    if len(data) == 192:
        return np.frombuffer(data, dtype=np.uint8).reshape(64, 3)
    raise ValueError(f"unexpected palette size {len(data)}")


def decode_bank_tiles(rom_bytes: np.ndarray):
    """(n, 8, 8) uint8 pixel indices 0..3 from 16-byte-per-tile data."""
    tiles = rom_bytes.reshape(-1, 16)
    lo = tiles[:, :8].astype(np.uint16)
    hi = tiles[:, 8:].astype(np.uint16)
    bits = np.arange(7, -1, -1)
    out = ((lo[:, :, None] >> bits) & 1) | (((hi[:, :, None] >> bits) & 1) << 1)
    return out.astype(np.uint8)


class StateView:
    """Bank-aware view of a savestate's PPU-relevant data."""

    def __init__(self, state_bytes: bytes, chr_rom: bytes):
        self.st = parse_state(state_bytes)
        self.chr_rom = np.frombuffer(chr_rom, dtype=np.uint8)
        ppu = ppu_dump(self.st)
        self.palette = np.frombuffer(ppu["palette"][:32], dtype=np.uint8)
        self.oam = ppu["oam"][:256]
        self.nmt = np.frombuffer(ppu["nametable"][:2048], dtype=np.uint8)
        reg = find(self.st, "PPU", "REG")
        self.reg = reg if isinstance(reg, (bytes, bytearray)) else reg[0]
        self.ctrl = self.reg[0]
        self.mask = self.reg[1]
        t = struct.unpack_from("<H", self.reg, 3)[0]
        self.t = t
        self.coarse_x = t & 31
        self.coarse_y = (t >> 5) & 31
        self.nt_x = (t >> 10) & 1
        self.nt_y = (t >> 11) & 1
        self.xfine = self.reg[7] & 7
        self.sprite_pattern = 0x1000 if (self.ctrl & 0x08) else 0x0000
        self.bg_pattern = 0x1000 if (self.ctrl & 0x10) else 0x0000
        self.sprites_8x16 = bool(self.ctrl & 0x20)
        bnk = find(self.st, "IMG", "MPR", "CHR", "BNK")
        bnk = bnk if isinstance(bnk, (bytes, bytearray)) else bnk[0]
        self.chr_pages = [bnk[i * 3 + 1] | (bnk[i * 3 + 2] << 8) for i in range(8)]
        self._tile_cache = {}

    def pattern_tiles(self, pattern_base: int):
        """(256, 8, 8) tiles for the pattern table at 0x0000 or 0x1000."""
        key = pattern_base
        if key in self._tile_cache:
            return self._tile_cache[key]
        # 2KB per pattern table (256 tiles = 4KB actually; 256*16 = 4096)
        pages = [pattern_base // 1024 + i for i in range(4)]
        rom_off = [self.chr_pages[p] * 1024 for p in pages]
        data = np.concatenate([self.chr_rom[o:o + 1024] for o in rom_off])
        tiles = decode_bank_tiles(data)
        self._tile_cache[key] = tiles
        return tiles

    def nt_grids(self, cx, cy, ntx, nty):
        """32x30 tile-index and palette grids for screen at scroll (cx,cy,ntx,nty)."""
        gx, gy = np.meshgrid(np.arange(32), np.arange(30))
        nx = (gx + cx + ntx * 32) % 64
        ny = (gy + cy + nty * 30) % 60
        phys = (nx // 32)          # 0/1 physical nametable
        px, py = nx % 32, ny % 30
        base = phys * 1024
        idx = base + py * 32 + px
        tiles = self.nmt[idx]
        aidx = base + 960 + (py // 4) * 8 + (px // 4)
        attr = self.nmt[aidx]
        shift = ((py % 4) // 2) * 4 + ((px % 4) // 2) * 2
        pals = (attr >> shift) & 3
        return tiles, pals

    def render(self, master: np.ndarray, sprites: bool = True, cx=None, cy=None, ntx=None, nty=None):
        if cx is None:
            cx, cy, ntx, nty = self.coarse_x, self.coarse_y, self.nt_x, self.nt_y
        tiles, pals = self.nt_grids(cx, cy, ntx, nty)
        bank = self.pattern_tiles(self.bg_pattern)
        px = bank[tiles]                       # (30,32,8,8)
        img_idx = px.transpose(0, 2, 1, 3).reshape(240, 256)
        pal_idx = np.repeat(np.repeat(pals, 8, 0), 8, 1)  # (240,256)
        color_idx = self.palette[pal_idx * 4 + img_idx] & 0x3F
        img = master[color_idx]
        bg_prio = img_idx != 0
        if not (self.mask & 0x02):          # BG left-clip: show backdrop in x<8
            img[:, :8] = master[self.palette[0] & 0x3F]
            bg_prio[:, :8] = False
        if not sprites:
            return img
        sbank = self.pattern_tiles(self.sprite_pattern)
        for i in range(63, -1, -1):
            y, tile, attr, x = self.oam[i * 4:i * 4 + 4]
            if y >= 239:
                continue
            pal = attr & 3
            flip_h = bool(attr & 0x40)
            flip_v = bool(attr & 0x80)
            behind = bool(attr & 0x20)
            if self.sprites_8x16:
                t0 = (tile & 0xFE)
                sub = sbank[t0:t0 + 2].reshape(16, 8)
                full = np.concatenate([sub, sbank[(tile & 0xFE) + 0x100:(tile & 0xFE) + 0x102].reshape(16, 8)]) if False else sub
                t = full
            else:
                t = sbank[tile]
            for sy in range(t.shape[0]):
                for sx in range(8):
                    pxv = t[(t.shape[0] - 1 - sy) if flip_v else sy][(7 - sx) if flip_h else sx]
                    yy, xx = y + 1 + sy, x + sx
                    if not (self.mask & 0x04) and xx < 8:   # sprite left-clip
                        continue
                    if pxv and yy < 240 and xx < 256 and not (behind and bg_prio[yy, xx]):
                        ci = self.palette[16 + pal * 4 + pxv] & 0x3F
                        img[yy, xx] = master[ci]
        return img

    def sprite_mask(self):
        """Where active sprites actually paint (for debugging OAM)."""
        m = np.zeros((240, 256), dtype=np.uint8)
        sbank = self.pattern_tiles(self.sprite_pattern)
        for i in range(64):
            y, tile, attr, x = self.oam[i * 4:i * 4 + 4]
            if y >= 239:
                continue
            t = sbank[tile]
            for sy in range(8):
                for sx in range(8):
                    if t[sy][sx]:
                        yy, xx = y + 1 + sy, x + sx
                        if yy < 240 and xx < 256:
                            m[yy, xx] = 255
        return m


def render_file(state_path, out="work/state_render.png", master=None, **kw):
    from PIL import Image
    prg, chr_rom = load_rom()
    if master is None:
        master = master_palette()
    sv = StateView(open(state_path, "rb").read(), chr_rom)
    img = sv.render(master, **kw)
    if out:
        Image.fromarray(np.uint8(img)).save(out)
    return sv, img


def fit_scroll(state_path, ref_png, out_png="work/state_render_fit.png"):
    from PIL import Image
    prg, chr_rom = load_rom()
    master = master_palette()
    sv = StateView(open(state_path, "rb").read(), chr_rom)
    ref = np.array(Image.open(ref_png).convert("RGB")).astype(int)
    best = None
    for nty in (0, 1):
        for ntx in (0, 1):
            for cy in range(30):
                for cx in range(32):
                    img = sv.render(master, sprites=False, cx=cx, cy=cy, ntx=ntx, nty=nty).astype(int)
                    d = np.abs(img - ref).mean()
                    if best is None or d < best[0]:
                        best = (d, cx, cy, ntx, nty, img)
    d, cx, cy, ntx, nty, img = best
    print(f"best scroll: coarse=({cx},{cy}) nt=({ntx},{nty}) bgdiff={d:.3f}")
    img2 = sv.render(master, sprites=True, cx=cx, cy=cy, ntx=ntx, nty=nty)
    Image.fromarray(np.uint8(img2)).save(out_png)
    return best


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "--fit":
        fit_scroll(sys.argv[1], sys.argv[3])
    else:
        sv, img = render_file(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "work/state_render.png")
        print(f"ctrl=${sv.ctrl:02X} mask=${sv.mask:02X} t=${sv.t:04X} scroll=({sv.coarse_x*8},{sv.coarse_y*8}) nt=({sv.nt_x},{sv.nt_y})")
        print(f"sprites: 8x16={sv.sprites_8x16} pattern=${sv.sprite_pattern:04X}  bg pattern=${sv.bg_pattern:04X}")
        print("wrote", sys.argv[2] if len(sys.argv) > 2 else "work/state_render.png")
