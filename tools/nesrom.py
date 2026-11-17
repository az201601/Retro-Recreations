"""Minimal NES ROM reader + CHR pattern-table tools for Chip 'n Dale: Rescue Rangers 2 (USA).

No emulator: we read the iNES container, split PRG/CHR, decode 2bpp tiles,
and render them as indexed PNGs so that sprites / tilesets can be carved out.
"""
import os
import numpy as np
from PIL import Image

ROM_PATH = os.path.join(os.path.dirname(__file__), "..",
                        "Chip 'n Dale - Rescue Rangers 2 (USA).nes")


class NesRom:
    def __init__(self, path=ROM_PATH):
        self.data = open(path, "rb").read()
        assert self.data[:4] == b"NES\x1a"
        self.prg_banks = self.data[4]
        self.chr_banks = self.data[5]
        self.flags6 = self.data[6]
        self.flags7 = self.data[7]
        self.mapper = (self.flags7 & 0xF0) | (self.flags6 >> 4)
        off = 16
        self.prg = self.data[off:off + self.prg_banks * 16384]
        off += self.prg_banks * 16384
        self.chr = self.data[off:off + self.chr_banks * 8192]

    # ---- CHR -----------------------------------------------------------
    def tile(self, bank, index):
        """Return 8x8 uint8 array of colour indices 0..3."""
        base = bank * 8192 + index * 16
        b = self.chr[base:base + 16]
        lo = b[:8]
        hi = b[8:]
        out = np.zeros((8, 8), np.uint8)
        for y in range(8):
            for x in range(8):
                bit = 7 - x
                out[y, x] = ((lo[y] >> bit) & 1) | (((hi[y] >> bit) & 1) << 1)
        return out

    def bank_image(self, bank, tiles_per_row=16):
        n = 256
        rows = n // tiles_per_row
        img = np.zeros((rows * 8, tiles_per_row * 8), np.uint8)
        for i in range(n):
            r, c = divmod(i, tiles_per_row)
            img[r * 8:r * 8 + 8, c * 8:c * 8 + 8] = self.tile(bank, i)
        return img


# NES master palette (2C02, commonly used "NESdev" table)
NES_PALETTE = [
    0x666666, 0x002A88, 0x1412A7, 0x3B00A4, 0x5C007E, 0x6E0040, 0x6C0600, 0x561D00,
    0x333500, 0x0B4800, 0x005200, 0x004F08, 0x00404D, 0x000000, 0x000000, 0x000000,
    0xADADAD, 0x155FD9, 0x4240FF, 0x7527FE, 0xA01ACC, 0xB71E7B, 0xB53120, 0x994E00,
    0x6B6D00, 0x378700, 0x009400, 0x008F0E, 0x007B7F, 0x000000, 0x000000, 0x000000,
    0xFFFEFF, 0x64B0FF, 0x9290FF, 0xC676FF, 0xF36AFF, 0xFE6ECC, 0xFE8170, 0xEA9E22,
    0xBCBE00, 0x88D800, 0x4CE400, 0x3BD845, 0x3FD6D5, 0x3D3D3D, 0x000000, 0x000000,
    0xFFFEFF, 0xC7E5FF, 0xD5D4FF, 0xEDC9FF, 0xFBC3FF, 0xFEC4EA, 0xFECCC4, 0xF7D7A5,
    0xE4E594, 0xCFEF96, 0xBDF4AB, 0xB3F3CC, 0xB5EBF2, 0xB8B8B8, 0x000000, 0x000000,
]


def idx_to_rgba(idx, palette4, transparent_index0=True):
    """idx: HxW uint8 0..3 ; palette4: list of 4 NES colour ids."""
    h, w = idx.shape
    rgba = np.zeros((h, w, 4), np.uint8)
    for i in range(4):
        c = NES_PALETTE[palette4[i] & 0x3F]
        m = idx == i
        rgba[m, 0] = (c >> 16) & 255
        rgba[m, 1] = (c >> 8) & 255
        rgba[m, 2] = c & 255
        rgba[m, 3] = 255
    if transparent_index0:
        rgba[idx == 0, 3] = 0
    return rgba


def save_index_png(arr, path, scale=1):
    """Save indexed 0..3 image as a dark-on-light PNG (easy to eyeball)."""
    shades = np.array([0, 85, 170, 255], np.uint8)
    rgb = np.dstack([shades[arr]] * 3)
    im = Image.fromarray(rgb, "RGB")
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
    return im
