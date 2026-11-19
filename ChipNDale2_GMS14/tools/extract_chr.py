#!/usr/bin/env python3
"""
extract_chr.py -- Extract NES CHR graphics from a .nes ROM.

Reads the iNES header, decodes the 8x8 2bpp CHR tiles, and writes PNG
sheets (tilesets / sprite-tile banks) using only the Python standard
library (no PIL needed).

Usage:
    python3 extract_chr.py "path/to/game.nes" [output_dir]

Outputs (into output_dir, default ./EXTRACTED):
    chr_sheet_full.png       every CHR tile, 128 cols, grayscale
    tileset_backgrounds.png  background banks as a tileset (game palette)
    palette.png              the game's 32-colour palette (from PRG $0F146)

The palette address ($0F146) is specific to Chip 'n Dale Rescue Rangers 2.
For other games you would need to locate their palette data in PRG.
"""
import sys, os, glob, struct, zlib

# Standard NES 64-colour palette (RGB hex).
NES = [
    0x7C7C7C,0x0000FC,0x0000BC,0x4428BC,0x9400BC,0xA80094,0xA80020,0xA81000,
    0x881400,0x503000,0x007800,0x006800,0x005800,0x004058,0x000000,0x000000,
    0xA8A8A8,0x0000FC,0x0000F8,0x6828FC,0xD800CC,0xE800A8,0xE80058,0xF83800,
    0xF83800,0x887800,0x008800,0x008858,0x008878,0x005898,0x000000,0x000000,
    0xB8B8B8,0x0078F8,0x0058F8,0x0058F8,0xD800F8,0xE800F8,0xF838F8,0xF85858,
    0xF85858,0xF8B858,0xF8D838,0xB8F858,0x58F858,0x58D8B8,0x58D8F8,0x78B8F8,
    0xF8F8F8,0xA0A0F8,0xA0A8F0,0xA0A0F8,0xF8A0F8,0xF8A0F8,0xF8A0F8,0xF8B8F8,
    0xF8B8F8,0xF8D8A0,0xF8E8A0,0xF8F0A0,0xF0F8A0,0xA0F8A0,0xA0F8F8,0xF8F8F8]
def _rgb(h): return ((h >> 16) & 255, (h >> 8) & 255, h & 255)
NES_RGB = [_rgb(h) for h in NES]
GRAY = [(0,0,0), (90,90,90), (170,170,170), (255,255,255)]
PALETTE_PRG_OFFSET = 0x0F146  # CnD2 game palette location

def tile_pixels(t):
    """Decode one 16-byte NES CHR tile into 64 values (0-3)."""
    p0, p1 = t[0:8], t[8:16]
    out = []
    for r in range(8):
        for c in range(8):
            bit = 7 - c
            out.append(((p0[r] >> bit) & 1) | (((p1[r] >> bit) & 1) << 1))
    return out

def write_png(path, w, h, rgb):
    raw = b''.join(b'\x00' + bytes(rgb[y*w*3:(y+1)*w*3]) for y in range(h))
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t+d) & 0xffffffff)
    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(raw, 9))
           + chunk(b'IEND', b''))
    open(path, 'wb').write(png)
    print('wrote', path, w, 'x', h)

def sheet(tiles, indices, cols, scale, path, palette):
    rows = (len(indices) + cols - 1) // cols
    W, H = cols*8*scale, rows*8*scale
    rgb = bytearray(W*H*3)
    for n, ti in enumerate(indices):
        px = tile_pixels(tiles[ti])
        tx, ty = (n % cols)*8*scale, (n // cols)*8*scale
        for y in range(8):
            for x in range(8):
                col = palette[px[y*8+x]]
                for sy in range(scale):
                    for sx in range(scale):
                        o = ((ty + y*scale + sy)*W + (tx + x*scale + sx))*3
                        rgb[o:o+3] = bytes(col)
    write_png(path, W, H, rgb)

def main():
    rom = sys.argv[1] if len(sys.argv) > 1 else glob.glob('*.nes')[0]
    outdir = sys.argv[2] if len(sys.argv) > 2 else 'EXTRACTED'
    os.makedirs(outdir, exist_ok=True)
    data = open(rom, 'rb').read()
    assert data[:4] == b'NES\x1a', 'not an iNES ROM'
    prg_size, chr_size = data[4]*16384, data[5]*8192
    prg = data[16:16+prg_size]
    chr_rom = data[16+prg_size:16+prg_size+chr_size]
    tiles = [chr_rom[i*16:i*16+16] for i in range(len(chr_rom)//16)]
    print('ROM:', rom, '| PRG', prg_size, 'CHR', chr_size, '| tiles', len(tiles))

    game_pal = list(prg[PALETTE_PRG_OFFSET:PALETTE_PRG_OFFSET+32])
    pal_bg = [NES_RGB[game_pal[i]] for i in range(4)]  # background subpalette 0

    sheet(tiles, list(range(len(tiles))), 128, 1,
          os.path.join(outdir, 'chr_sheet_full.png'), GRAY)
    sheet(tiles, list(range(0, min(20*256, len(tiles)))), 64, 1,
          os.path.join(outdir, 'tileset_backgrounds.png'), pal_bg)

    W, H = 32*16, 16
    rgb = bytearray(W*H*3)
    for i in range(32):
        col = NES_RGB[game_pal[i]]
        for y in range(H):
            for x in range(16):
                o = (y*W + i*16 + x)*3
                rgb[o:o+3] = bytes(col)
    write_png(os.path.join(outdir, 'palette.png'), W, H, rgb)
    print('done.')

if __name__ == '__main__':
    main()
