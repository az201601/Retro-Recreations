#!/usr/bin/env python3
"""Extract an iNES cartridge's CHR-ROM into an indexed tile atlas and raw bytes.

Usage: python3 tools/extract_nes_chr.py "Chip 'n Dale - Rescue Rangers 2 (USA).nes" [output-dir]
The atlas is a diagnostic 4-shade grayscale image; it is not palette-correct game art.
"""
from pathlib import Path
import json
import sys


def decode_tile(tile):
    pixels = []
    for y in range(8):
        lo, hi = tile[y], tile[y + 8]
        pixels.append([((lo >> (7 - x)) & 1) | (((hi >> (7 - x)) & 1) << 1) for x in range(8)])
    return pixels


def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    rom = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) == 3 else Path('assets/extracted_chr')
    data = rom.read_bytes()
    if len(data) < 16 or data[:4] != b'NES\x1a':
        raise SystemExit('Not a valid iNES/NES 2.0 file')
    h = data[:16]
    prg_size, chr_size = h[4] * 16384, h[5] * 8192
    trainer_size = 512 if h[6] & 4 else 0
    start = 16 + trainer_size + prg_size
    if not chr_size or start + chr_size > len(data):
        raise SystemExit('ROM has no complete CHR-ROM region (CHR may be RAM-backed)')
    chr_data = data[start:start + chr_size]
    out.mkdir(parents=True, exist_ok=True)
    (out / 'chr_rom.bin').write_bytes(chr_data)
    tiles = [decode_tile(chr_data[i:i + 16]) for i in range(0, len(chr_data), 16)]
    cols = 32
    rows = (len(tiles) + cols - 1) // cols
    width, height = cols * 8, rows * 8
    shades = (0, 85, 170, 255)
    rgb = bytearray()
    for y in range(height):
        for x in range(width):
            tile_index = (y // 8) * cols + (x // 8)
            value = tiles[tile_index][y % 8][x % 8] if tile_index < len(tiles) else 0
            shade = shades[value]
            rgb.extend((shade, shade, shade))
    ppm = out / 'chr_atlas.ppm'
    ppm.write_bytes(f'P6\n{width} {height}\n255\n'.encode() + rgb)
    manifest = {
        'input': rom.name, 'mapper': ((h[7] & 0xF0) | (h[6] >> 4)),
        'prg_rom_bytes': prg_size, 'chr_rom_bytes': chr_size,
        'chr_bank_bytes': 8192, 'chr_bank_count': chr_size // 8192,
        'tile_count': len(tiles), 'tile_size': [8, 8],
        'atlas': {'file': 'chr_atlas.png (convert chr_atlas.ppm to PNG if desired)', 'columns': cols, 'rows': rows},
        'note': 'Raw CHR patterns only; correct scene appearance also depends on runtime CHR bank selection, nametables, palettes, sprite composition, and emulation.'
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Extracted {len(tiles)} tiles ({chr_size} bytes) to {out}')
    print(f'Atlas: {ppm} ({width}x{height}); convert with ImageMagick: convert {ppm} {out / "chr_atlas.png"}')

if __name__ == '__main__':
    main()
