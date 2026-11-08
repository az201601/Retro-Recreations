#!/usr/bin/env python3
"""Export an iNES ROM's raw 2bpp CHR tiles as grayscale PNG contact sheets.

These are pattern-table indices, not the game's palettes or assembled sprites.
Uses only the Python standard library; does not modify the input ROM.
"""
import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path


def chunk(kind, data):
    return (struct.pack('>I', len(data)) + kind + data +
            struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff))


def png_gray(width, height, pixels):
    rows = b''.join(b'\0' + pixels[y * width:(y + 1) * width]
                    for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 0, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(rows, 9)) + chunk(b'IEND', b''))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    data = args.rom.read_bytes()
    if len(data) < 16 or data[:4] != b'NES\x1a':
        parser.error('not an iNES file')
    h = data[:16]
    if h[7] & 0x0c == 0x08:
        parser.error('NES 2.0 is not supported')
    start = 16 + (512 if h[6] & 4 else 0)
    prg_size, chr_size = h[4] * 16384, h[5] * 8192
    if not chr_size:
        parser.error('ROM has no CHR ROM (it may use CHR RAM)')
    if len(data) < start + prg_size + chr_size:
        parser.error('truncated ROM')
    chr_data = data[start + prg_size:start + prg_size + chr_size]
    args.output.mkdir(parents=True, exist_ok=True)
    # 256 tiles per sheet, in ascending CHR offset order.
    pages = []
    for base in range(0, len(chr_data), 4096):
        page = chr_data[base:base + 4096]
        pixels = bytearray(128 * 128)
        for tile in range(len(page) // 16):
            tx, ty = (tile % 16) * 8, (tile // 16) * 8
            for y in range(8):
                lo, hi = page[tile * 16 + y], page[tile * 16 + y + 8]
                for x in range(8):
                    index = ((lo >> (7-x)) & 1) | (((hi >> (7-x)) & 1) << 1)
                    pixels[(ty + y) * 128 + tx + x] = index * 85
        name = 'chr_%03d.png' % (base // 4096)
        (args.output / name).write_bytes(png_gray(128, 128, pixels))
        pages.append({'file': name, 'chr_byte_offset': base,
                      'first_tile': base // 16, 'tile_count': len(page) // 16})
    manifest = {'source_file': args.rom.name, 'sha256': hashlib.sha256(data).hexdigest(),
                'format': 'iNES', 'mapper': (h[6] >> 4) | (h[7] & 0xf0),
                'prg_bytes': prg_size, 'chr_bytes': chr_size,
                'chr_file_offset': start + prg_size,
                'tile_count': len(chr_data) // 16,
                'sheet_columns': 16, 'tile_width': 8, 'tile_height': 8,
                'note': 'Grayscale represents raw color indices 0-3; it is not the NES palette.',
                'sheets': pages}
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print('Exported %d tiles in %d sheets to %s' % (manifest['tile_count'], len(pages), args.output))


if __name__ == '__main__':
    main()
