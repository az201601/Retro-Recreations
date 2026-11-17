"""Background (nametable) decoding from emulator traces.

A trace record contains the live VRAM (2 KB = 4 name tables + attributes),
palette RAM, CHR banking and the PPU's scroll registers, so a complete,
pixel exact view of the background can be reconstructed without screenshots.
"""
import numpy as np

from . import sprites as S


def name_table(vram, nt=0, mirror="vertical"):
    """Return (tiles 30x32 uint8, attrs 30x32 uint8 0..3) for a name table.

    mirror: vertical = $2000/$2400 (0/1) and $2800/$2C00 (2/3) share banks.
    """
    # 2KB VRAM layout: $2000..$27FF then $2800..$2FFF
    if mirror == "vertical":
        idx = nt % 2
    else:
        idx = nt // 2
    base = idx * 0x400
    tiles = np.zeros((30, 32), np.uint8)
    attrs = np.zeros((30, 32), np.uint8)
    for row in range(30):
        for col in range(32):
            tiles[row, col] = vram[base + row * 32 + col]
    # attribute table: 8x8 bytes, each covers 4x4 tiles (2x2 quads)
    for ay in range(8):
        for ax in range(8):
            a = vram[base + 0x3C0 + ay * 8 + ax]
            for qy in range(2):
                for qx in range(2):
                    shift = (qy * 2 + qx) * 2
                    v = (a >> shift) & 3
                    for ty in range(2):
                        for tx in range(2):
                            row = ay * 4 + qy * 2 + ty
                            col = ax * 4 + qx * 2 + tx
                            if row < 30:
                                attrs[row, col] = v
    return tiles, attrs


def render_bg(vram, palette, chr_win, nt=0, bg_page=0, mirror="vertical",
              scroll_x=0, scroll_y=0, height=240, width=256, tile_override=None):
    """Render a background view. Returns RGBA uint8 array (height x width x 4).

    Only integer tile scrolling is supported (good enough for reconstruction).
    """
    tiles, attrs = name_table(vram, nt, mirror)
    out = np.zeros((height, width, 4), np.uint8)
    tx0 = (scroll_x // 8) % 32
    ty0 = (scroll_y // 8) % 30
    for py in range(0, height, 8):
        for px in range(0, width, 8):
            tc = (tx0 + px // 8) % 32
            tr = (ty0 + py // 8) % 30
            if tile_override is not None:
                t = tile_override[tr, tc]
                a = attrs[tr, tc]
            else:
                t = tiles[tr, tc]
                a = attrs[tr, tc]
            addr = int(bg_page) * 0x1000 + int(t) * 16
            pix = S.tile_pixels(chr_win.read(addr, 16), 0)
            pal = palette[a * 4:a * 4 + 4]
            block = np.zeros((8, 8, 4), np.uint8)
            for i in range(4):
                m = pix == i
                c = S.color(pal[i])
                block[m, 0], block[m, 1], block[m, 2] = c
                block[m, 3] = 255 if i else 0
            out[py:py + 8, px:px + 8] = block
    return out


def render_screen(rec, chr_win, nt=0, scroll_x=None, scroll_y=None):
    """Render one full screen (background + sprites) from a trace record."""
    v = None
    # recorded v register: pad[0..1] little endian (set by the capture tool)
    if hasattr(rec, "vram_addr") and rec.vram_addr:
        v = rec.vram_addr
    if v:
        nt = (v >> 10) & 3
        sy = ((v >> 5) & 0x1F) * 8 + ((v >> 12) & 7)
        sx = (v & 0x1F) * 8 + (getattr(rec, "fine_x", 0) or 0)
    else:
        sx = scroll_x or 0
        sy = scroll_y or 0
    if scroll_x is not None:
        sx = scroll_x
    if scroll_y is not None:
        sy = scroll_y
    bg = render_bg(rec.vram, rec.palette, chr_win, nt,
                   rec.bg_page, mirror="vertical", scroll_x=sx, scroll_y=sy)
    sprite = S.oam_composite(rec, chr_win)
    alpha = sprite[:, :, 3] > 0
    for c in range(3):
        np.copyto(bg[:, :, c], sprite[:, :, c], where=alpha)
    np.copyto(bg[:, :, 3], sprite[:, :, 3], where=alpha)
    return bg


def metatile_map(vram, palette, chr_win, nt=0, bg_page=0, scale=2):
    """Build a 16x16 metatile tileset + map for GameMaker import.

    Returns (tileset RGBA array, map 15x16 uint16 array of tile indices,
             list of (palette_index, tile_ids) per metatile).
    """
    tiles, attrs = name_table(vram, nt)
    quads = {}
    order = []
    m = np.zeros((15, 16), np.uint16)
    for qy in range(15):
        for qx in range(16):
            ids = []
            for dy in range(2):
                for dx in range(2):
                    ids.append(int(tiles[qy * 2 + dy, qx * 2 + dx]))
            pal = int(attrs[qy * 2, qx * 2])
            key = (pal, tuple(ids))
            if key not in quads:
                quads[key] = len(order)
                order.append(key)
            m[qy, qx] = quads[key]
    cols = 16
    rows = (len(order) + cols - 1) // cols
    sheet = np.zeros((rows * 16, cols * 16, 4), np.uint8)
    for i, (pal_idx, ids) in enumerate(order):
        ox, oy = (i % cols) * 16, (i // cols) * 16
        for k, tid in enumerate(ids):
            dx, dy = (k % 2) * 8, (k // 2) * 8
            pix = S.tile_pixels(chr_win.read(int(bg_page) * 0x1000 + int(tid) * 16, 16), 0)
            p = palette[pal_idx * 4:pal_idx * 4 + 4]
            blk = np.zeros((8, 8, 4), np.uint8)
            for c in range(4):
                mm = pix == c
                col = S.color(p[c])
                blk[mm, 0], blk[mm, 1], blk[mm, 2] = col
                blk[mm, 3] = 255
            sheet[oy + dy:oy + dy + 8, ox + dx:ox + dx + 8] = blk
    return sheet, m, order


# ---------------------------------------------------------------------------
# Full scroll canvas
#
# Vertical mirroring gives two distinct name tables (0 + 1).  The NES can
# scroll vertically by up to 240 px, so the complete reachable background is
# 512 x 480 px = four name tables:  NT0 NT1
#                                   NT2 NT3
# with NT2 mirroring NT0 and NT3 mirroring NT1.  The canvas is laid out
# exactly like that, so any screen is a 256x240 crop at (dy, dx).
# ---------------------------------------------------------------------------

def canvas_tiles(vram, mirror="vertical"):
    """Tile indices + attribute palette index for the 64x60 tile canvas."""
    tiles = np.zeros((60, 64), np.uint8)
    attrs = np.zeros((60, 64), np.uint8)
    for cy in range(2):
        for cx in range(2):
            nt = cy * 2 + cx
            t, a = name_table(vram, nt, mirror)
            tiles[cy * 30:cy * 30 + 30, cx * 32:cx * 32 + 32] = t
            attrs[cy * 30:cy * 30 + 30, cx * 32:cx * 32 + 32] = a
    return tiles, attrs


def render_canvas(vram, palette, chr_win, bg_page=0, mirror="vertical"):
    """Render the whole 512x480 scroll canvas (RGBA)."""
    tiles, attrs = canvas_tiles(vram, mirror)
    out = np.zeros((480, 512, 4), np.uint8)
    for ry in range(60):
        for cx in range(64):
            t = int(tiles[ry, cx])
            a = int(attrs[ry, cx])
            addr = int(bg_page) * 0x1000 + t * 16
            pix = S.tile_pixels(chr_win.read(addr, 16), 0)
            pal = palette[a * 4:a * 4 + 4]
            blk = np.zeros((8, 8, 4), np.uint8)
            for i in range(4):
                m = pix == i
                c = S.color(pal[i])
                blk[m, 0], blk[m, 1], blk[m, 2] = c
                blk[m, 3] = 255
            out[ry * 8:ry * 8 + 8, cx * 8:cx * 8 + 8] = blk
    return out


def find_offset(canvas, frame, step=4, colors=(0,)):
    """Locate ``frame`` inside ``canvas``; returns (dy, dx, score).

    Only tiles are compared, so this is a plain 2-D search on a coarse grid
    followed by a pixel-exact refinement.  ``colors`` selects which of the
    frame's RGB channels to use (blue separates the layers best here).
    """
    ch = colors[0]
    H, W = canvas.shape[:2]
    h, w = frame.shape[:2]
    coarse = canvas[::step, ::step, ch].astype(np.int16)
    target = frame[::step, ::step, ch].astype(np.int16)
    th, tw = target.shape
    best = (1e18, 0, 0)
    for dy in range(0, (H - h) // step + 1):
        for dx in range(0, (W - w) // step + 1):
            sub = coarse[dy:dy + th, dx:dx + tw]
            if sub.shape != target.shape:
                continue
            s = int(np.abs(sub - target).sum())
            if s < best[0]:
                best = (s, dy * step, dx * step)
    # refine by 1 px on a small window
    _, by, bx = best
    best = (1e18, by, bx)
    for dy in range(max(0, by - step), min(H - h, by + step) + 1):
        for dx in range(max(0, bx - step), min(W - w, bx + step) + 1):
            sub = canvas[dy:dy + h, dx:dx + w, ch].astype(np.int16)
            s = int(np.abs(sub - frame[:, :, ch].astype(np.int16)).sum())
            if s < best[0]:
                best = (s, dy, dx)
    return best[1], best[2], best[0]
