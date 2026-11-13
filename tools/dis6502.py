#!/usr/bin/env python3
"""
6502 / NES disassembler for Chip 'n Dale Rescue Rangers 2 (MMC1, 128KB PRG)
- Recursive traversal from RESET/NMI vectors + linear sweep fallback
- MMC1 write detection (STA/STX/STY/INC/DEC to $8000-$FFFF)
- PPU/APU register annotation ($2000-$2007, $4000-$4017, $4014, $4016/$4017)
- Fixed bank ($C000-$FFFF = PRG bank 7) + switchable bank ($8000-$BFFF) views

Usage:
  python3 tools/dis6502.py --rom "Chip 'n Dale - Rescue Rangers 2 (USA).nes" --bank 7 --base 0xC000 --out disassembly/fixed_bank_C000.asm
  python3 tools/dis6502.py --rom ... --bank 6 --base 0x8000 --out disassembly/bank6_8000.asm
  python3 tools/dis6502.py --rom ... --trace   # recursive trace from vectors, prints MMC1/PPU writes
"""
import argparse, struct, sys, os

# opcode table: opcode -> (mnemonic, mode, size)
# modes: imp, acc, imm, zp, zpx, zpy, abs, absx, absy, ind, indx, indy, rel
OPS = {}
def op(code, mnem, mode, size):
    OPS[code] = (mnem, mode, size)

# Official opcodes
op(0x00,"BRK","imp",1); op(0x01,"ORA","indx",2); op(0x05,"ORA","zp",2); op(0x06,"ASL","zp",2)
op(0x08,"PHP","imp",1); op(0x09,"ORA","imm",2); op(0x0A,"ASL","acc",1); op(0x0D,"ORA","abs",3)
op(0x0E,"ASL","abs",3); op(0x10,"BPL","rel",2); op(0x11,"ORA","indy",2); op(0x15,"ORA","zpx",2)
op(0x16,"ASL","zpx",2); op(0x18,"CLC","imp",1); op(0x19,"ORA","absy",3); op(0x1D,"ORA","absx",3)
op(0x1E,"ASL","absx",3); op(0x20,"JSR","abs",3); op(0x21,"AND","indx",2); op(0x24,"BIT","zp",2)
op(0x25,"AND","zp",2); op(0x26,"ROL","zp",2); op(0x28,"PLP","imp",1); op(0x29,"AND","imm",2)
op(0x2A,"ROL","acc",1); op(0x2C,"BIT","abs",3); op(0x2D,"AND","abs",3); op(0x2E,"ROL","abs",3)
op(0x30,"BMI","rel",2); op(0x31,"AND","indy",2); op(0x35,"AND","zpx",2); op(0x36,"ROL","zpx",2)
op(0x38,"SEC","imp",1); op(0x39,"AND","absy",3); op(0x3D,"AND","absx",3); op(0x3E,"ROL","absx",3)
op(0x40,"RTI","imp",1); op(0x41,"EOR","indx",2); op(0x45,"EOR","zp",2); op(0x46,"LSR","zp",2)
op(0x48,"PHA","imp",1); op(0x49,"EOR","imm",2); op(0x4A,"LSR","acc",1); op(0x4C,"JMP","abs",3)
op(0x4D,"EOR","abs",3); op(0x4E,"LSR","abs",3); op(0x50,"BVC","rel",2); op(0x51,"EOR","indy",2)
op(0x55,"EOR","zpx",2); op(0x56,"LSR","zpx",2); op(0x58,"CLI","imp",1); op(0x59,"EOR","absy",3)
op(0x5D,"EOR","absx",3); op(0x5E,"LSR","absx",3); op(0x60,"RTS","imp",1); op(0x61,"ADC","indx",2)
op(0x65,"ADC","zp",2); op(0x66,"ROR","zp",2); op(0x68,"PLA","imp",1); op(0x69,"ADC","imm",2)
op(0x6A,"ROR","acc",1); op(0x6C,"JMP","ind",3); op(0x6D,"ADC","abs",3); op(0x6E,"ROR","abs",3)
op(0x70,"BVS","rel",2); op(0x71,"ADC","indy",2); op(0x75,"ADC","zpx",2); op(0x76,"ROR","zpx",2)
op(0x78,"SEI","imp",1); op(0x79,"ADC","absy",3); op(0x7D,"ADC","absx",3); op(0x7E,"ROR","absx",3)
op(0x81,"STA","indx",2); op(0x84,"STY","zp",2); op(0x85,"STA","zp",2); op(0x86,"STX","zp",2)
op(0x88,"DEY","imp",1); op(0x8A,"TXA","imp",1); op(0x8C,"STY","abs",3); op(0x8D,"STA","abs",3)
op(0x8E,"STX","abs",3); op(0x90,"BCC","rel",2); op(0x91,"STA","indy",2); op(0x94,"STY","zpx",2)
op(0x95,"STA","zpx",2); op(0x96,"STX","zpy",2); op(0x98,"TYA","imp",1); op(0x99,"STA","absy",3)
op(0x9A,"TXS","imp",1); op(0x9D,"STA","absx",3); op(0xA0,"LDY","imm",2); op(0xA1,"LDA","indx",2)
op(0xA2,"LDX","imm",2); op(0xA4,"LDY","zp",2); op(0xA5,"LDA","zp",2); op(0xA6,"LDX","zp",2)
op(0xA8,"TAY","imp",1); op(0xA9,"LDA","imm",2); op(0xAA,"TAX","imp",1); op(0xAC,"LDY","abs",3)
op(0xAD,"LDA","abs",3); op(0xAE,"LDX","abs",3); op(0xB0,"BCS","rel",2); op(0xB1,"LDA","indy",2)
op(0xB4,"LDY","zpx",2); op(0xB5,"LDA","zpx",2); op(0xB6,"LDX","zpy",2); op(0xB8,"CLV","imp",1)
op(0xB9,"LDA","absy",3); op(0xBA,"TSX","imp",1); op(0xBC,"LDY","absx",3); op(0xBD,"LDA","absx",3)
op(0xBE,"LDX","absy",3); op(0xC0,"CPY","imm",2); op(0xC1,"CMP","indx",2); op(0xC4,"CPY","zp",2)
op(0xC5,"CMP","zp",2); op(0xC6,"DEC","zp",2); op(0xC8,"INY","imp",1); op(0xC9,"CMP","imm",2)
op(0xCA,"DEX","imp",1); op(0xCC,"CPY","abs",3); op(0xCD,"CMP","abs",3); op(0xCE,"DEC","abs",3)
op(0xD0,"BNE","rel",2); op(0xD1,"CMP","indy",2); op(0xD5,"CMP","zpx",2); op(0xD6,"DEC","zpx",2)
op(0xD8,"CLD","imp",1); op(0xD9,"CMP","absy",3); op(0xDD,"CMP","absx",3); op(0xDE,"DEC","absx",3)
op(0xE0,"CPX","imm",2); op(0xE1,"SBC","indx",2); op(0xE4,"CPX","zp",2); op(0xE5,"SBC","zp",2)
op(0xE6,"INC","zp",2); op(0xE8,"INX","imp",1); op(0xE9,"SBC","imm",2); op(0xEA,"NOP","imp",1)
op(0xEC,"CPX","abs",3); op(0xED,"SBC","abs",3); op(0xEE,"INC","abs",3); op(0xF0,"BEQ","rel",2)
op(0xF1,"SBC","indy",2); op(0xF5,"SBC","zpx",2); op(0xF6,"INC","zpx",2); op(0xF8,"SED","imp",1)
op(0xF9,"SBC","absy",3); op(0xFD,"SBC","absx",3); op(0xFE,"INC","absx",3)

PPU_REGS = {0x2000:"PPUCTRL",0x2001:"PPUMASK",0x2002:"PPUSTATUS",0x2003:"OAMADDR",0x2004:"OAMDATA",
             0x2005:"PPUSCROLL",0x2006:"PPUADDR",0x2007:"PPUDATA"}
APU_REGS = {0x4000:"SQ1_VOL",0x4001:"SQ1_SWEEP",0x4002:"SQ1_LO",0x4003:"SQ1_HI",0x4004:"SQ2_VOL",
            0x4005:"SQ2_SWEEP",0x4006:"SQ2_LO",0x4007:"SQ2_HI",0x4008:"TRI_LIN",0x400A:"TRI_LO",
            0x400B:"TRI_HI",0x400C:"NOISE_VOL",0x400E:"NOISE_LO",0x400F:"NOISE_HI",0x4010:"DMC_FREQ",
            0x4011:"DMC_RAW",0x4012:"DMC_START",0x4013:"DMC_LEN",0x4015:"APUSTATUS",0x4017:"APUFRAME",
            0x4014:"OAMDMA",0x4016:"JOY1",0x4017:"JOY2/APUFRAME"}

def load_rom(path):
    data = open(path,'rb').read()
    assert data[:4]==b'NES\x1a', "not iNES"
    prg_banks, chr_banks = data[4], data[5]
    prg = data[16:16+prg_banks*16384]
    chr_ = data[16+prg_banks*16384:16+prg_banks*16384+chr_banks*8192]
    return data, prg, chr_, prg_banks, chr_banks

def bank_bytes(prg, bank):
    return prg[bank*16384:(bank+1)*16384]

def fmt_operand(mode, operand_bytes, addr, size):
    if mode=="imp": return ""
    if mode=="acc": return "A"
    if mode=="imm": return f"#${operand_bytes[0]:02X}"
    if mode=="zp": return f"${operand_bytes[0]:02X}"
    if mode=="zpx": return f"${operand_bytes[0]:02X},X"
    if mode=="zpy": return f"${operand_bytes[0]:02X},Y"
    if mode=="abs":
        v = operand_bytes[0] | (operand_bytes[1]<<8)
        return f"${v:04X}"
    if mode=="absx":
        v = operand_bytes[0] | (operand_bytes[1]<<8)
        return f"${v:04X},X"
    if mode=="absy":
        v = operand_bytes[0] | (operand_bytes[1]<<8)
        return f"${v:04X},Y"
    if mode=="ind":
        v = operand_bytes[0] | (operand_bytes[1]<<8)
        return f"(${v:04X})"
    if mode=="indx": return f"(${operand_bytes[0]:02X},X)"
    if mode=="indy": return f"(${operand_bytes[0]:02X}),Y"
    if mode=="rel":
        off = operand_bytes[0]
        if off>=128: off-=256
        target = addr+size+off
        return f"${target:04X}"
    return "?"

def annotate(addr, mnem, mode, operand_bytes):
    notes=[]
    if mode in ("abs","absx","absy") and len(operand_bytes)>=2:
        v = operand_bytes[0] | (operand_bytes[1]<<8)
        if v in PPU_REGS: notes.append(f"PPU:{PPU_REGS[v]}")
        if v in APU_REGS: notes.append(f"APU:{APU_REGS[v]}")
        if 0x8000 <= v <= 0xFFFF and mnem in ("STA","STX","STY","INC","DEC","ASL","LSR","ROL","ROR"):
            notes.append("MMC1-WRITE? (serial $8000-$FFFF)")
        if v==0x4014: notes.append("OAM DMA $XX00 page")
        if v in (0x4016,0x4017): notes.append("Controller read")
    return "  ; "+" | ".join(notes) if notes else ""

def disassemble_linear(code, base, start_off=0, end_off=None):
    if end_off is None: end_off=len(code)
    lines=[]
    pc=start_off
    while pc < end_off:
        addr = base+pc
        opcode = code[pc]
        if opcode not in OPS:
            lines.append(f"{addr:04X}:  {opcode:02X}        .byte ${opcode:02X}  ; unknown/illegal")
            pc+=1
            continue
        mnem, mode, size = OPS[opcode]
        if pc+size > len(code):
            lines.append(f"{addr:04X}:  {code[pc]:02X}        .byte ${opcode:02X}  ; truncated")
            break
        operand = code[pc+1:pc+size]
        operand_str = fmt_operand(mode, operand, addr, size)
        bytes_str = " ".join(f"{b:02X}" for b in code[pc:pc+size])
        ann = annotate(addr, mnem, mode, operand)
        lines.append(f"{addr:04X}:  {bytes_str:<8} {mnem:<4} {operand_str}{ann}")
        pc+=size
    return lines

def trace_recursive(prg, fixed_bank=7):
    """Follow JMP/JSR/branch from RESET stub and NMI. Returns set of code offsets in fixed bank."""
    fixed = bank_bytes(prg, fixed_bank)
    base = 0xC000
    # entry points: $FFE0 stub, $C000 trampoline, $C003 NMI
    entries = [0xFFE0, 0xC000, 0xC003]
    visited=set()
    worklist=[]
    for e in entries:
        off=e-base
        if 0<=off<len(fixed): worklist.append(off)
    mmc1_writes=[]; ppu_writes=[]; apu_writes=[]; jsr_targets=set(); jmp_targets=set()
    while worklist:
        off=worklist.pop()
        while 0<=off<len(fixed) and off not in visited:
            visited.add(off)
            opcode=fixed[off]
            if opcode not in OPS: break
            mnem,mode,size=OPS[opcode]
            addr=base+off
            operand=fixed[off+1:off+size]
            # record writes
            if mode in ("abs","absx","absy") and len(operand)>=2:
                v=operand[0]|(operand[1]<<8)
                if mnem in ("STA","STX","STY","INC","DEC") and 0x8000<=v<=0xFFFF:
                    mmc1_writes.append((addr,v,mnem))
                if v in PPU_REGS and mnem in ("STA","STX","STY"):
                    ppu_writes.append((addr,v,mnem))
                if v in APU_REGS and mnem in ("STA","STX","STY"):
                    apu_writes.append((addr,v,mnem))
            if mnem=="JMP" and mode=="abs":
                t=operand[0]|(operand[1]<<8)
                jmp_targets.add(t)
                if 0xC000<=t<=0xFFFF:
                    worklist.append(t-base); break
                else: break
            elif mnem=="JSR":
                t=operand[0]|(operand[1]<<8)
                jsr_targets.add(t)
                if 0xC000<=t<=0xFFFF:
                    worklist.append(t-base)
                off+=size; continue
            elif mode=="rel":
                offv=operand[0]
                if offv>=128: offv-=256
                t=addr+size+offv
                if 0xC000<=t<=0xFFFF:
                    worklist.append(t-base)
                off+=size; continue
            elif mnem in ("RTS","RTI","BRK"):
                break
            else:
                off+=size; continue
    return visited, mmc1_writes, ppu_writes, apu_writes, jsr_targets, jmp_targets

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--bank", type=int, default=7)
    ap.add_argument("--base", type=lambda x:int(x,0), default=0xC000)
    ap.add_argument("--out", default=None)
    ap.add_argument("--trace", action="store_true")
    args=ap.parse_args()
    data,prg,chr_,pb,cb=load_rom(args.rom)
    print(f"ROM: PRG {pb} banks, CHR {cb} banks, mapper 1 (MMC1)")
    if args.trace:
        visited,mmc1,ppu,apu,jsr,jmp=trace_recursive(prg)
        print(f"\n=== Recursive trace from RESET/NMI (fixed bank 7 @ $C000) ===")
        print(f"code bytes visited: {len(visited)}")
        print(f"JSR targets ({len(jsr)}): {sorted(f'${x:04X}' for x in jsr)}")
        print(f"JMP targets ({len(jmp)}): {sorted(f'${x:04X}' for x in jmp)}")
        print(f"\nMMC1 writes ({len(mmc1)}):")
        for a,v,m in sorted(set(mmc1)):
            print(f"  ${a:04X}: {m} ${v:04X}")
        print(f"\nPPU writes ({len(ppu)}):")
        for a,v,m in sorted(set(ppu)):
            print(f"  ${a:04X}: {m} ${v:04X} ({PPU_REGS.get(v,'?')})")
        print(f"\nAPU writes ({len(apu)}):")
        for a,v,m in sorted(set(apu)):
            print(f"  ${a:04X}: {m} ${v:04X} ({APU_REGS.get(v,'?')})")
        # dump visited code linearised in address order
        fixed=bank_bytes(prg,7)
        print(f"\n=== Visited code (address order) ===")
        offs=sorted(visited)
        # group contiguous
        for off in offs:
            opcode=fixed[off]
            if opcode not in OPS: continue
            mnem,mode,size=OPS[opcode]
            addr=args.base+off if False else 0xC000+off
            operand=fixed[off+1:off+size]
            print(f"{addr:04X}: {mnem:<4} {fmt_operand(mode,operand,addr,size)}{annotate(addr,mnem,mode,operand)}")
        return
    code=bank_bytes(prg,args.bank)
    lines=disassemble_linear(code,args.base)
    header=[f"; Chip 'n Dale Rescue Rangers 2 (USA) - PRG bank {args.bank} @ ${args.base:04X}",
            f"; Mapper 1 (MMC1), 128KB PRG / 128KB CHR, horizontal mirroring",
            f"; Generated by tools/dis6502.py - linear sweep, verify with recursive trace",
            f"; File offset: ${16+args.bank*16384:05X}  Size: 16384 bytes",
            ""]
    out="\n".join(header+lines)+"\n"
    if args.out:
        open(args.out,'w').write(out)
        print(f"wrote {args.out} ({len(lines)} lines)")
    else:
        print(out)

if __name__=="__main__":
    main()
