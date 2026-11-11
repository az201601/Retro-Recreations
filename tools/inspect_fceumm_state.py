#!/usr/bin/env python3
"""Extract PPU and MMC1 research data from an uncompressed FCEU state."""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def parse_state(data):
    if len(data) < 16 or data[:4] != b'FCS\xff':
        raise ValueError('expected an uncompressed FCEU state')
    length = struct.unpack_from('<I', data, 4)[0]
    end = 16 + length
    if end > len(data):
        raise ValueError('truncated state')
    fields = {}
    pos = 16
    while pos < end:
        if pos + 5 > end:
            raise ValueError('truncated chunk header')
        kind, size = struct.unpack_from('<BI', data, pos)
        pos += 5
        stop = pos + size
        if stop > end:
            raise ValueError('truncated chunk')
        while pos < stop:
            if pos + 8 > stop:
                raise ValueError('truncated field header')
            tag, size = struct.unpack_from('<4sI', data, pos)
            pos += 8
            if pos + size > stop:
                raise ValueError('truncated field')
            key = (kind, tag)
            if key in fields:
                raise ValueError('duplicate field')
            fields[key] = data[pos:pos + size]
            pos += size
    return fields


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('state', type=Path)
    p.add_argument('rom', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    data, rom = a.state.read_bytes(), a.rom.read_bytes()
    fields = parse_state(data)
    def require(chunk, name, size):
        value = fields.get((chunk, name.encode('ascii')))
        if value is None or len(value) != size:
            raise ValueError('missing or unexpected field %s' % name)
        return value
    if len(rom) < 16 or rom[:4] != b'NES\x1a' or rom[7] & 12 == 8:
        raise ValueError('expected iNES ROM')
    mapper = (rom[6] >> 4) | (rom[7] & 0xf0)
    chr_start = 16 + (512 if rom[6] & 4 else 0) + rom[4] * 16384
    chr_size = rom[5] * 8192
    if mapper != 1 or not chr_size or len(rom) < chr_start + chr_size:
        raise ValueError('expected complete mapper 1 ROM with CHR ROM')
    nt = require(3, 'NTAR', 2048)
    pal = require(3, 'PRAM', 32)
    oam = require(3, 'SPRA', 256)
    ppu = require(3, 'PPUR', 4)
    reg = require(16, 'DREG', 4)
    banks = [reg[1], reg[2]] if reg[0] & 16 else [reg[1] & ~1, reg[1] | 1]
    # Standard MMC1 mapping, normalized to the actual CHR ROM size.
    banks = [b % (chr_size // 4096) for b in banks]
    active_chr = b''.join(rom[chr_start + b*4096:chr_start + (b+1)*4096] for b in banks)
    sprites = []
    for i in range(64):
        y, tile, attr, x = oam[i*4:i*4+4]
        sprites.append({'oam_index': i, 'x': x, 'oam_y': y, 'screen_y': (y+1) % 256,
                        'tile': tile, 'palette': attr & 3, 'behind_background': bool(attr & 32),
                        'flip_x': bool(attr & 64), 'flip_y': bool(attr & 128)})
    mirroring = ['one-screen lower', 'one-screen upper', 'vertical', 'horizontal'][reg[0] & 3]
    result = {'state_sha256': hashlib.sha256(data).hexdigest(), 'rom_sha256': hashlib.sha256(rom).hexdigest(),
              'mapper': mapper, 'mmc1_registers': list(reg), 'mirroring_at_capture': mirroring,
              'chr_4k_banks_at_capture': banks, 'ppu_registers': list(ppu),
              'ppu_ctrl': ppu[0], 'ppu_mask': ppu[1], 'sprite_height': 16 if ppu[0] & 32 else 8,
              'background_pattern_table': (ppu[0] >> 4) & 1, 'sprite_pattern_table_if_8x8': (ppu[0] >> 3) & 1,
              'palette_indices': list(pal), 'sprites': sprites,
              'warning': 'End-of-frame state only: mid-frame register changes, scrolling and sprite assembly are not reconstructed. Palette indices are not RGB values.'}
    a.output.mkdir(parents=True, exist_ok=True)
    (a.output / 'active_chr.bin').write_bytes(active_chr)
    (a.output / 'nametable_ram.bin').write_bytes(nt)
    (a.output / 'palette_ram.bin').write_bytes(pal)
    (a.output / 'oam.bin').write_bytes(oam)
    (a.output / 'state.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PPU state exported; CHR 4 KiB banks:', banks, 'mirroring:', mirroring)


if __name__ == '__main__':
    main()
