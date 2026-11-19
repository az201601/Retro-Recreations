#!/usr/bin/env python3
"""
Extract state-1 (second screen) graphics from the ROM.

Outputs (extracted/screens/state1/):
  state1_bg.png     256x240 background rendered from the nametable the ROM
                    builds (fill + $B98B strip + $B9CD patch), CHR bank 31,
                    state-1 background palette.
  emblem.png        the 4-object mirrored metasprite composite (parent +
                      3 flip children) with the parent anchor marked in the
                      JSON (origin_x/origin_y = anchor pixel in the image).
  emblem_one.png    a single unflipped copy of metasprite set 0 frame 0.
  state1_data.json  palettes, metasprite records, trajectory phases.

Background stream format ($C46D): repeating blocks of
  [count_code, row_code, data...]
count_code: bits0-5 = bytes per row (0 means 64), bit6 = column mode,
bit7 = RLE (one byte repeated). row_code: bits0-5 = rows, bit7 = repeat-row
mode. Only the plain literal mode is supported here (asserted).
"""

import json
import os

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Pillow is required: pip install pillow")

OUT = "extracted/screens/state1"

# Standard NES palette (NESdev RGB approximation), index $00-$3F.
NES_RGB = [
    0x666666, 0x002A88, 0x1412A7, 0x3B00A4, 0x5C007E, 0x6E0040, 0x6C0600, 0x561D00,
    0x333500, 0x0B4800, 0x005200, 0x004F08, 0x00404D, 0x000000, 0x000000, 0x000000,
    0xADADAD, 0x155FD9, 0x4240FF, 0x7527FE, 0xA01ACC, 0xB71E7B, 0xB53120, 0x994E00,
    0x6B6D00, 0x388700, 0x0C9300, 0x008F32, 0x007C8D, 0x000000, 0x000000, 0x000000,
    0xFFFEFF, 0x64B0FF, 0x9290FF, 0xC676FF, 0xF36AFF, 0xFE6ECC, 0xFE8170, 0xEA9E22,
    0xBCBE00, 0x88D800, 0x5CE430, 0x45E082, 0x48CDDE, 0x4F4F4F, 0x000000, 0x000000,
    0xFFFEFF, 0xC0DFFF, 0xD3D2FF, 0xE8C8FF, 0xFBC2FF, 0xFEC4EA, 0xFECCC5, 0xF7D8A5,
    0xE4E594, 0xCFEF96, 0xBDF4AB, 0xB3F3CC, 0xB5EBF2, 0xB8B8B8, 0x000000, 0x000000,
]


def rgb(idx):
    v = NES_RGB[idx & 0x3F]
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255)


class Rom:
    def __init__(self, path):
        with open(path, "rb") as f:
            data = f.read()
        self.prg = data[16:16 + data[4] * 0x4000]
        self.chr = data[16 + data[4] * 0x4000:]

    def bank_byte(self, bank, cpu):
        return self.prg[bank * 0x4000 + (cpu - 0x8000)]

    def bank_bytes(self, bank, cpu, n):
        return bytes(self.bank_byte(bank, cpu + i) for i in range(n))

    def tile(self, chr_bank, index):
        """64 pixel values 0-3 for one 8x8 tile in a 4KB CHR bank."""
        base = chr_bank * 0x1000 + index * 16
        out = []
        for y in range(8):
            p0, p1 = self.chr[base + y], self.chr[base + 8 + y]
            for x in range(8):
                bit = 7 - x
                out.append((((p1 >> bit) & 1) << 1) | ((p0 >> bit) & 1))
        return out


def decode_c46d(stream):
    """Decode one $C46A stream -> list of (row_width, [rows]) blocks."""
    blocks = []
    i = 0
    while i < len(stream):
        b0, b1 = stream[i], stream[i + 1]
        i += 2
        count = (b0 & 0x3F) or 0x40
        rows = b1 & 0x3F
        assert not (b0 & 0xC0), "RLE/column mode not supported (b0=$%02X)" % b0
        assert not (b1 & 0x80), "repeat-row mode not supported (b1=$%02X)" % b1
        data = []
        for _ in range(rows):
            data.append(list(stream[i:i + count]))
            i += count
        blocks.append((count, data))
        if rows == 0 or i >= len(stream):
            break
    return blocks


def draw_tile(img, px, chr_bank, index, palette, dx, dy, flip_x=False, flip_y=False):
    pix = ROM.tile(chr_bank, index)
    for y in range(8):
        for x in range(8):
            v = pix[y * 8 + x]
            if v == 0:
                continue
            xx = dx + (7 - x if flip_x else x)
            yy = dy + (7 - y if flip_y else y)
            if 0 <= xx < img.width and 0 <= yy < img.height:
                px[xx, yy] = palette[v]


def draw_sprite_8x16(img, px, tile_byte, attr, obj_flags, dx, dy, spr_chr0, spr_chr1, spr_palettes):
    """One 8x16 sprite exactly as $F191 composes it (no strip advance)."""
    table_bank = spr_chr1 if (tile_byte & 1) else spr_chr0
    pair = tile_byte & 0xFE
    eff_attr = attr ^ obj_flags
    flip_x = bool(eff_attr & 0x40)
    flip_y = bool(eff_attr & 0x80)
    palette = [None] + [rgb(spr_palettes[(attr & 3) * 4 + i]) for i in (1, 2, 3)]
    # top tile first; flip_y swaps halves and mirrors rows (handled per tile)
    draw_tile(img, px, table_bank, pair + (1 if flip_y else 0), palette,
              dx, dy, flip_x, flip_y)
    draw_tile(img, px, table_bank, pair + (0 if flip_y else 1), palette,
              dx, dy + 8, flip_x, flip_y)


ROM = None


def main():
    global ROM
    ROM = Rom("Chip 'n Dale - Rescue Rangers 2 (USA).nes")
    os.makedirs(OUT, exist_ok=True)

    # --- palettes: state-1 config ptr1/ptr2 in bank 3 ($B081/$B091) ---
    bg_pal_idx = list(ROM.bank_bytes(3, 0xB081, 16))
    spr_pal_idx = list(ROM.bank_bytes(3, 0xB091, 16))

    # --- background nametable ($2000; $2400 gets the same strip) ---
    nametable = [0] * (32 * 30)
    strip = decode_c46d(ROM.bank_bytes(3, 0xB98B, 2 + 32 * 2))
    for width, rows in strip:
        for r, row in enumerate(rows):
            nametable[r * 32:r * 32 + width] = row
    patch = decode_c46d(ROM.bank_bytes(3, 0xB9CD, 2 + 12 * 8))
    patch_off = 0x144  # $2144
    for width, rows in patch:
        for r, row in enumerate(rows):
            start = patch_off + r * 32
            nametable[start:start + width] = row

    # Spotlight compositing: BG palette colour 1 is $0F (black), colour 0 is
    # transparent on the NES (backdrop/sprites show through). So the BG layer
    # is exported as black ink (pixel value >0) on transparency; in-game the
    # pale spotlight disc is drawn first and this overlay on top.
    bg_img = Image.new("RGBA", (256, 240), (0, 0, 0, 0))
    bpx = bg_img.load()
    for ty in range(30):
        for tx in range(32):
            pix = ROM.tile(31, nametable[ty * 32 + tx])
            for y in range(8):
                for x in range(8):
                    if pix[y * 8 + x] > 0:
                        bpx[tx * 8 + x, ty * 8 + y] = (0, 0, 0, 255)
    bg_img.save(os.path.join(OUT, "state1_bg.png"))

    # --- metasprite set 0 frame 0 (bank 5) ---
    def b5(cpu):
        return ROM.bank_byte(5, cpu)

    def b5_16(cpu):
        return b5(cpu) | (b5(cpu + 1) << 8)

    set0 = b5_16(0x8000)
    frame0 = b5_16(set0)
    spr_palettes = spr_pal_idx

    def s8(v):
        return v - 256 if v >= 128 else v

    def parse_frame(ptr):
        """$F191 frame format: a sequence of strips ended by a $00 byte.

        Strip: [count][dx][dy] then count x [tile, attr] (8x16 sprites).
        count bit 7 = vertical strip (advance Y), bits 0-6 = sprite count.
        After each strip the renderer loops back for another count byte;
        $00 ends the frame. (An earlier version of this extractor read
        only the first strip, which produced a wrong 64x32 sliver; the
        real frame has two strips and composes a 64x64 disc.)
        """
        strips = []
        sprites = []
        p = ptr
        while True:
            cnt = b5(p)
            p += 1
            if cnt == 0:
                break
            vertical = bool(cnt & 0x80)
            n = cnt & 0x7F
            sdx, sdy = s8(b5(p)), s8(b5(p + 1))
            p += 2
            strip = []
            for i in range(n):
                t, at = b5(p), b5(p + 1)
                p += 2
                x = sdx if vertical else sdx + i * 8
                y = sdy + i * 8 if vertical else sdy
                strip.append((x, y, t, at))
            strips.append({"count_byte": cnt, "dx": sdx, "dy": sdy,
                           "vertical": vertical,
                           "tiles": [s[2] for s in strip]})
            sprites.extend(strip)
        return strips, sprites

    strips, frame_sprites = parse_frame(frame0)

    def render_emblem(objects):
        """objects: list of $0344 flag bytes. Returns (image, origin).

        Mirroring matches $F191: flipX tile i sits at -(x)-8, flipY at
        -(y)-16 (8x16 cells), with the tile graphics flipped via the
        attribute XOR. The children's +$03BC follow offset ($F37C) and
        the renderer's -$03BC ($F191) cancel, so all four copies share
        the parent's origin.
        """
        placed = []  # (tile_byte, attr, obj_flags, x, y)
        for flags in objects:
            flip_x = bool(flags & 0x40)
            flip_y = bool(flags & 0x80)
            for (sx, sy, t, at) in frame_sprites:
                x = (-sx - 8) if flip_x else sx
                y = (-sy - 16) if flip_y else sy
                placed.append((t, at, flags, x, y))
        min_x = min(q[3] for q in placed)
        min_y = min(q[4] for q in placed)
        max_x = max(q[3] + 8 for q in placed)
        max_y = max(q[4] + 16 for q in placed)
        img = Image.new("RGBA", (max_x - min_x, max_y - min_y), (0, 0, 0, 0))
        px = img.load()
        # RGBA draw: reuse draw helpers with an RGBA-aware shim
        for (t, at, fl, x, y) in placed:
            _draw_sprite_rgba(img, px, t, at, fl, x - min_x, y - min_y,
                              spr_palettes)
        return img, (-min_x, -min_y), placed

    def _draw_sprite_rgba(img, px, tile_byte, attr, obj_flags, ddx, ddy, pals):
        table_bank = 29 if (tile_byte & 1) else 31
        pair = tile_byte & 0xFE
        eff = attr ^ obj_flags
        fx = bool(eff & 0x40)
        fy = bool(eff & 0x80)
        pal = [None] + [rgb(pals[(attr & 3) * 4 + i]) + (255,) for i in (1, 2, 3)]
        for half in range(2):
            tile_idx = pair + (half ^ (1 if fy else 0))
            pix = ROM.tile(table_bank, tile_idx)
            for yy in range(8):
                for xx in range(8):
                    v = pix[yy * 8 + xx]
                    if v == 0:
                        continue
                    X = ddx + (7 - xx if fx else xx)
                    Y = ddy + half * 8 + (7 - yy if fy else yy)
                    if 0 <= X < img.width and 0 <= Y < img.height:
                        px[X, Y] = pal[v]

    one, one_org, _ = render_emblem([0x20])
    one.save(os.path.join(OUT, "emblem_one.png"))
    # parent ($20) + children ($20|$40, $20|$80, $20|$C0)
    emblem, origin, placed = render_emblem([0x20, 0x60, 0xA0, 0xE0])
    emblem.save(os.path.join(OUT, "emblem.png"))

    # Composited preview: black backdrop, spotlight disc at its final
    # scripted position (70,104), silhouette overlay on top.
    preview = Image.new("RGBA", (256, 240), (0, 0, 0, 255))
    preview.alpha_composite(emblem, (70 - origin[0], 104 - origin[1]))
    preview.alpha_composite(bg_img)
    preview.convert("RGB").save(os.path.join(OUT, "preview_end.png"))

    data = {
        "bg_palette_indices": bg_pal_idx,
        "sprite_palette_indices": spr_pal_idx,
        "bg_palette_rgb": [rgb(i) for i in bg_pal_idx[:4]],
        "sprite_palettes_rgb": [[rgb(spr_pal_idx[g * 4 + i]) for i in range(4)]
                                for g in range(4)],
        "chr_banks": {"bg_pattern_table": 31, "sprite_pattern_table": 29,
                      "sprite_size": "8x16"},
        "metasprite": {"set": 0, "frame": 0,
                       "strips": strips,
                       "sprites_xy_tile_attr": [list(s) for s in frame_sprites],
                       "emblem_origin": origin,
                       "emblem_size": [emblem.width, emblem.height]},
        "trajectory": [
            {"frames": 128, "vx": 0.0, "vy": 2.0},
            {"frames": 96, "vx": -1.375, "vy": -1.375},
            {"frames": 64, "vx": 2.0, "vy": 0.0},
            {"frames": 48, "vx": -1.375, "vy": 1.375},
            {"frames": 128, "vx": -2.0, "vy": 0.0},
            {"frames": 134, "vx": 2.0, "vy": 0.0, "set_y": 104},
            {"frames": 16, "vx": -4.0, "vy": 0.0},
            {"frames": 60, "vx": 0.0, "vy": 0.0, "note": "WAIT"},
        ],
        "start_pos": [192, -64],
        "sounds": [{"at": "after phase 5 loops", "id": "0x74"},
                   {"at": "after phase 7", "id": "0x73"}],
    }
    with open(os.path.join(OUT, "state1_data.json"), "w") as f:
        json.dump(data, f, indent=1)
    print("wrote", OUT, "emblem origin", origin, "size",
          emblem.width, emblem.height)


if __name__ == "__main__":
    main()
