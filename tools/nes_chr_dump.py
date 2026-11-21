#!/usr/bin/env python3
"""
nes_chr_dump.py - lossless CHR extractor for iNES NES ROMs.

Reads an .nes file, parses the iNES header (including MMC1/mapper 1),
decodes every 8x8 2bpp tile in CHR ROM and writes one indexed-color PNG
sheet per 8KB CHR bank (16 tiles per row).

CHR data is luminance-indexed (4 entries per tile via 2 bitplanes), so the
PNG output is palette-agnostic. Actual colours come from the console's
palette RAM ($3F00-$3F1F) at run time - grab those with the FCEUX Lua
helper in this folder (fceux_palette_dump.lua), or from the PPU viewer.

Usage:
    python3 nes_chr_dump.py rom.nes --out extracted/
    python3 nes_chr_dump.py rom.nes --info          # header stats only

This is general-purpose NES tooling (works on any iNES ROM), analogous to
FCEUX itself. Outputs land in whatever directory YOU choose; do what you
like with them on your own machine and your own copy of the ROM.
Requires: python3 + Pillow  (pip install pillow)
"""

import argparse
import json
import struct
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install pillow")

TILE = 8
TILES_PER_ROW = 16
BANK_BYTES = 8 * 1024  # one CHR bank = 1024 tiles


def parse_ines(data: bytes) -> dict:
    if len(data) < 16 or data[:4] != b"NES\x1a":
        sys.exit("not an iNES ROM (bad magic)")
    prg_banks_16k = data[4]
    chr_banks_8k = data[5]
    flags6 = data[6]
    flags7 = data[7]
    trainer = bool(flags6 & 0x04)
    mapper = (flags6 >> 4) | (flags7 & 0xF0)
    vs = bool(flags6 & 0x01)
    offset = 16 + (512 if trainer else 0)
    prg_start = offset
    chr_start = prg_start + prg_banks_16k * 16384
    chr_end = chr_start + chr_banks_8k * BANK_BYTES
    return {
        "mapper": mapper,
        "prg_banks_16k": prg_banks_16k,
        "chr_banks_8k": chr_banks_8k,
        "trainer": trainer,
        "mirroring": "vertical" if vs else "horizontal",
        "chr_start": chr_start,
        "chr_end": chr_end,
        "file_size": len(data),
        "ines_2": (flags7 & 0x0C) == 0x08,
    }


def decode_tile(tile: bytes) -> list[list[int]]:
    """Decode a 16-byte 2bpp tile into an 8x8 list of palette indices (0-3)."""
    assert len(tile) == 16
    rows = []
    for y in range(TILE):
        lo, hi = tile[y], tile[y + 8]
        row = []
        for x in range(TILE):
            bit = 7 - x
            row.append(((lo >> bit) & 1) | (((hi >> bit) & 1) << 1))
        rows.append(row)
    return rows


def dump_bank(bank: bytes, bank_index: int, out_dir: Path) -> dict:
    n_tiles = len(bank) // 16
    cols = TILES_PER_ROW
    rows = (n_tiles + cols - 1) // cols
    img = Image.new("P", (cols * TILE, rows * TILE))
    # grayscale ramp, indices 0-3 (index-transparent where unused)
    ramp = [0, 0, 0, 85, 85, 85, 170, 170, 170, 255, 255, 255]
    img.putpalette((ramp + [0, 0, 0] * 256)[:768])
    px = img.load()
    for t in range(n_tiles):
        tile = bank[t * 16:(t + 1) * 16]
        rows_px = decode_tile(tile)
        tx, ty = (t % cols) * TILE, (t // cols) * TILE
        for y in range(TILE):
            for x in range(TILE):
                px[tx + x, ty + y] = rows_px[y][x]
    path = out_dir / f"chr_bank_{bank_index:02d}.png"
    img.save(path)
    return {"bank": bank_index, "tiles": n_tiles, "file": path.name}


def main() -> None:
    ap = argparse.ArgumentParser(description="Lossless NES CHR (tile) extractor")
    ap.add_argument("rom", help="path to .nes file")
    ap.add_argument("--out", default="extracted", help="output directory (default: extracted/)")
    ap.add_argument("--info", action="store_true", help="print header stats only, write nothing")
    args = ap.parse_args()

    data = Path(args.rom).read_bytes()
    info = parse_ines(data)
    print(json.dumps({k: v for k, v in info.items()}, indent=2))
    if args.info:
        return

    chr_data = data[info["chr_start"]:info["chr_end"]]
    if len(chr_data) < info["chr_banks_8k"] * BANK_BYTES:
        sys.exit("CHR data truncated (bad header or truncated dump)")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = [dump_bank(chr_data[b * BANK_BYTES:(b + 1) * BANK_BYTES], b, out_dir)
                for b in range(info["chr_banks_8k"])]
    with open(out_dir / "manifest.json", "w") as f:
        json.dump({"rom": str(args.rom), "mapper": info["mapper"], "banks": manifest}, f, indent=2)
    print(f"wrote {len(manifest)} bank sheets + manifest.json -> {out_dir}/")


if __name__ == "__main__":
    main()
