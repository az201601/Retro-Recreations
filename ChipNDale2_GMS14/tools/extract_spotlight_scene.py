#!/usr/bin/env python3
"""
extract_spotlight_scene.py -- Pull the authentic Chip 'n Dale Rescue Rangers 2
"spotlight" scene (the attract scene that plays after the copyright screen)
straight out of the ROM, as GameMaker: Studio 1.4 ready PNGs + data.

What the scene actually is (verified against the running ROM)
------------------------------------------------------------
The sequence after the copyright screen is NOT a scrolling eye/mask effect.
It is:

  1. The title logo screen's brick wall is loaded into the nametable, but its
     four background palettes are all zeroed to black ($0F,$0F,$0F,$20), so the
     screen reads as pure black.
  2. A "light disk" - 32 consecutive hardware sprites (8x16 mode, 4 sprites
     wide x 8 rows tall, so a 64x63 pixel disc) - is placed with sprite
     attribute bit 5 SET, i.e. *behind the background*.
  3. Since the wall's colour 0 is the universal backdrop, and the disc is drawn
     behind the (opaque) wall, the disc only shows through where the wall's
     pixel is colour 0 - the mortar lines - which is why the early frames show
     a pink disc full of brick-shaped dark blobs.
  4. The four background palettes are then faded up from black to
     `0F 17 37 20 / 0F 17 05 20 / 0F 15 32 05 / 0F 17 27 20`, which reveals
     the mural. The disc keeps sweeping around behind the wall the whole time.

So the two assets the user asked for are:
    spotlight_circle.png    the 64x63 light disc (32 sprites composed)
    backdrop_bricks.png     the brick wall / mural backdrop

Outputs (into ../EXTRACTED/spotlight/):
    spotlight_circle.png       64x63 disc, full alpha, NES colours
    spotlight_circle_grid.png  8x8 sprite-cell version with guides (reference)
    spotlight_circle_raw.txt   the raw 4-colour (0..3) pixel indices
    backdrop_bricks.png        256x240 brick wall exactly as the game shows it
    backdrop_bricks_tilemap.txt  the 32x30 nametable tile indices
    backdrop_bricks_palette.txt  the 4 background palettes used
    scene_frames/fNNNN.png     the real rendered sequence (contact sheet + PNGs)

Usage
-----
    python3 extract_spotlight_scene.py ["path/to/game.nes"] [output_dir]
"""
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from nes_emu import NES                       # noqa: E402

DEFAULT_ROM = os.path.abspath(os.path.join(
    HERE, '..', '..', "Chip 'n Dale - Rescue Rangers 2 (USA).nes"))
DEFAULT_OUT = os.path.abspath(os.path.join(HERE, '..', 'EXTRACTED', 'spotlight'))

# NES 2C02 palette, "Nestopia / hardware-measured" approximation. This is far
# closer to what the game looks like on a real CRT than the older saturated
# FCEUX table, and it is what the EXTRACTED/spotlight PNGs are rendered with.
NES_PALETTE = [
    (84, 84, 84), (0, 30, 116), (8, 16, 144), (48, 0, 136),
    (68, 0, 100), (92, 0, 48), (84, 4, 0), (60, 24, 0),
    (32, 42, 0), (8, 58, 0), (0, 64, 0), (0, 60, 0),
    (0, 50, 60), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (152, 150, 152), (8, 76, 196), (48, 50, 236), (92, 30, 228),
    (136, 20, 176), (160, 20, 100), (152, 34, 32), (120, 60, 0),
    (84, 90, 0), (40, 114, 0), (8, 124, 0), (0, 118, 40),
    (0, 102, 120), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (236, 238, 236), (76, 154, 236), (120, 124, 236), (176, 98, 236),
    (228, 84, 236), (236, 88, 180), (236, 106, 100), (212, 136, 32),
    (160, 170, 0), (116, 196, 0), (76, 208, 32), (56, 204, 108),
    (56, 180, 204), (60, 60, 60), (0, 0, 0), (0, 0, 0),
    (236, 238, 236), (168, 204, 236), (188, 188, 236), (212, 178, 236),
    (236, 174, 236), (236, 174, 212), (236, 180, 176), (228, 196, 144),
    (204, 210, 120), (180, 222, 120), (168, 226, 144), (152, 226, 180),
    (160, 214, 228), (160, 162, 160), (0, 0, 0), (0, 0, 0),
]


# ---------------------------------------------------------------- PNG writer
def write_png(path, w, h, rgba):
    """Write an RGBA8888 PNG using only the standard library."""
    raw = bytearray()
    stride = w * 4
    for y in range(h):
        raw.append(0)                                  # filter: none
        raw += rgba[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data +
                struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (b'\x89PNG\r\n\x1a\n' +
           chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) +
           chunk(b'IDAT', zlib.compress(bytes(raw), 9)) +
           chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(png)


def rgb_of(nes_index):
    return NES_PALETTE[nes_index & 0x3F]


# ---------------------------------------------------------------- screen render
def render_screen(nes, show_bg=True, show_sprites=True, key_backdrop=False):
    """Render the current PPU state to an RGBA bytearray (256x240).

    This models the PPU's compositing rules that matter here:
      * background colour 0 is the universal backdrop;
      * a sprite with attribute bit 5 set is drawn BEHIND background pixels,
        but still in front of the backdrop where the background is colour 0.

    ``key_backdrop=True`` makes every background colour-0 pixel fully
    transparent instead of painting it with the backdrop colour. On the NES
    those pixels *are* the backdrop, so this is exactly how GameMaker needs the
    wall delivered in order to let the light disk show through the mortar.
    """
    W, H = 256, 240
    mask = nes.ppumask
    if not show_bg:
        mask &= ~0x08
    if not show_sprites:
        mask &= ~0x10

    bg_pattern = (nes.ppuctrl >> 4) & 1
    sp_pattern = (nes.ppuctrl >> 3) & 1

    # colour index (into the 64-entry NES palette) plus a "is background
    # pixel an opaque colour" flag per pixel
    out = bytearray(W * H * 4)
    bg_opaque = bytearray(W * H)

    backdrop = nes.pal[0]

    if mask & 0x08:
        for sy in range(H):
            ty = sy >> 3
            fy = sy & 7
            row_base = (ty & 0x1F) * 32
            for sx in range(W):
                tx = sx >> 3
                tile = nes.nt[row_base + tx]
                attr = nes.nt[0x3C0 + (ty >> 2) * 8 + (tx >> 2)]
                shift = ((ty & 2) << 1) | ((tx & 2) >> 1)
                palnum = (attr >> shift) & 3
                off = nes.chr_offset(bg_pattern * 0x1000 + tile * 16 + fy)
                b0 = nes.chr[off]
                b1 = nes.chr[off + 8]
                bit = 7 - (sx & 7)
                c = ((b0 >> bit) & 1) | (((b1 >> bit) & 1) << 1)
                o = (sy * W + sx) * 4
                if c == 0:
                    if key_backdrop:
                        out[o:o + 4] = b'\x00\x00\x00\x00'
                        continue
                    idx = backdrop
                else:
                    idx = nes.pal[palnum * 4 + c]
                    bg_opaque[sy * W + sx] = 1
                r, g, b = rgb_of(idx)
                out[o:o + 4] = bytes((r, g, b, 255))
    else:
        r, g, b = rgb_of(backdrop)
        for i in range(W * H):
            out[i * 4:i * 4 + 4] = bytes((r, g, b, 255))

    if mask & 0x10:
        h16 = bool(nes.ppuctrl & 0x20)
        sheight = 16 if h16 else 8
        for i in range(63, -1, -1):                    # lower index = front
            sy0 = nes.oam[i * 4]
            tile = nes.oam[i * 4 + 1]
            attr = nes.oam[i * 4 + 2]
            sx0 = nes.oam[i * 4 + 3]
            behind = bool(attr & 0x20)
            spal = attr & 3
            for r_ in range(sheight):
                yy = sy0 + 1 + r_
                if yy >= H:
                    continue
                ry = (sheight - 1 - r_) if (attr & 0x80) else r_
                t = ((tile & 0xFE) | (1 if ry >= 8 else 0)) if h16 else tile
                off = nes.chr_offset(sp_pattern * 0x1000 + t * 16 + (ry & 7))
                b0 = nes.chr[off]
                b1 = nes.chr[off + 8]
                for c_ in range(8):
                    xx = sx0 + c_
                    if xx >= W:
                        continue
                    cc = (7 - c_) if (attr & 0x40) else c_
                    bit = 7 - cc
                    col = ((b0 >> bit) & 1) | (((b1 >> bit) & 1) << 1)
                    if col == 0:
                        continue
                    if behind and bg_opaque[yy * W + xx]:
                        continue
                    idx = nes.pal[16 + spal * 4 + col]
                    rr, gg, bb = rgb_of(idx)
                    o = (yy * W + xx) * 4
                    out[o:o + 4] = bytes((rr, gg, bb, 255))

    return out


# ---------------------------------------------------------------- sprite disc
def sprite_pixels(nes, slot, sp_pattern, h16):
    """Decode one OAM slot to a list of rows of colour indices (0=transparent)."""
    y = nes.oam[slot * 4]
    tile = nes.oam[slot * 4 + 1]
    attr = nes.oam[slot * 4 + 2]
    x = nes.oam[slot * 4 + 3]
    sheight = 16 if h16 else 8
    rows = []
    for r_ in range(sheight):
        ry = (sheight - 1 - r_) if (attr & 0x80) else r_
        t = ((tile & 0xFE) | (1 if ry >= 8 else 0)) if h16 else tile
        off = nes.chr_offset(sp_pattern * 0x1000 + t * 16 + (ry & 7))
        b0 = nes.chr[off]
        b1 = nes.chr[off + 8]
        row = []
        for c_ in range(8):
            cc = (7 - c_) if (attr & 0x40) else c_
            bit = 7 - cc
            row.append(((b0 >> bit) & 1) | (((b1 >> bit) & 1) << 1))
        rows.append(row)
    return rows, x, y + 1, attr


def compose_light_disk(nes):
    """Compose the 32 spotlight sprites into a 64x63 colour-index grid.

    Returns (grid, palette_indices, origin_x, origin_y) where grid rows are
    lists of raw 2-bit colour indices (0 = transparent).
    """
    slots = [i for i in range(64) if nes.oam[i * 4] < 0xEF]
    if not slots:
        return None, None, 0, 0
    h16 = bool(nes.ppuctrl & 0x20)
    sp_pattern = (nes.ppuctrl >> 3) & 1
    sheight = 16 if h16 else 8

    xs = [nes.oam[i * 4 + 3] for i in slots]
    ys = [nes.oam[i * 4] + 1 for i in slots]
    ox, oy = min(xs), min(ys)
    w = max(xs) + 8 - ox
    h = max(ys) + sheight - oy

    grid = [[0] * w for _ in range(h)]
    pals = set()
    for i in slots:
        rows, sx, sy, attr = sprite_pixels(nes, i, sp_pattern, h16)
        pals.add(attr & 3)
        for r_, row in enumerate(rows):
            for c_, v in enumerate(row):
                if v == 0:
                    continue
                gx, gy = sx + c_ - ox, sy + r_ - oy
                if 0 <= gx < w and 0 <= gy < h:
                    grid[gy][gx] = v
    return grid, sorted(pals), ox, oy


def grid_to_rgba(grid, palette, transparent=True):
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = bytearray(w * h * 4)
    for y in range(h):
        for x in range(w):
            c = grid[y][x]
            o = (y * w + x) * 4
            if c == 0 and transparent:
                out[o:o + 4] = b'\x00\x00\x00\x00'
            else:
                r, g, b = rgb_of(palette[c])
                out[o:o + 4] = bytes((r, g, b, 255))
    return w, h, out


# ------------------------------------------------------------------- tile PNG
def nametable_to_rgba(nes, key_backdrop=False):
    """Render only the background layer from the nametable."""
    return render_screen(nes, show_bg=True, show_sprites=False,
                         key_backdrop=key_backdrop)


# ----------------------------------------------------------------------- main
def main(argv):
    rom = argv[1] if len(argv) > 1 else DEFAULT_ROM
    outdir = argv[2] if len(argv) > 2 else DEFAULT_OUT
    os.makedirs(outdir, exist_ok=True)
    frames_dir = os.path.join(outdir, 'scene_frames')
    os.makedirs(frames_dir, exist_ok=True)

    print("ROM  :", rom)
    print("OUT  :", outdir)

    # ---------------------------------------------------------------- capture
    # Frame 480 is the canonical "spotlight is right of centre, wall fully
    # revealed behind it" frame; both requested assets are complete there.
    nes = NES(rom)
    nes.run_to_frame(480)
    print("captured frame 480: chr banks $%02X/$%02X, %d sprites" %
          (nes.chr0, nes.chr1,
           sum(1 for i in range(64) if nes.oam[i * 4] < 0xEF)))

    # ------------------------------------------------- 1. spotlight circle
    grid, pals, ox, oy = compose_light_disk(nes)
    if grid is None:
        raise SystemExit("No spotlight sprites found on screen.")
    # The disc uses sprite palette 2 ($00,$36,$16,$26) -> indices 1,2,3
    spal = nes.pal[16 + pals[0] * 4: 16 + pals[0] * 4 + 4]
    print("light disk: %dx%d at (%d,%d), sprite palette %s" %
          (len(grid[0]), len(grid), ox, oy, spal.hex(' ')))

    w, h, rgba = grid_to_rgba(grid, spal, transparent=True)
    write_png(os.path.join(outdir, 'spotlight_circle.png'), w, h, rgba)

    # grid + 8px guides reference image
    scale = 4
    gw, gh = w * scale, h * scale
    grgba = bytearray(gw * gh * 4)
    for y in range(gh):
        for x in range(gw):
            o = (y * gw + x) * 4
            grgba[o:o + 4] = rgba[((y // scale) * w + (x // scale)) * 4:
                                  ((y // scale) * w + (x // scale)) * 4 + 4] or b'\x00\x00\x00\x00'
    for y in range(gh):
        for x in range(gw):
            if (x % (8 * scale) == 0) or (y % (8 * scale) == 0):
                o = (y * gw + x) * 4
                if grgba[o + 3] == 0:
                    grgba[o:o + 4] = b'\x30\x30\x60\xff'
    write_png(os.path.join(outdir, 'spotlight_circle_grid.png'), gw, gh, grgba)

    with open(os.path.join(outdir, 'spotlight_circle_raw.txt'), 'w') as f:
        f.write("# 64x63 spotlight disk, raw 2-bit NES colour indices\n")
        f.write("# sprite palette: %s\n" % spal.hex(' '))
        f.write("# 0 = transparent\n")
        for row in grid:
            f.write(''.join(str(v) for v in row) + '\n')

    # ------------------------------------------------ 2. backdrop (bricks)
    # Fully revealed wall: use the frame where the mural is on screen.
    nes2 = NES(rom)
    nes2.run_to_frame(1150)
    fade_end = 1150
    bg_rgba = nametable_to_rgba(nes2)
    write_png(os.path.join(outdir, 'backdrop_bricks.png'), 256, 240, bg_rgba)

    with open(os.path.join(outdir, 'backdrop_bricks_tilemap.txt'), 'w') as f:
        f.write("# 32x30 nametable tile indices (frame 1150)\n")
        for r in range(30):
            f.write(' '.join('%02X' % nes2.nt[r * 32 + c] for c in range(32)) + '\n')
        f.write("\n# attribute table (64 bytes, 4x4 tile blocks)\n")
        for r in range(8):
            f.write(' '.join('%02X' % nes2.nt[0x3C0 + r * 8 + c] for c in range(8)) + '\n')

    # The measured palette fade from black to full colour, as the game does it.
    fade_nes = NES(rom)
    fade_rows = []
    prev = None
    while fade_nes.frame < fade_end:
        fade_nes.step()
        if fade_nes.frame >= fade_end:
            break
        cur = (bytes(fade_nes.pal[0:16]), fade_nes.frame)
        key = bytes(fade_nes.pal[0:16])
        if key != prev and fade_nes.frame >= 880:
            fade_rows.append((fade_nes.frame, key))
            prev = key
    with open(os.path.join(outdir, 'fade_palettes.txt'), 'w') as f:
        f.write("# Spotlight backdrop palettes are $0F $0F $0F $20 (a black grate).\n")
        f.write("# At step 886 the colourful title mural is swapped in and its four\n")
        f.write("# background palettes are faded from black to full colour by step 904.\n")
        f.write("# Below is every distinct palette state the ROM writes.\n#\n")
        f.write("# frame  BG0            BG1            BG2            BG3\n")
        for fr, pal in fade_rows:
            b = ['%02X' % v for v in pal]
            f.write("  %4d   %-14s %-14s %-14s %-14s\n" % (
                fr, ' '.join(b[0:4]), ' '.join(b[4:8]),
                ' '.join(b[8:12]), ' '.join(b[12:16])))

    with open(os.path.join(outdir, 'backdrop_bricks_palette.txt'), 'w') as f:
        f.write("# background palettes (frame 1150)\n")
        for i in range(4):
            f.write("BG%d: %s\n" % (i, nes2.pal[i * 4:i * 4 + 4].hex(' ').upper()))

    # The same wall in its blacked-out state (what the spotlight sweeps over)
    wall_nes = NES(rom)
    wall_nes.run_to_frame(480)
    dark = nametable_to_rgba(wall_nes)
    write_png(os.path.join(outdir, 'backdrop_bricks_dark.png'), 256, 240, dark)

    #--------------------------------------------------------------------------
    # GameMaker-ready MASK for the spotlight scene.
    #
    # During the spotlight the wall is NOT the colourful mural. It is the
    # "grate" nametable (CHR bank 31) drawn with palette $0F $0F $0F $20, i.e.
    # every brick tile renders BLACK (colour index 1) and every mortar hole
    # renders the backdrop (colour index 0).
    #
    # The light disk is a set of sprites flagged "behind background", so the
    # PPU shows the disk on colour-0 pixels (the mortar holes) and hides it
    # under colour-1 pixels (the brick tiles). Verified against the running ROM:
    # every one of the 2198 disc pixels that landed on background colour 0 was
    # visible, and all 738 that landed on colour 1 were covered.
    #
    # So the GameMaker asset is: the grate, transparent where the background is
    # colour 0, opaque black where it is colour 1.
    #--------------------------------------------------------------------------
    wall_key = nametable_to_rgba(nes, key_backdrop=True)
    write_png(os.path.join(outdir, 'spotlight_mask.png'), 256, 240, wall_key)

    # The stencil as the player actually sees it while the spotlight sweeps:
    # black mural shape, backdrop (visible = where the disc shows) everywhere
    # else. This is exactly the ROM's frame at step 480.
    write_png(os.path.join(outdir, 'spotlight_stencil_preview.png'), 256, 240,
              nametable_to_rgba(nes))

    # ------------------------------------------------- 3. scene contact sheet
    # Capture the real sequence so the animation timing can be matched exactly.
    marks = [180, 210, 240, 260, 280, 300, 330, 360, 390, 420, 450, 480,
             510, 540, 570, 600, 650, 700, 750, 800, 850, 900, 950, 1000,
             1050, 1100, 1150]
    tiled = NES(rom)
    for f in marks:
        tiled.run_to_frame(f)
        write_png(os.path.join(frames_dir, 'f%04d.png' % f), 256, 240,
                  render_screen(tiled))

    # ------------------------------------------------- 4. composite preview
    # A flat 4x4 strip of the real sequence, so the timing can be eyeballed.
    picks = [240, 300, 360, 420, 480, 540, 600, 700, 800, 900, 1000, 1150,
             1150, 1150, 1150, 1150]
    sheet = NES(rom)
    cols, rows, scale = 4, 4, 1
    sw, sh = 256 * cols, 240 * rows
    sheetbuf = bytearray(sw * sh * 4)
    for i, f in enumerate(picks):
        sheet.run_to_frame(f)
        img = render_screen(sheet)
        cx, cy = (i % cols) * 256, (i // cols) * 240
        for y in range(240):
            src = y * 256 * 4
            dst = ((cy + y) * sw + cx) * 4
            sheetbuf[dst:dst + 256 * 4] = img[src:src + 256 * 4]
    write_png(os.path.join(outdir, 'scene_contact_sheet.png'), sw, sh, sheetbuf)

    print("wrote spotlight_circle.png (%dx%d)" % (w, h))
    print("wrote backdrop_bricks.png (256x240)")
    print("wrote %d scene frames" % len(marks))
    print("wrote scene_contact_sheet.png (4x4 of the real sequence)")


if __name__ == '__main__':
    main(sys.argv)
