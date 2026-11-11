#!/usr/bin/env python3
"""Assemble selected frame-end OAM fragments from the matching PPU state."""
import argparse
import json
from pathlib import Path
from render_ppu import load_fceumm_palette, pixel, png, rgba


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('ppu', type=Path)
    p.add_argument('palette_source', type=Path)
    p.add_argument('output', type=Path, help='output PNG')
    p.add_argument('--indices', required=True, help='comma-separated OAM indices belonging to the candidate object')
    a = p.parse_args()
    try:
        indices = {int(v) for v in a.indices.split(',')}
    except ValueError:
        p.error('indices must be comma-separated integers')
    if not indices or any(i < 0 or i > 63 for i in indices):
        p.error('indices must be in range 0..63')
    state = json.loads((a.ppu/'state.json').read_text())
    chr_data = (a.ppu/'active_chr.bin').read_bytes()
    pal = (a.ppu/'palette_ram.bin').read_bytes()
    if len(chr_data) != 8192 or len(pal) != 32:
        p.error('unexpected PPU export sizes')
    colors = load_fceumm_palette(a.palette_source)
    sprites = [s for s in state['sprites'] if s['oam_index'] in indices]
    if len(sprites) != len(indices) or any(s['oam_y'] >= 239 for s in sprites):
        p.error('missing or offscreen OAM index')
    height = state['sprite_height']
    x0 = min(s['x'] for s in sprites)
    y0 = min(s['screen_y'] for s in sprites)
    width = max(s['x'] + 8 for s in sprites) - x0
    out_height = max(s['screen_y'] + height for s in sprites) - y0
    buf = bytearray(width*out_height*4)
    # Lower OAM indices take priority over higher ones where opaque pixels overlap.
    for s in sorted(sprites, key=lambda s: s['oam_index'], reverse=True):
        tile = s['tile']
        table, base = ((tile & 1, tile & 0xfe) if height == 16
                       else (state['sprite_pattern_table_if_8x8'], tile))
        for y in range(height):
            for x in range(8):
                sx = 7-x if s['flip_x'] else x
                sy = height-1-y if s['flip_y'] else y
                ci = pixel(chr_data, table, base+sy//8, sx, sy % 8)
                if ci:
                    dst = ((s['screen_y']-y0+y)*width+s['x']-x0+x)*4
                    buf[dst:dst+4] = rgba(colors[pal[16+s['palette']*4+ci] & 63])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    png(a.output, width, out_height, buf)
    metadata = {'oam_indices': sorted(indices), 'screen_x': x0, 'screen_y': y0,
                'width': width, 'height': out_height,
                'warning': 'Candidate assembled manually from one end-of-frame OAM state; no scanline limits, background priority, animation, or game-object identity verified.'}
    a.output.with_suffix('.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    print('Assembled %d OAM fragments into %dx%d image' % (len(indices), width, out_height))


if __name__ == '__main__':
    main()
