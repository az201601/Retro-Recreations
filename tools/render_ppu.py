#!/usr/bin/env python3
"""Render frame-end PPU research exports as nametables, tile atlases and OAM fragments."""
import argparse
import json
import re
import struct
import zlib
from pathlib import Path


def png(path, w, h, pixels):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    rows = b''.join(b'\0' + pixels[y*w*4:(y+1)*w*4] for y in range(h))
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rows, 9)) + chunk(b'IEND', b''))


def load_fceumm_palette(path):
    # Read the palette from the installed core's source instead of embedding it.
    text = path.read_text(encoding='utf-8')
    match = re.search(r'pal\s+palette\s*\[512\]\s*=\s*\{(.*?)EMPTY_PALETTE', text, re.S)
    if not match:
        raise ValueError('cannot locate FCEUmm default palette')
    triples = re.findall(r'\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\}', match.group(1))
    if len(triples) != 64:
        raise ValueError('expected 64 palette colors')
    return [tuple(map(int, color)) for color in triples]


def pixel(chr_data, table, tile, x, y):
    offset = table * 4096 + tile * 16 + y
    bit = 7 - x
    return ((chr_data[offset] >> bit) & 1) | (((chr_data[offset + 8] >> bit) & 1) << 1)


def rgba(color, alpha=255):
    return bytes((*color, alpha))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('ppu', type=Path, help='output directory from inspect_fceumm_state.py')
    p.add_argument('palette_source', type=Path, help='FCEUmm src/palettes/palettes.h')
    p.add_argument('output', type=Path)
    a = p.parse_args()
    state = json.loads((a.ppu / 'state.json').read_text())
    chr_data = (a.ppu / 'active_chr.bin').read_bytes()
    nt = (a.ppu / 'nametable_ram.bin').read_bytes()
    pal = (a.ppu / 'palette_ram.bin').read_bytes()
    if len(chr_data) != 8192 or len(nt) != 2048 or len(pal) != 32:
        p.error('unexpected PPU export sizes')
    colors = load_fceumm_palette(a.palette_source)
    a.output.mkdir(parents=True, exist_ok=True)
    bg_table = state['background_pattern_table']
    atlas_files = []
    for palette in range(4):
        pixels = bytearray(128*128*4)
        for tile in range(256):
            for y in range(8):
                for x in range(8):
                    ci = pixel(chr_data, bg_table, tile, x, y)
                    nes = pal[0 if ci == 0 else palette * 4 + ci] & 63
                    dst = (((tile // 16)*8+y)*128 + (tile % 16)*8+x)*4
                    pixels[dst:dst+4] = rgba(colors[nes])
        name = 'background_tiles_palette_%d.png' % palette
        png(a.output / name, 128, 128, pixels)
        atlas_files.append(name)
    nametable_files = []
    for page in range(2):
        buf = bytearray(256*240*4)
        page_data = nt[page*1024:(page+1)*1024]
        for ty in range(30):
            for tx in range(32):
                tile = page_data[ty*32+tx]
                attr = page_data[960+(ty//4)*8+tx//4]
                palette = (attr >> (((ty % 4)//2)*4 + ((tx % 4)//2)*2)) & 3
                for y in range(8):
                    for x in range(8):
                        ci = pixel(chr_data, bg_table, tile, x, y)
                        nes = pal[0 if ci == 0 else palette*4+ci] & 63
                        dst = ((ty*8+y)*256+tx*8+x)*4
                        buf[dst:dst+4] = rgba(colors[nes])
        name = 'nametable_physical_%d.png' % page
        png(a.output / name, 256, 240, buf)
        nametable_files.append(name)
    fragment_dir = a.output / 'oam_fragments'
    fragment_dir.mkdir(exist_ok=True)
    fragments = []
    height = state['sprite_height']
    for sprite in state['sprites']:
        if sprite['oam_y'] >= 239:
            continue
        tile = sprite['tile']
        if height == 16:
            table, base = tile & 1, tile & 0xfe
        else:
            table, base = state['sprite_pattern_table_if_8x8'], tile
        buf = bytearray(8*height*4)
        for y in range(height):
            for x in range(8):
                sx = 7-x if sprite['flip_x'] else x
                sy = height-1-y if sprite['flip_y'] else y
                ci = pixel(chr_data, table, base + sy//8, sx, sy % 8)
                color = colors[pal[16+sprite['palette']*4+ci] & 63] if ci else (0, 0, 0)
                dst = (y*8+x)*4
                buf[dst:dst+4] = rgba(color, 255 if ci else 0)
        name = 'oam_%02d.png' % sprite['oam_index']
        png(fragment_dir / name, 8, height, buf)
        fragments.append({'file': 'oam_fragments/' + name, **sprite})
    report = {'source': str(a.ppu), 'nametables': nametable_files, 'background_atlases': atlas_files,
              'fragments': fragments, 'palette_source': str(a.palette_source),
              'warning': 'Frame-end data, not guaranteed to represent the full rendered frame. Physical nametables are not screen-aligned. OAM fragments may be hidden or unused; they are not assembled game sprites.'}
    (a.output / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Rendered 2 nametables, 4 background tile atlases and %d OAM fragments' % len(fragments))


if __name__ == '__main__':
    main()
