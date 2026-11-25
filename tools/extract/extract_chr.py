#!/usr/bin/env python3
"""Extract CHR banks from Chip 'n Dale Rescue Rangers 2 (USA) NES ROM.

Produces per-bank tilesheet PNGs (16x16 tiles, 128x128 px) and optional
per-tile exports. Uses a grayscale preview palette by default.
"""
from __future__ import annotations
import argparse, os
from PIL import Image

NES_HEADER = 16
PRG_BANK = 16384
CHR_BANK = 8192

# Default 2bpp grayscale preview
GRAY = [(0, 0, 0), (85, 85, 85), (170, 170, 170), (255, 255, 255)]


def load_rom(path: str):
    with open(path, "rb") as f:
        data = f.read()
    if data[:4] != b"NES\x1a":
        raise ValueError("Not an iNES ROM")
    prg_banks = data[4]
    chr_banks = data[5]
    chr_off = NES_HEADER + prg_banks * PRG_BANK
    chr = data[chr_off:chr_off + chr_banks * CHR_BANK]
    return data, prg_banks, chr_banks, chr


def decode_tile(chr: bytes, tile_index: int):
    base = tile_index * 16
    pixels = [[0] * 8 for _ in range(8)]
    for row in range(8):
        lo = chr[base + row]
        hi = chr[base + 8 + row]
        for col in range(8):
            bit = 7 - col
            pixels[row][col] = ((lo >> bit) & 1) | (((hi >> bit) & 1) << 1)
    return pixels


def bank_to_image(bank_data: bytes, palette=GRAY, scale=1):
    img = Image.new("RGBA", (128 * scale, 128 * scale), (0, 0, 0, 0))
    px = img.load()
    for t in range(256):
        tile = decode_tile(bank_data, t)
        tx, ty = (t % 16) * 8, (t // 16) * 8
        for row in range(8):
            for col in range(8):
                val = tile[row][col]
                # index 0 transparent for easy layering; preview as dark gray
                if val == 0:
                    color = (0, 0, 0, 0)
                else:
                    r, g, b = palette[val]
                    color = (r, g, b, 255)
                for sy in range(scale):
                    for sx in range(scale):
                        px[(tx + col) * scale + sx, (ty + row) * scale + sy] = color
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", default="Chip 'n Dale - Rescue Rangers 2 (USA).nes")
    ap.add_argument("--out", default="tools/out/chr")
    ap.add_argument("--scale", type=int, default=1)
    args = ap.parse_args()

    _, prg_banks, chr_banks, chr = load_rom(args.rom)
    os.makedirs(args.out, exist_ok=True)
    print(f"PRG banks: {prg_banks}, CHR banks: {chr_banks}")
    for b in range(chr_banks):
        bank_data = chr[b * CHR_BANK:(b + 1) * CHR_BANK]
        img = bank_to_image(bank_data, scale=args.scale)
        path = os.path.join(args.out, f"bank_{b:02d}.png")
        img.save(path)
        print("wrote", path)


if __name__ == "__main__":
    main()
