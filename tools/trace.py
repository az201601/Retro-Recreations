"""Reader for the per-frame trace produced by tools/nes/capture.

Record layout (little endian, 4400 bytes):
  int32 frame
  u8 chr_lo, chr_hi, prg_lo, prg_hi, chr_mode, prg_mode, spr_page, bg_page, long_sprites
  u8 pad[3]
  u8 palette[32]
  u8 oam[256]
  u8 ram[2048]     CPU RAM
  u8 vram[2048]    PPU name tables
  u8 pad[3]        PPU v register (lo, hi) + fine X
"""
import struct

REC = 4400
_FMT = "<i9B3s32s256s2048s2048s"
assert struct.calcsize(_FMT) == REC


class Rec:
    __slots__ = ("frame", "chr_lo", "chr_hi", "prg_lo", "prg_hi", "chr_mode",
                 "prg_mode", "spr_page", "bg_page", "long_sprites", "palette",
                 "oam", "ram", "pad", "vram")

    @property
    def vram_addr(self):
        return self.pad[0] | (self.pad[1] << 8)

    @property
    def fine_x(self):
        return self.pad[2]

    @property
    def sprites(self):
        """List of dicts for the 64 OAM entries (y already +1 like the PPU)."""
        out = []
        for i in range(64):
            y, t, a, x = self.oam[i * 4:i * 4 + 4]
            out.append(dict(slot=i, y=(y + 1) & 0xFF, tile=t, attr=a, x=x,
                            pal=(a & 3) + 4, prio=(a >> 5) & 1,
                            flipx=bool(a & 0x40), flipy=bool(a & 0x80)))
        return out

    @property
    def visible_sprites(self):
        return [s for s in self.sprites if s["y"] < 240]


def load(path):
    data = open(path, "rb").read()
    n = len(data) // REC
    recs = []
    for i in range(n):
        v = struct.unpack_from(_FMT, data, i * REC)
        r = Rec()
        (r.frame, r.chr_lo, r.chr_hi, r.prg_lo, r.prg_hi, r.chr_mode, r.prg_mode,
         r.spr_page, r.bg_page, r.long_sprites, r.pad, r.palette, r.oam, r.ram,
         r.vram) = v
        recs.append(r)
    return recs
