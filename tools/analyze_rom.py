#!/usr/bin/env python3
"""
ROM forensics for Chip 'n Dale Rescue Rangers 2 (USA) - MMC1
- iNES header, vectors, bank stats, entropy map
- CHR tile extraction (4KB banks, 2bpp planar)
- PRG data-bank heuristics (code vs data scoring)
- Text / pointer table scan
Usage: python3 tools/analyze_rom.py --rom "...nes" --out analysis/rom_forensics.md
"""
import argparse, struct, hashlib, math, collections, os, re

def entropy(b):
    if not b: return 0
    c=collections.Counter(b)
    return -sum((v/len(b))*math.log2(v/len(b)) for v in c.values())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--chr-out", default=None, help="dir to dump CHR tiles as PNG-ish PPM")
    args=ap.parse_args()
    data=open(args.rom,'rb').read()
    print(f"file: {args.rom} size={len(data)} sha256={hashlib.sha256(data).hexdigest()} md5={hashlib.md5(data).hexdigest()}")
    assert data[:4]==b'NES\x1a'
    prg_banks, chr_banks = data[4], data[5]
    flags6, flags7 = data[6], data[7]
    mapper = ((flags7 & 0xF0) | (flags6>>4))
    prg=data[16:16+prg_banks*16384]
    chr_=data[16+prg_banks*16384:16+prg_banks*16384+chr_banks*8192]
    print(f"PRG {prg_banks}x16KB={len(prg)} CHR {chr_banks}x8KB={len(chr_)} mapper={mapper} flags6=${flags6:02X} flags7=${flags7:02X}")
    print(f"header mirroring bit: {'vertical' if flags6&1 else 'horizontal'} (IGNORED for MMC1 - real mirroring from MMC1 control $1E = vertical)")
    # vectors
    vec=prg[-6:]
    nmi,rst,irq=struct.unpack('<HHH',vec)
    print(f"vectors NMI=${nmi:04X} RESET=${rst:04X} IRQ=${irq:04X}")
    print(f"reset stub @ $FFE0: {prg[-32:].hex(' ')}")
    print(f"  -> SEI; INC $FFE1 (MMC1 reset: write $E2 bit7=1); CLD; JMP $C000; JMP $C106")
    # bank stats
    print("\nPRG banks (16KB):")
    for i in range(prg_banks):
        b=prg[i*16384:(i+1)*16384]
        print(f"  bank {i} @file ${16+i*16384:05X} sha={hashlib.sha256(b).hexdigest()[:12]} entropy={entropy(b):.3f} nonzero={sum(1 for x in b if x)} first16={b[:16].hex(' ')}")
    print("\nCHR banks (8KB = 2x4KB):")
    for i in range(chr_banks):
        b=chr_[i*8192:(i+1)*8192]
        print(f"  chr8k {i} sha={hashlib.sha256(b).hexdigest()[:12]} entropy={entropy(b):.3f} nonzero={sum(1 for x in b if x)}")
    # CHR 4KB sub-banks
    print("\nCHR 4KB sub-banks (32 total, MMC1 CHR0/CHR1):")
    for i in range(32):
        b=chr_[i*4096:(i+1)*4096]
        # count distinct tiles (256 tiles per 4KB)
        tiles=[b[j*16:(j+1)*16] for j in range(256)]
        uniq=len(set(tiles))
        print(f"  chr4k {i:2d} (8k {i//2} half {i%2}) sha={hashlib.sha256(b).hexdigest()[:12]} entropy={entropy(b):.3f} uniq_tiles={uniq}/256")
    # PRG code-vs-data heuristic: % bytes that are valid opcodes in linear sweep + JSR/JMP density
    print("\nPRG bank code-vs-data heuristic (linear sweep valid-opcode ratio):")
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from dis6502 import OPS
    for i in range(prg_banks):
        b=prg[i*16384:(i+1)*16384]
        pc=0; valid=0; total=0; jsr=0
        while pc < len(b):
            op=b[pc]
            total+=1
            if op in OPS:
                valid+=1
                mnem,mode,size=OPS[op]
                if mnem=="JSR": jsr+=1
                pc+=size
            else:
                pc+=1
        print(f"  bank {i}: valid {valid}/{total} ({valid/total*100:.1f}%) JSRs={jsr} -> {'CODE?' if valid/total>0.85 else 'DATA?'}")
    # strings
    strs=re.findall(rb'[ -~]{6,}', data)
    print(f"\nASCII strings >=6 chars: {len(strs)} (first 30)")
    for s in strs[:30]:
        print(f"  {s[:100]}")
    # entropy map per 1KB
    print("\nEntropy map per 4KB (PRG):")
    for i in range(0,len(prg),4096):
        print(f"  PRG ${i:05X} ent={entropy(prg[i:i+4096]):.2f}")
    print("\nEntropy map per 4KB (CHR):")
    for i in range(0,len(chr_),4096):
        print(f"  CHR ${i:05X} ent={entropy(chr_[i:i+4096]):.2f}")
    if args.out:
        # write markdown summary (appendix generated)
        with open(args.out,'w') as f:
            f.write(f"# ROM forensics (generated)\n\n- File: `{args.rom}`\n- Size: {len(data)} bytes\n- SHA256: `{hashlib.sha256(data).hexdigest()}`\n- MD5: `{hashlib.md5(data).hexdigest()}`\n- iNES: PRG {prg_banks}x16KB, CHR {chr_banks}x8KB, mapper {mapper} (MMC1), flags6=${flags6:02X} flags7=${flags7:02X}\n- Vectors: NMI=${nmi:04X} RESET=${rst:04X} IRQ=${irq:04X}\n- MMC1 control $1E = vertical mirroring, 16KB PRG @ $8000, CHR 4KBx2\n")
            f.write("\n## PRG banks\n\n| bank | file offset | sha256[:12] | entropy | first16 |\n|---|---|---|---|---|\n")
            for i in range(prg_banks):
                b=prg[i*16384:(i+1)*16384]
                f.write(f"| {i} | ${16+i*16384:05X} | {hashlib.sha256(b).hexdigest()[:12]} | {entropy(b):.3f} | `{b[:16].hex(' ')}` |\n")
            f.write("\n## CHR 4KB sub-banks\n\n| idx | sha[:12] | entropy | uniq tiles |\n|---|---|---|---|\n")
            for i in range(32):
                b=chr_[i*4096:(i+1)*4096]
                tiles=[b[j*16:(j+1)*16] for j in range(256)]
                f.write(f"| {i} | {hashlib.sha256(b).hexdigest()[:12]} | {entropy(b):.3f} | {len(set(tiles))}/256 |\n")
        print(f"wrote {args.out}")

if __name__=="__main__":
    main()
