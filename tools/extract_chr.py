#!/usr/bin/env python3
"""
extract_chr.py -- extract all CHR-ROM tiles from the NES ROM to PNG sheets.

Chip 'n Dale RR2 (USA): mapper 1 (MMC1), 8 x 16KB PRG, 16 x 8KB CHR = 32 x 4KB
CHR banks, 256 tiles each. Tiles are 2bpp NES format; we export each bank as a
16x16 tile grid (128x128 px) plus a combined indexed sheet.

Output:
    assets/tiles/chr_bank_XX.png    4KB bank as tile grid (grayscale 0..3 -> 4 shades)
    assets/tiles/chr_all.png        all banks stacked
    assets/tiles/chr_meta.json      tile counts / offsets for tooling
"""
import json
import os
import sys

import numpy as np
from PIL import Image

ROM = "Chip 'n Dale - Rescue Rangers 2 (USA).nes"
OUT = "assets/tiles"

SHADES = np.array([[30, 30, 30], [96, 96, 96], [170, 170, 170], [240, 240, 240]], dtype=np.uint8)


def decode_tiles(data: bytes) -> np.ndarray:
    """(n, 8, 8) indices 0..3 from 16-byte-per-tile data."""
    arr = np.frombuffer(data, dtype=np.uint8).reshape(-1, 16)
    lo = arr[:, :8].astype(np.uint16)
    hi = arr[:, 8:].astype(np.uint16)
    bits = np.arange(7, -1, -1)
    return (((lo[:, :, None] >> bits) & 1) | (((hi[:, :, None] >> bits) & 1) << 1)).astype(np.uint8)


def tiles_to_sheet(tiles: np.ndarray, cols=16) -> Image.Image:
    n = tiles.shape[0]
    rows = (n + cols - 1) // cols
    sheet = np.zeros((rows * 8, cols * 8), dtype=np.uint8)
    for i in range(n):
        r, c = divmod(i, cols)
        sheet[r * 8:r * 8 + 8, c * 8:c * 8 + 8] = tiles[i]
    return Image.fromarray(SHADES[sheet], "RGB")


def main():
    os.makedirs(OUT, exist_ok=True)
    rom = open(ROM, "rb").read()
    chr_rom = rom[16 + 8 * 16384:]
    assert len(chr_rom) == 128 * 1024, len(chr_rom)
    banks = []
    for b in range(32):
        tiles = decode_tiles(chr_rom[b * 4096:(b + 1) * 4096])
        banks.append(tiles)
        img = tiles_to_sheet(tiles)
        img.save(f"{OUT}/chr_bank_{b:02d}.png")
    allt = np.concatenate(banks)
    tiles_to_sheet(allt, cols=16).save(f"{OUT}/chr_all.png")
    meta = {
        "rom": ROM,
        "chr_bytes": len(chr_rom),
        "banks_4kb": 32,
        "tiles_per_bank": 256,
        "total_tiles": 8192,
        "format": "NES 2bpp, 16 bytes/tile, bank_XX.png = 16x16 tiles",
    }
    with open(f"{OUT}/chr_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"wrote 32 bank sheets + chr_all.png ({allt.shape[0]} tiles) -> {OUT}/")


if __name__ == "__main__":
    main()
