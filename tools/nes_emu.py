#!/usr/bin/env python3
"""
Minimal NES emulator for dynamic validation (Chip 'n Dale Rescue Rangers 2, MMC1)
- 6502 CPU (official opcodes), NMI/IRQ/RESET, BRK/RTI
- MMC1 (serial, control/CHR0/CHR1/PRG, 16KB PRG low + fixed, CHR 4KBx2, vertical mirroring)
- PPU stub (registers, VRAM nametable/palette, OAM, VBlank timing, OAMDMA)
- APU stub (writes ignored, $4015/$4017)
- Controller $4016/$4017 with scripted input
- Logging: MMC1 commits, $40 state, $1D-$20 CHR banks, $0600, PC trace (optional)

Usage:
  python3 tools/nes_emu.py --rom "Chip 'n Dale - Rescue Rangers 2 (USA).nes" --frames 600 --log analysis/dynamic_log.txt
  python3 tools/nes_emu.py --rom ... --frames 600 --trace-pc --log analysis/dynamic_log.txt
"""
import argparse, struct, sys

# 6502 opcode table: opcode -> (mnemonic, mode, cycles)
# modes: imp, acc, imm, zp, zpx, zpy, abs, absx, absy, ind, indx, indy, rel
OPS = {}
def op(code, mnem, mode, cycles):
    OPS[code] = (mnem, mode, cycles)

op(0x00,"BRK","imp",7); op(0x01,"ORA","indx",6); op(0x05,"ORA","zp",3); op(0x06,"ASL","zp",5)
op(0x08,"PHP","imp",3); op(0x09,"ORA","imm",2); op(0x0A,"ASL","acc",2); op(0x0D,"ORA","abs",4)
op(0x0E,"ASL","abs",6); op(0x10,"BPL","rel",2); op(0x11,"ORA","indy",5); op(0x15,"ORA","zpx",4)
op(0x16,"ASL","zpx",6); op(0x18,"CLC","imp",2); op(0x19,"ORA","absy",4); op(0x1D,"ORA","absx",4)
op(0x1E,"ASL","absx",7); op(0x20,"JSR","abs",6); op(0x21,"AND","indx",6); op(0x24,"BIT","zp",3)
op(0x25,"AND","zp",3); op(0x26,"ROL","zp",5); op(0x28,"PLP","imp",4); op(0x29,"AND","imm",2)
op(0x2A,"ROL","acc",2); op(0x2C,"BIT","abs",4); op(0x2D,"AND","abs",4); op(0x2E,"ROL","abs",6)
op(0x30,"BMI","rel",2); op(0x31,"AND","indy",5); op(0x35,"AND","zpx",4); op(0x36,"ROL","zpx",6)
op(0x38,"SEC","imp",2); op(0x39,"AND","absy",4); op(0x3D,"AND","absx",4); op(0x3E,"ROL","absx",7)
op(0x40,"RTI","imp",6); op(0x41,"EOR","indx",6); op(0x45,"EOR","zp",3); op(0x46,"LSR","zp",5)
op(0x48,"PHA","imp",3); op(0x49,"EOR","imm",2); op(0x4A,"LSR","acc",2); op(0x4C,"JMP","abs",3)
op(0x4D,"EOR","abs",4); op(0x4E,"LSR","abs",6); op(0x50,"BVC","rel",2); op(0x51,"EOR","indy",5)
op(0x55,"EOR","zpx",4); op(0x56,"LSR","zpx",6); op(0x58,"CLI","imp",2); op(0x59,"EOR","absy",4)
op(0x5D,"EOR","absx",4); op(0x5E,"LSR","absx",7); op(0x60,"RTS","imp",6); op(0x61,"ADC","indx",6)
op(0x65,"ADC","zp",3); op(0x66,"ROR","zp",5); op(0x68,"PLA","imp",4); op(0x69,"ADC","imm",2)
op(0x6A,"ROR","acc",2); op(0x6C,"JMP","ind",5); op(0x6D,"ADC","abs",4); op(0x6E,"ROR","abs",6)
op(0x70,"BVS","rel",2); op(0x71,"ADC","indy",5); op(0x75,"ADC","zpx",4); op(0x76,"ROR","zpx",6)
op(0x78,"SEI","imp",2); op(0x79,"ADC","absy",4); op(0x7D,"ADC","absx",4); op(0x7E,"ROR","absx",7)
op(0x81,"STA","indx",6); op(0x84,"STY","zp",3); op(0x85,"STA","zp",3); op(0x86,"STX","zp",3)
op(0x88,"DEY","imp",2); op(0x8A,"TXA","imp",2); op(0x8C,"STY","abs",4); op(0x8D,"STA","abs",4)
op(0x8E,"STX","abs",4); op(0x90,"BCC","rel",2); op(0x91,"STA","indy",6); op(0x94,"STY","zpx",4)
op(0x95,"STA","zpx",4); op(0x96,"STX","zpy",4); op(0x98,"TYA","imp",2); op(0x99,"STA","absy",5)
op(0x9A,"TXS","imp",2); op(0x9D,"STA","absx",5); op(0xA0,"LDY","imm",2); op(0xA1,"LDA","indx",6)
op(0xA2,"LDX","imm",2); op(0xA4,"LDY","zp",3); op(0xA5,"LDA","zp",3); op(0xA6,"LDX","zp",3)
op(0xA8,"TAY","imp",2); op(0xA9,"LDA","imm",2); op(0xAA,"TAX","imp",2); op(0xAC,"LDY","abs",4)
op(0xAD,"LDA","abs",4); op(0xAE,"LDX","abs",4); op(0xB0,"BCS","rel",2); op(0xB1,"LDA","indy",5)
op(0xB4,"LDY","zpx",4); op(0xB5,"LDA","zpx",4); op(0xB6,"LDX","zpy",4); op(0xB8,"CLV","imp",2)
op(0xB9,"LDA","absy",4); op(0xBA,"TSX","imp",2); op(0xBC,"LDY","absx",4); op(0xBD,"LDA","absx",4)
op(0xBE,"LDX","absy",4); op(0xC0,"CPY","imm",2); op(0xC1,"CMP","indx",6); op(0xC4,"CPY","zp",3)
op(0xC5,"CMP","zp",3); op(0xC6,"DEC","zp",5); op(0xC8,"INY","imp",2); op(0xC9,"CMP","imm",2)
op(0xCA,"DEX","imp",2); op(0xCC,"CPY","abs",4); op(0xCD,"CMP","abs",4); op(0xCE,"DEC","abs",6)
op(0xD0,"BNE","rel",2); op(0xD1,"CMP","indy",5); op(0xD5,"CMP","zpx",4); op(0xD6,"DEC","zpx",6)
op(0xD8,"CLD","imp",2); op(0xD9,"CMP","absy",4); op(0xDD,"CMP","absx",4); op(0xDE,"DEC","absx",7)
op(0xE0,"CPX","imm",2); op(0xE1,"SBC","indx",6); op(0xE4,"CPX","zp",3); op(0xE5,"SBC","zp",3)
op(0xE6,"INC","zp",5); op(0xE8,"INX","imp",2); op(0xE9,"SBC","imm",2); op(0xEA,"NOP","imp",2)
op(0xEC,"CPX","abs",4); op(0xED,"SBC","abs",4); op(0xEE,"INC","abs",6); op(0xF0,"BEQ","rel",2)
op(0xF1,"SBC","indy",5); op(0xF5,"SBC","zpx",4); op(0xF6,"INC","zpx",6); op(0xF8,"SED","imp",2)
op(0xF9,"SBC","absy",4); op(0xFD,"SBC","absx",4); op(0xFE,"INC","absx",7)

class MMC1:
    def __init__(self, prg, chr_):
        self.prg = prg  # bytes, 8x16KB
        self.chr = chr_  # bytes, 32x4KB
        self.shift = 0
        self.count = 0
        self.control = 0
        self.chr0 = 0
        self.chr1 = 0
        self.prg_bank = 0
        self.mirroring = 2  # vertical default
        self.log = []
    def write(self, addr, val, pc):
        if val & 0x80:
            # MMC1 reset: shift=0, PRG mode forced to 16KB fixed last bank at $C000
            # (NESdev: reset "inadvertently selects 16KB PRG bank size", $C000 fixed)
            self.shift = 0
            self.count = 0
            self.control = 0x0C  # 00001100: 16KB low switch ($8000), mirroring 0 (temp, real $1E follows)
            self.mirroring = 0
            return
        self.shift |= (val & 1) << self.count
        self.count += 1
        if self.count == 5:
            v = self.shift
            if 0x8000 <= addr <= 0x9FFF:
                self.control = v
                self.mirroring = v & 3
                self.log.append(f"MMC1 CTRL=${v:02X} mirror={self.mirroring} chr4k={(v>>4)&1} prg16k={(v>>3)&1} prglow={(v>>2)&1} @PC=${pc:04X}")
            elif 0xA000 <= addr <= 0xBFFF:
                self.chr0 = v
                self.log.append(f"MMC1 CHR0={v} @PC=${pc:04X}")
            elif 0xC000 <= addr <= 0xDFFF:
                self.chr1 = v
                self.log.append(f"MMC1 CHR1={v} @PC=${pc:04X}")
            elif 0xE000 <= addr <= 0xFFFF:
                self.prg_bank = v
                self.log.append(f"MMC1 PRG={v} @PC=${pc:04X}")
            self.shift = 0
            self.count = 0
    def read_prg(self, addr):
        # addr $8000-$FFFF
        ctrl = self.control
        prg16k = (ctrl >> 3) & 1
        prglow = (ctrl >> 2) & 1
        if prg16k == 0:
            # 32KB mode: bank even
            bank32 = self.prg_bank & ~1  # 0,2,4,6 (16KB bank numbers)
            off = bank32 * 16384 + (addr - 0x8000)
            return self.prg[off]
        else:
            if addr < 0xC000:
                # switchable low
                off = self.prg_bank * 16384 + (addr - 0x8000)
                return self.prg[off]
            else:
                # fixed last bank
                off = 7 * 16384 + (addr - 0xC000)
                return self.prg[off]
    def read_chr(self, addr):
        # addr $0000-$1FFF (PPU pattern)
        chr4k = (self.control >> 4) & 1
        if chr4k == 1:
            if addr < 0x1000:
                off = self.chr0 * 4096 + addr
            else:
                off = self.chr1 * 4096 + (addr - 0x1000)
            return self.chr[off]
        else:
            # 8KB mode: chr0 even bank
            bank8 = self.chr0 & ~1
            off = bank8 * 4096 + addr
            return self.chr[off]

class NES:
    def __init__(self, rom_path, input_script=None):
        data = open(rom_path,'rb').read()
        assert data[:4]==b'NES\x1a'
        prg_banks, chr_banks = data[4], data[5]
        self.prg = data[16:16+prg_banks*16384]
        self.chr = data[16+prg_banks*16384:16+prg_banks*16384+chr_banks*8192]
        self.mmc1 = MMC1(self.prg, self.chr)
        self.ram = bytearray(2048)
        self.vram_nt = bytearray(2048)  # nametable 2KB
        self.vram_pal = bytearray(32)
        self.oam = bytearray(256)
        # CPU
        self.A=0; self.X=0; self.Y=0; self.SP=0xFD
        self.P=0x24  # I=1, unused=1
        self.PC=0
        self.cycles=0
        self.frame=0
        self.frame_cycles=0
        self.FRAME_LEN=29780
        # PPU
        self.ppuctrl=0; self.ppumask=0; self.ppustatus=0
        self.oamaddr=0; self.ppuscroll_w=0; self.ppuaddr_w=0
        self.ppuaddr=0; self.vblank=False; self.nmi_pending=False
        self.oam_dma_stall=0
        # APU/controller
        self.apu_regs=bytearray(0x18)
        self.joy_strobe=[0,0]
        self.joy_latch=[0,0]
        self.joy_idx=[0,0]
        self.input_script=input_script or {}  # frame -> joy1 byte
        self.halted=False
        self.reset()
    def reset(self):
        self.PC=self.read16(0xFFFC)
        self.SP=0xFD; self.P=0x24
        self.cycles=0; self.frame=0; self.frame_cycles=0
        self.vblank=False
    # flags helpers
    def get_flag(self, f):
        return (self.P>>f)&1
    def set_flag(self, f, v):
        if v: self.P|=(1<<f)
        else: self.P&=~(1<<f)
    def set_nz(self, v):
        v&=0xFF
        self.set_flag(7, v&0x80)
        self.set_flag(1, v==0)
        return v
    def read16(self, addr):
        return self.read(addr) | (self.read((addr+1)&0xFFFF)<<8)
    def push(self, v):
        self.ram[0x100+self.SP]=v&0xFF
        self.SP=(self.SP-1)&0xFF
    def pull(self):
        self.SP=(self.SP+1)&0xFF
        return self.ram[0x100+self.SP]
    def read(self, addr):
        addr&=0xFFFF
        if addr<0x2000:
            return self.ram[addr&0x7FF]
        elif addr<0x4000:
            reg=addr&7
            if reg==2:
                v=self.ppustatus
                # clear vblank on read
                self.vblank=False
                self.ppustatus&=0x7F  # clear bit7? keep others
                self.ppuscroll_w=0; self.ppuaddr_w=0
                return v
            elif reg==4:
                return self.oam[self.oamaddr]
            elif reg==7:
                v=self.ppu_read_data()
                return v
            else:
                return 0
        elif addr<0x4018:
            if addr==0x4015:
                return 0x00
            elif addr==0x4016:
                return self.joy_read(0)
            elif addr==0x4017:
                return self.joy_read(1)
            else:
                return 0
        elif addr<0x8000:
            return 0
        else:
            return self.mmc1.read_prg(addr)
    def write(self, addr, val):
        addr&=0xFFFF; val&=0xFF
        if addr<0x2000:
            self.ram[addr&0x7FF]=val
        elif addr<0x4000:
            reg=addr&7
            if reg==0:
                self.ppuctrl=val
            elif reg==1:
                self.ppumask=val
            elif reg==3:
                self.oamaddr=val
            elif reg==4:
                self.oam[self.oamaddr]=val
                self.oamaddr=(self.oamaddr+1)&0xFF
            elif reg==5:
                self.ppuscroll_w^=1
            elif reg==6:
                if self.ppuaddr_w==0:
                    self.ppuaddr=(val&0x3F)<<8 | (self.ppuaddr&0xFF)
                    self.ppuaddr_w=1
                else:
                    self.ppuaddr=(self.ppuaddr&0xFF00)|val
                    self.ppuaddr_w=0
            elif reg==7:
                self.ppu_write_data(val)
        elif addr<0x4018:
            if addr==0x4014:
                # OAM DMA
                base=val<<8
                for i in range(256):
                    self.oam[(self.oamaddr+i)&0xFF]=self.read((base+i)&0xFFFF)
                self.oam_dma_stall=513
            elif addr==0x4016:
                self.joy_strobe[0]=val&1
                if val&1:
                    self.joy_latch[0]=self.current_joy(0)
                    self.joy_idx[0]=0
            elif addr==0x4017:
                self.joy_strobe[1]=val&1
                if val&1:
                    self.joy_latch[1]=self.current_joy(1)
                    self.joy_idx[1]=0
            else:
                if addr<0x4014:
                    self.apu_regs[addr-0x4000]=val
        elif addr<0x8000:
            pass
        else:
            self.mmc1.write(addr, val, self.PC)
    def current_joy(self, pad):
        if pad==0:
            return self.input_script.get(self.frame, 0)
        return 0
    def joy_read(self, pad):
        if self.joy_strobe[pad]:
            return self.joy_latch[pad]&1
        idx=self.joy_idx[pad]
        if idx>=8:
            return 1
        v=(self.joy_latch[pad]>>idx)&1
        self.joy_idx[pad]+=1
        return v
    def ppu_read_data(self):
        addr=self.ppuaddr&0x3FFF
        if addr<0x2000:
            v=self.mmc1.read_chr(addr)
            # buffered read for pattern? simplify direct
        elif addr<0x3000:
            # nametable with mirroring
            nt=self.nt_addr(addr)
            v=self.vram_nt[nt]
        elif addr<0x3F00:
            nt=self.nt_addr(addr-0x1000)
            v=self.vram_nt[nt]
        else:
            v=self.pal_read(addr)
        inc=32 if (self.ppuctrl&4) else 1
        self.ppuaddr=(self.ppuaddr+inc)&0x3FFF
        return v
    def ppu_write_data(self, val):
        addr=self.ppuaddr&0x3FFF
        if addr<0x2000:
            pass  # CHR ROM read-only
        elif addr<0x3000:
            self.vram_nt[self.nt_addr(addr)]=val
        elif addr<0x3F00:
            self.vram_nt[self.nt_addr(addr-0x1000)]=val
        else:
            self.pal_write(addr, val)
        inc=32 if (self.ppuctrl&4) else 1
        self.ppuaddr=(self.ppuaddr+inc)&0x3FFF
    def nt_addr(self, addr):
        # addr $2000-$2FFF, vertical mirroring: $2000=$2800, $2400=$2C00
        # horizontal: $2000=$2400, $2800=$2C00
        # MMC1 mirroring: 0=one-screen low,1=one-screen high,2=vertical,3=horizontal
        m=self.mmc1.mirroring
        nt=(addr>>10)&3  # 0:$2000,1:$2400,2:$2800,3:$2C00
        off=addr&0x3FF
        if m==0:
            return off
        elif m==1:
            return 0x400+off
        elif m==2:  # vertical: 0->0,1->1,2->0,3->1
            return (nt&1)*0x400+off
        else:  # horizontal: 0->0,1->0,2->1,3->1
            return ((nt>>1)&1)*0x400+off
    def pal_read(self, addr):
        a=addr&0x1F
        if a in (0x10,0x14,0x18,0x1C):
            a-=0x10
        return self.vram_pal[a]
    def pal_write(self, addr, val):
        a=addr&0x1F
        if a in (0x10,0x14,0x18,0x1C):
            a-=0x10
        self.vram_pal[a]=val
    def trigger_nmi(self):
        self.push((self.PC>>8)&0xFF)
        self.push(self.PC&0xFF)
        self.push(self.P & ~0x10)  # B=0 for NMI
        self.set_flag(2,1)  # I
        self.PC=self.read16(0xFFFA)
    def trigger_irq(self):
        self.push((self.PC>>8)&0xFF)
        self.push(self.PC&0xFF)
        self.push(self.P & ~0x10)
        self.set_flag(2,1)
        self.PC=self.read16(0xFFFE)
    def step(self):
        if self.oam_dma_stall>0:
            self.oam_dma_stall-=1
            self.cycles+=1
            self.advance_ppu(1)
            return
        pc0=self.PC
        opcode=self.read(self.PC)
        if opcode not in OPS:
            # illegal: treat as NOP 1 byte
            self.PC=(self.PC+1)&0xFFFF
            self.cycles+=2
            self.advance_ppu(2)
            return
        mnem,mode,cyc=OPS[opcode]
        # fetch operand
        # sizes
        size={ "imp":1,"acc":1,"imm":2,"zp":2,"zpx":2,"zpy":2,"abs":3,"absx":3,"absy":3,"ind":3,"indx":2,"indy":2,"rel":2 }[mode]
        b1=self.read((self.PC+1)&0xFFFF) if size>=2 else 0
        b2=self.read((self.PC+2)&0xFFFF) if size>=3 else 0
        imm=b1
        absaddr=b1|(b2<<8)
        next_pc=(self.PC+size)&0xFFFF
        # effective address
        ea=None
        if mode=="zp": ea=b1
        elif mode=="zpx": ea=(b1+self.X)&0xFF
        elif mode=="zpy": ea=(b1+self.Y)&0xFF
        elif mode=="abs": ea=absaddr
        elif mode=="absx": ea=(absaddr+self.X)&0xFFFF
        elif mode=="absy": ea=(absaddr+self.Y)&0xFFFF
        elif mode=="indx":
            zp=(b1+self.X)&0xFF
            ea=self.read(zp)|(self.read((zp+1)&0xFF)<<8)
        elif mode=="indy":
            zp=b1
            base=self.read(zp)|(self.read((zp+1)&0xFF)<<8)
            ea=(base+self.Y)&0xFFFF
        elif mode=="ind":
            lo=self.read(absaddr)
            hi_addr=(absaddr&0xFF00)|((absaddr+1)&0xFF)  # 6502 page wrap bug
            hi=self.read(hi_addr)
            ea=lo|(hi<<8)
        # execute
        # helpers for RMW
        def read_ea():
            if mode=="imm": return imm
            if mode=="acc": return self.A
            return self.read(ea)
        def write_ea(v):
            if mode=="acc":
                self.A=v&0xFF
            else:
                self.write(ea, v&0xFF)
        # branches
        if mode=="rel":
            off=b1
            if off>=128: off-=256
            cond=False
            if mnem=="BPL": cond=not self.get_flag(7)
            elif mnem=="BMI": cond=bool(self.get_flag(7))
            elif mnem=="BVC": cond=not self.get_flag(6)
            elif mnem=="BVS": cond=bool(self.get_flag(6))
            elif mnem=="BCC": cond=not self.get_flag(0)
            elif mnem=="BCS": cond=bool(self.get_flag(0))
            elif mnem=="BNE": cond=not self.get_flag(1)
            elif mnem=="BEQ": cond=bool(self.get_flag(1))
            if cond:
                next_pc=(next_pc+off)&0xFFFF
                cyc+=1  # branch taken
            self.PC=next_pc
            self.cycles+=cyc
            self.advance_ppu(cyc)
            return
        # jumps/calls
        if mnem=="JMP":
            self.PC=ea
            self.cycles+=cyc
            self.advance_ppu(cyc)
            return
        if mnem=="JSR":
            ret=(self.PC+2)&0xFFFF
            self.push((ret>>8)&0xFF)
            self.push(ret&0xFF)
            self.PC=absaddr
            self.cycles+=cyc
            self.advance_ppu(cyc)
            return
        if mnem=="RTS":
            lo=self.pull(); hi=self.pull()
            self.PC=(((hi<<8)|lo)+1)&0xFFFF
            self.cycles+=cyc
            self.advance_ppu(cyc)
            return
        if mnem=="RTI":
            self.P=self.pull()|0x20
            lo=self.pull(); hi=self.pull()
            self.PC=(hi<<8)|lo
            self.cycles+=cyc
            self.advance_ppu(cyc)
            return
        if mnem=="BRK":
            self.PC=(self.PC+2)&0xFFFF
            self.push((self.PC>>8)&0xFF)
            self.push(self.PC&0xFF)
            self.push(self.P|0x30)
            self.set_flag(2,1)
            self.PC=self.read16(0xFFFE)
            self.cycles+=cyc
            self.advance_ppu(cyc)
            return
        # ALU / load / store / etc.
        # For simplicity, implement via mnem dispatch
        if mnem=="LDA":
            self.A=self.set_nz(read_ea())
        elif mnem=="LDX":
            self.X=self.set_nz(read_ea())
        elif mnem=="LDY":
            self.Y=self.set_nz(read_ea())
        elif mnem=="STA":
            self.write(ea, self.A)
        elif mnem=="STX":
            self.write(ea, self.X)
        elif mnem=="STY":
            self.write(ea, self.Y)
        elif mnem=="TAX":
            self.X=self.set_nz(self.A)
        elif mnem=="TAY":
            self.Y=self.set_nz(self.A)
        elif mnem=="TXA":
            self.A=self.set_nz(self.X)
        elif mnem=="TYA":
            self.A=self.set_nz(self.Y)
        elif mnem=="TSX":
            self.X=self.set_nz(self.SP)
        elif mnem=="TXS":
            self.SP=self.X
        elif mnem=="INX":
            self.X=self.set_nz((self.X+1)&0xFF)
        elif mnem=="INY":
            self.Y=self.set_nz((self.Y+1)&0xFF)
        elif mnem=="DEX":
            self.X=self.set_nz((self.X-1)&0xFF)
        elif mnem=="DEY":
            self.Y=self.set_nz((self.Y-1)&0xFF)
        elif mnem=="INC":
            v=(read_ea()+1)&0xFF
            self.set_nz(v); write_ea(v)
        elif mnem=="DEC":
            v=(read_ea()-1)&0xFF
            self.set_nz(v); write_ea(v)
        elif mnem=="ADC":
            m=read_ea()
            # decimal mode ignored (CLD always in this game)
            res=self.A+m+self.get_flag(0)
            self.set_flag(6, ((self.A^res)&(m^res)&0x80)!=0)
            self.set_flag(0, res>0xFF)
            self.A=self.set_nz(res&0xFF)
        elif mnem=="SBC":
            m=read_ea()
            res=self.A-m-(1-self.get_flag(0))
            self.set_flag(6, ((self.A^res)&(~m^res)&0x80)!=0)
            self.set_flag(0, res>=0)
            self.A=self.set_nz(res&0xFF)
        elif mnem=="AND":
            self.A=self.set_nz(self.A & read_ea())
        elif mnem=="ORA":
            self.A=self.set_nz(self.A | read_ea())
        elif mnem=="EOR":
            self.A=self.set_nz(self.A ^ read_ea())
        elif mnem=="CMP":
            m=read_ea()
            res=(self.A-m)&0xFF
            self.set_flag(0, self.A>=m)
            self.set_nz(res)
        elif mnem=="CPX":
            m=read_ea()
            res=(self.X-m)&0xFF
            self.set_flag(0, self.X>=m)
            self.set_nz(res)
        elif mnem=="CPY":
            m=read_ea()
            res=(self.Y-m)&0xFF
            self.set_flag(0, self.Y>=m)
            self.set_nz(res)
        elif mnem=="BIT":
            m=read_ea()
            self.set_flag(7, m&0x80)
            self.set_flag(6, m&0x40)
            self.set_flag(1, (self.A & m)==0)
        elif mnem=="ASL":
            m=read_ea()
            self.set_flag(0, m&0x80)
            v=self.set_nz((m<<1)&0xFF)
            write_ea(v)
        elif mnem=="LSR":
            m=read_ea()
            self.set_flag(0, m&1)
            v=self.set_nz(m>>1)
            write_ea(v)
        elif mnem=="ROL":
            m=read_ea()
            c=self.get_flag(0)
            self.set_flag(0, m&0x80)
            v=self.set_nz(((m<<1)|c)&0xFF)
            write_ea(v)
        elif mnem=="ROR":
            m=read_ea()
            c=self.get_flag(0)
            self.set_flag(0, m&1)
            v=self.set_nz((m>>1)|(c<<7))
            write_ea(v)
        elif mnem=="PHA":
            self.push(self.A)
        elif mnem=="PHP":
            self.push(self.P|0x30)
        elif mnem=="PLA":
            self.A=self.set_nz(self.pull())
        elif mnem=="PLP":
            self.P=self.pull()|0x20
        elif mnem=="CLC":
            self.set_flag(0,0)
        elif mnem=="SEC":
            self.set_flag(0,1)
        elif mnem=="CLI":
            self.set_flag(2,0)
        elif mnem=="SEI":
            self.set_flag(2,1)
        elif mnem=="CLD":
            self.set_flag(3,0)
        elif mnem=="SED":
            self.set_flag(3,1)
        elif mnem=="CLV":
            self.set_flag(6,0)
        elif mnem=="NOP":
            pass
        else:
            pass
        self.PC=next_pc
        self.cycles+=cyc
        self.advance_ppu(cyc)
    def advance_ppu(self, cyc):
        self.frame_cycles+=cyc
        if self.frame_cycles>=self.FRAME_LEN:
            self.frame_cycles-=self.FRAME_LEN
            self.frame+=1
            # VBlank set at frame start
            was_vblank=self.vblank
            self.vblank=True
            self.ppustatus|=0x80
            if (self.ppuctrl&0x80) and not was_vblank:
                self.nmi_pending=True
        # NMI check (after instruction)
        if self.nmi_pending:
            self.nmi_pending=False
            self.trigger_nmi()
    def run_frames(self, nframes, log_cb=None):
        target=self.frame+nframes
        steps=0
        while self.frame<target and not self.halted:
            self.step()
            steps+=1
            if steps>5000000:
                print(f"WARN: step limit hit at frame {self.frame} PC=${self.PC:04X}")
                break
            if log_cb:
                log_cb(self)
        return steps

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--frames", type=int, default=600)
    ap.add_argument("--log", default=None)
    ap.add_argument("--trace-pc", action="store_true")
    args=ap.parse_args()
    # Input script: press Start (bit3=$08) at frame 120-130, A (bit0) at 200, etc.
    # Joy byte: bit0=A,1=B,2=Select,3=Start,4=Up,5=Down,6=Left,7=Right
    script={}
    for f in range(120,131):
        script[f]=0x08  # Start
    for f in range(300,310):
        script[f]=0x08
    nes=NES(args.rom, input_script=script)
    print(f"Reset PC=${nes.PC:04X} (expect $FFE0)")
    last_state=-1; last_chr=(-1,-1); last_prg=-1
    log_lines=[]
    def log_cb(n):
        # state
        st=n.ram[0x40]
        if st!=last_state:
            msg=f"frame {n.frame}: STATE $40 {last_state}->{st} PC=${n.PC:04X}"
            print(msg); log_lines.append(msg)
            # use nonlocal via closure hack: store in list
            log_cb.last_state=st
        # CHR banks $1D-$20
        chr0=n.ram[0x1D]; chr1=n.ram[0x1E]; chr0b=n.ram[0x1F]; chr1b=n.ram[0x20]
        if (chr0,chr1)!=(log_cb.last_chr if hasattr(log_cb,'last_chr') else (-1,-1)):
            msg=f"frame {n.frame}: CHR $1D/$1E={chr0}/{chr1} $1F/$20={chr0b}/{chr1b} PC=${n.PC:04X}"
            print(msg); log_lines.append(msg)
            log_cb.last_chr=(chr0,chr1)
        prg=n.ram[0x26]
        if prg!=(log_cb.last_prg if hasattr(log_cb,'last_prg') else -1):
            msg=f"frame {n.frame}: PRG $26={prg} PC=${n.PC:04X}"
            print(msg); log_lines.append(msg)
            log_cb.last_prg=prg
    log_cb.last_state=-1; log_cb.last_chr=(-1,-1); log_cb.last_prg=-1
    steps=nes.run_frames(args.frames, log_cb=log_cb)
    print(f"\nRan {steps} steps, {nes.frame} frames, cycles={nes.cycles}")
    print(f"Final: PC=${nes.PC:04X} A=${nes.A:02X} X=${nes.X:02X} Y=${nes.Y:02X} SP=${nes.SP:02X} P=${nes.P:02X}")
    print(f"RAM $40(state)={nes.ram[0x40]} $1D-$20={[nes.ram[i] for i in range(0x1D,0x21)]} $26(PRG)={nes.ram[0x26]} $0600={nes.ram[0x600]}")
    print(f"MMC1 log ({len(nes.mmc1.log)} entries):")
    for l in nes.mmc1.log[:100]:
        print(f"  {l}")
    if len(nes.mmc1.log)>100:
        print(f"  ... and {len(nes.mmc1.log)-100} more")
    if args.log:
        with open(args.log,'w') as f:
            f.write(f"frames={nes.frame} steps={steps} cycles={nes.cycles}\n")
            f.write(f"final PC=${nes.PC:04X} state={nes.ram[0x40]} CHR={[nes.ram[i] for i in range(0x1D,0x21)]} PRG={nes.ram[0x26]}\n")
            f.write("\n=== MMC1 log ===\n")
            for l in nes.mmc1.log:
                f.write(l+"\n")
            f.write("\n=== State/CHR/PRG changes ===\n")
            for l in log_lines:
                f.write(l+"\n")
        print(f"wrote {args.log}")

if __name__=="__main__":
    main()
