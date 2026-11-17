"""Reconstruct sprites straight from emulator traces.

Everything here works on raw OAM + CHR data, so the output is pixel exact.
"""
import numpy as np
from PIL import Image

# thealmightyguru NES palette (same table the capture core renders with)
NES_PALETTE = [
    0x7C7C7C, 0x0000FC, 0x0000BC, 0x4428BC, 0x940084, 0xA80020, 0xA81000, 0x881400,
    0x503000, 0x007800, 0x006800, 0x005800, 0x004058, 0x000000, 0x000000, 0x000000,
    0xBCBCBC, 0x0078F8, 0x0058F8, 0x6844FC, 0xD800CC, 0xE40058, 0xF83800, 0xE45C10,
    0xAC7C00, 0x00B800, 0x00A800, 0x00A844, 0x008888, 0x000000, 0x000000, 0x000000,
    0xF8F8F8, 0x3CBCFC, 0x6888FC, 0x9878F8, 0xF878F8, 0xF85898, 0xF87858, 0xFCA044,
    0xF8B800, 0xB8F818, 0x58D854, 0x58F898, 0x00E8D8, 0x787878, 0x000000, 0x000000,
    0xFCFCFC, 0xA4E4FC, 0xB8B8F8, 0xD8B8F8, 0xF8B8F8, 0xF8A4C0, 0xF0D0B0, 0xFCE0A8,
    0xF8D878, 0xD8F878, 0xB8F8B8, 0xB8F8D8, 0x00FCFC, 0xF8D8F8, 0x000000, 0x000000,
]


def color(index):
    c = NES_PALETTE[index & 0x3F]
    return ((c >> 16) & 255, (c >> 8) & 255, c & 255)


def tile_pixels(chr_data, offset):
    """Decode a 2bpp tile at a byte offset of a CHR blob -> 8x8 uint8 0..3."""
    lo = chr_data[offset:offset + 8]
    hi = chr_data[offset + 8:offset + 16]
    out = np.empty((8, 8), np.uint8)
    for y in range(8):
        l, h = lo[y], hi[y]
        for x in range(8):
            bit = 7 - x
            out[y, x] = ((l >> bit) & 1) | (((h >> bit) & 1) << 1)
    return out


class ChrWindows:
    """Maps a PPU pattern-table address ($0000-$1FFF) to ROM data for a frame."""

    def __init__(self, rom_chr, chr_lo, chr_hi, chr_mode):
        self.chr = rom_chr
        self.chr_lo = int(chr_lo) & 0xFF
        self.chr_hi = int(chr_hi) & 0xFF
        self.chr_mode = int(chr_mode) & 1  # MMC1 mode_chr: 0 = 8KB, 1 = twin 4KB

    def read(self, address, size):
        """Read PPU pattern bytes [address, address+size) from the ROM."""
        address = int(address)
        size = int(size)
        out = bytearray()
        while size > 0:
            if self.chr_mode == 0:  # one 8KB bank mapped at $0000
                base = self.chr_lo * 0x2000
                n = min(size, 0x2000 - address)
                out += self.chr[base + address: base + address + n]
            else:
                if address < 0x1000:
                    base, off = self.chr_lo * 0x1000, address
                else:
                    base, off = self.chr_hi * 0x1000, address - 0x1000
                n = min(size, 0x1000 - off)
                out += self.chr[base + off: base + off + n]
            address += n
            size -= n
        return bytes(out)


def sprite_tile(rec, chr_win, tile_index, sprite_page):
    addr = sprite_page * 0x1000 + (tile_index & 0xFF) * 16
    return tile_pixels(chr_win.read(addr, 16), 0)


def render_sprite(rec, chr_win, s, long_sprites=None, spr_page=1):
    """Return (rgba HxW uint8 array) of one hardware sprite, already flipped."""
    # s['pal'] is the 4..7 sprite palette number
    pal = rec.palette[s['pal'] * 4: s['pal'] * 4 + 4]
    if long_sprites is None:
        long_sprites = bool(rec.long_sprites)
    if long_sprites:
        t0 = s['tile'] & 0xFE
        idx = tile_pixels(chr_win.read(s['tile'] & 0x01 * 0 + (0x1000 if s['tile'] & 1 else 0) + s['tile'] * 16, 16), 0)
        img = np.zeros((16, 8), np.uint8)
        # 8x16 mode: bit0 of the tile index picks the pattern table, pairs are +1
        pt = 0x1000 if (s['tile'] & 1) else 0x0000
        for k in range(2):
            ta = pt + ((s['tile'] & 0xFE) + k) * 16
            img[k * 8:(k + 1) * 8] = tile_pixels(chr_win.read(ta, 16), 0)
    else:
        img = sprite_tile(rec, chr_win, s['tile'], spr_page).copy()
    if s['flipx']:
        img = img[:, ::-1]
    if s['flipy']:
        img = img[::-1, :]
    rgba = np.zeros(img.shape + (4,), np.uint8)
    for i in range(4):
        m = img == i
        c = color(pal[i])
        rgba[m, 0], rgba[m, 1], rgba[m, 2] = c
        rgba[m, 3] = 255 if i else 0
    return rgba


def oam_composite(rec, chr_win, long_sprites=None):
    """Composite every visible sprite into a 256x240 RGBA image (no bg)."""
    if long_sprites is None:
        long_sprites = bool(rec.long_sprites)
    canvas = np.zeros((240, 256, 4), np.uint8)
    for s in sorted(rec.sprites, key=lambda s: -s['prio']):
        if s['y'] >= 240:
            continue
        sp = render_sprite(rec, chr_win, s, long_sprites, rec.spr_page)
        h, w = sp.shape[:2]
        y0, x0 = s['y'], s['x']
        if y0 < 0 or x0 < 0:
            continue
        y1, x1 = min(240, y0 + h), min(256, x0 + w)
        src = sp[:y1 - y0, :x1 - x0]
        alpha = src[:, :, 3] > 0
        dst = canvas[y0:y1, x0:x1]
        for c in range(3):
            np.copyto(dst[:, :, c], src[:, :, c], where=alpha)
        np.copyto(dst[:, :, 3], src[:, :, 3], where=alpha)
    return canvas
