#!/usr/bin/env python3
"""
Extract CHR ROM pattern data from Chip 'n Dale Rescue Rangers 2 (USA).

Renders NES 2bpp planar tiles to PNG sheets:

  extracted/tiles/chr_4k_bank_XX.png   256 tiles, 16x16 tiles (128x128 px)
  extracted/tiles/chr_8k_bank_XX.png   1024 tiles, 16x64 tiles (128x512 px)

Pixel values 0-3 are mapped to grayscale 0/85/170/255 so the sheets preserve
the exact tile index data and can be recoloured later with real palettes.
A CSV index with per-bank hashes is written alongside the PNGs.
"""

import argparse
import csv
import hashlib
import os

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Pillow is required: pip install pillow")

GRAY = [0, 85, 170, 255]


def tile_pixels(chr_data, tile_index):
    """Return 64 pixel values (0-3) for one 16-byte NES tile."""
    base = tile_index * 16
    out = []
    for y in range(8):
        plane0 = chr_data[base + y]
        plane1 = chr_data[base + 8 + y]
        for x in range(8):
            bit = 7 - x
            out.append((((plane1 >> bit) & 1) << 1) | ((plane0 >> bit) & 1))
    return out


def render_bank(chr_data, first_tile, tile_count, tiles_wide):
    tiles_high = tile_count // tiles_wide
    img = Image.new("L", (tiles_wide * 8, tiles_high * 8), 0)
    px = img.load()
    for t in range(tile_count):
        tx = (t % tiles_wide) * 8
        ty = (t // tiles_wide) * 8
        pix = tile_pixels(chr_data, first_tile + t)
        for i, v in enumerate(pix):
            px[tx + (i % 8), ty + (i // 8)] = GRAY[v]
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", default="Chip 'n Dale - Rescue Rangers 2 (USA).nes")
    ap.add_argument("--out", default="extracted/tiles")
    args = ap.parse_args()

    with open(args.rom, "rb") as f:
        data = f.read()
    if data[:4] != b"NES\x1a":
        raise SystemExit("Not an iNES ROM")
    prg_size = data[4] * 0x4000
    chr_size = data[5] * 0x2000
    chr_data = data[16 + prg_size:16 + prg_size + chr_size]
    if len(chr_data) != chr_size:
        raise SystemExit("CHR data truncated")

    os.makedirs(args.out, exist_ok=True)
    rows = []

    # MMC1 switches CHR in 4 KB banks (256 tiles). Render those, plus the
    # iNES-native 8 KB units (512 tiles) for pattern-table overview.
    for bank in range(chr_size // 0x1000):
        chunk = chr_data[bank * 0x1000:(bank + 1) * 0x1000]
        name = "chr_4k_bank_%02d.png" % bank
        render_bank(chr_data, bank * 256, 256, 16).save(os.path.join(args.out, name))
        rows.append(["4k", bank, "0x%05X" % (bank * 0x1000), 256, name,
                     hashlib.sha1(chunk).hexdigest()])

    for bank in range(chr_size // 0x2000):
        chunk = chr_data[bank * 0x2000:(bank + 1) * 0x2000]
        name = "chr_8k_bank_%02d.png" % bank
        render_bank(chr_data, bank * 512, 512, 16).save(os.path.join(args.out, name))
        rows.append(["8k", bank, "0x%05X" % (bank * 0x2000), 512, name,
                     hashlib.sha1(chunk).hexdigest()])

    with open(os.path.join(args.out, "index.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["unit", "bank", "chr_file_offset", "tiles", "file", "sha1"])
        w.writerows(rows)

    print("Wrote %d sheets to %s" % (len(rows), args.out))


if __name__ == "__main__":
    main()
