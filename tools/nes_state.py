#!/usr/bin/env python3
"""Parse FCEUmm libretro savestates and render the NES PPU.

A savestate written by ``retroshot`` contains everything the PPU needs:

* ``RAM``  (2 KiB)  CPU work RAM
* ``NTAR`` (2 KiB)  both physical nametables + attribute tables
* ``PRAM`` (32 B)   palette RAM (16 background, 16 sprite entries)
* ``SPRA`` (256 B)  OAM (y, tile, attr, x per sprite)
* ``PPUR`` (4 B)    PPUCTRL, PPUMASK, PPUSTATUS, open-bus latch
* ``XOFF`` (1 B)    horizontal scroll written through $2005
* ``DREG`` (4 B)    MMC1 shift registers (control, CHR0, CHR1, PRG)

The CHR pattern tables live in cartridge ROM, so this module also needs the
ROM image.  MMC1 bank selection comes from ``DREG`` exactly as the core's
mapper does it, which means a captured room can be re-rendered pixel-for-pixel
without the emulator running.

Only the subset of the format needed for asset extraction is implemented, but
unknown chunks/fields are skipped by their length fields rather than guessed.
"""
from __future__ import annotations

import struct
import wave
from dataclasses import dataclass
from pathlib import Path

SCREEN_W, SCREEN_H = 256, 240

# FCEUmm's first internally generated palette (palettes/palettes.h "palette").
# Used only as a fallback for colours that no captured frame exercised; the
# extraction pipeline normally learns the exact RGB values from emulator
# frames (see PaletteMap).
FCEUMM_CLASSIC_PALETTE = [
    (117, 117, 117), (36, 24, 142), (0, 0, 170), (69, 0, 158),
    (142, 0, 117), (170, 0, 16), (166, 0, 0), (125, 8, 0),
    (65, 44, 0), (0, 69, 0), (0, 81, 0), (0, 60, 20),
    (24, 60, 93), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (190, 190, 190), (0, 113, 239), (32, 56, 239), (130, 0, 243),
    (188, 0, 242), (228, 5, 165), (237, 29, 75), (232, 89, 25),
    (199, 145, 0), (122, 183, 0), (29, 199, 0), (0, 194, 65),
    (0, 172, 155), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (255, 255, 255), (60, 192, 255), (109, 151, 255), (188, 131, 255),
    (240, 125, 255), (255, 129, 210), (255, 147, 148), (255, 179, 98),
    (255, 220, 74), (206, 255, 69), (126, 255, 79), (89, 255, 145),
    (71, 255, 213), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (255, 255, 255), (171, 226, 255), (190, 205, 255), (232, 195, 255),
    (255, 191, 255), (255, 194, 234), (255, 199, 199), (255, 209, 168),
    (255, 231, 154), (240, 255, 150), (207, 255, 154), (190, 255, 198),
    (183, 255, 231), (0, 0, 0), (0, 0, 0), (0, 0, 0),
]


def _tagged_records(payload: bytes):
    """Yield (desc, data) for each SFORMAT record in a chunk payload."""
    pos = 0
    n = len(payload)
    while pos + 8 <= n:
        desc = payload[pos:pos + 4].rstrip(b"\0").decode("latin1")
        size = struct.unpack_from("<I", payload, pos + 4)[0]
        start = pos + 8
        end = start + size
        if end > n:  # malformed tail: stop rather than invent data
            return
        yield desc, payload[start:end]
        pos = end


def parse_fcs(path: str | Path) -> dict[str, bytes]:
    """Return every SFORMAT field in a FCEUmm state, keyed by its 4-char tag.

    Later duplicates win, which matches the module layout used by the core.
    """
    data = Path(path).read_bytes()
    if data[:4] != b"FCS\xff":
        raise ValueError(f"{path}: not an FCEUmm savestate (bad magic)")
    if len(data) < 16:
        raise ValueError(f"{path}: truncated savestate header")
    pos = 16
    fields: dict[str, bytes] = {}
    while pos + 5 <= len(data):
        size = struct.unpack_from("<I", data, pos + 1)[0]
        body_start = pos + 5
        body_end = body_start + size
        if body_end > len(data):
            break
        for desc, payload in _tagged_records(data[body_start:body_end]):
            fields[desc] = payload
        pos = body_end
    return fields


@dataclass
class NesState:
    fields: dict[str, bytes]
    rom: bytes

    # ---- raw fields -----------------------------------------------------
    @property
    def ram(self) -> bytes:
        return self.fields["RAM"]

    @property
    def ntar(self) -> bytes:
        return self.fields["NTAR"]

    @property
    def pram(self) -> bytes:
        return self.fields["PRAM"]

    @property
    def oam(self) -> bytes:
        return self.fields["SPRA"]

    @property
    def ppuctrl(self) -> int:
        return self.fields["PPUR"][0]

    @property
    def ppumask(self) -> int:
        return self.fields["PPUR"][1]

    @property
    def xoff(self) -> int:
        return self.fields["XOFF"][0]

    @property
    def dregs(self) -> bytes:
        return self.fields.get("DREG", b"\x00\x00\x00\x00")

    # ---- CHR banking ----------------------------------------------------
    @property
    def chr_mode_4k(self) -> bool:
        return bool(self.dregs[0] & 0x10)

    def _bank_for_slot(self, slot: int) -> int:
        """4 KiB CHR bank mapped at VRAM $0000 (slot 0) or $1000 (slot 1)."""
        if self.chr_mode_4k:
            return self.dregs[1 + slot]
        # 8 KiB mode: DRegs[1] & ~1 selects the pair, slot chooses the half.
        return (self.dregs[1] & ~1) | slot

    @property
    def chr_rom(self) -> bytes:
        if len(self.rom) < 16:
            raise ValueError("ROM too short for iNES header")
        prg = self.rom[4] * 16384
        chr_size = self.rom[5] * 8192
        start = 16 + prg
        data = self.rom[start:start + chr_size]
        if not data:
            raise ValueError("ROM has no CHR ROM; CHR RAM games are unsupported here")
        return data

    def chr_bank(self, address: int) -> bytes:
        """Bytes for the 4 KiB CHR bank that covers PPU ``address``."""
        data = self.chr_rom
        bank = self._bank_for_slot((address >> 12) & 1)
        start = bank * 4096
        if start + 4096 > len(data):
            raise ValueError(f"CHR bank {bank} outside {len(data)} bytes of CHR ROM")
        return data[start:start + 4096]

    def chr_pattern_slot(self, address: int) -> int:
        return (address >> 12) & 1

    # ---- nametable helpers ---------------------------------------------
    def nametable(self, base: int) -> bytes:
        """Return a 1024-byte nametable page (base 0..3) honouring mirroring.

        FCEUmm maps the four logical name tables onto 2 KiB of physical VRAM
        according to MMC1 control bits 0-1.
        """
        mirror = self.dregs[0] & 3
        if mirror == 2:      # vertical: $2000=$2800, $2400=$2C00
            phys = base & 1
        elif mirror == 3:    # horizontal: $2000=$2400, $2800=$2C00
            phys = base >> 1
        elif mirror == 0:    # one-screen lower
            phys = 0
        elif mirror == 1:    # one-screen upper
            phys = 1
        else:
            phys = 0
        return self.ntar[phys * 0x400:(phys + 1) * 0x400]

    def scroll(self) -> tuple[int, int, int]:
        """Best-effort (coarse_x, fine_x, coarse_y) from PPU state.

        MMC1 games typically rewrite $2005 every frame; the core latches X in
        XOFF and leaves Y in the temporary address register.  For room-based
        screens both are zero, which is the common case here.
        """
        taddr = int.from_bytes(self.fields.get("TADD", b"\0\0"), "little")
        return (taddr & 0x1F, self.xoff, (taddr >> 5) & 0x1F)

    # ---- rendering ------------------------------------------------------
    def tile_pixels(self, pattern_slot: int, tile: int) -> list[list[int]]:
        """Return 8 rows of 2-bit pixel values for one tile."""
        if pattern_slot == 0:
            base = 0
        else:
            base = 0x1000
        bank = self.chr_bank(base)
        off = (tile * 16) & 0x0FFF
        rows = []
        for y in range(8):
            lo = bank[off + y]
            hi = bank[off + y + 8]
            row = []
            for x in range(7, -1, -1):
                row.append(((lo >> x) & 1) | (((hi >> x) & 1) << 1))
            rows.append(row)
        return rows

    def frame_indices(self, with_sprites: bool = True):
        """Render the visible frame.

        Returns ``(indices, sprite_mask, bg_pixel)`` where

        * ``indices[y][x]`` is the NES colour index that the PPU displayed,
        * ``sprite_mask[y][x]`` is True where a sprite pixel won the priority
          test (so the layer can be exported separately),
        * ``bg_pixel[y][x]`` is the 2-bit background pixel value (0 = colour 0),
          which callers can use for collision/background separation.

        Every pixel gets an index: with the background enabled, colour 0 of a
        tile shows the universal backdrop, exactly as the hardware does.
        """
        ctrl, mask = self.ppuctrl, self.ppumask
        base_nt = ctrl & 3
        bg_slot = 1 if (ctrl & 0x10) else 0
        spr_slot = 1 if (ctrl & 0x08) else 0
        coarse_x, fine_x, coarse_y = self.scroll()
        pram = self.pram
        backdrop = pram[0] & 0x3F

        indices = [[backdrop for _ in range(SCREEN_W)] for _ in range(SCREEN_H)]
        sprite_mask = [[False] * SCREEN_W for _ in range(SCREEN_H)]
        bg_pixel = [[0] * SCREEN_W for _ in range(SCREEN_H)]

        if mask & 0x08:  # background enabled
            tile_cache: dict[int, list[list[int]]] = {}
            # Cache the 32x30 tile/palette/attribute triplets for the page.
            for row in range(30):
                nt_page = self.nametable((base_nt + (row // 30)) & 3)
            nt_cache: dict[int, bytes] = {}

            def page_for(col: int) -> bytes:
                # Nametable pages wrap at 32 columns; honour the base table.
                page_index = (base_nt + (col // 32)) & 3
                if page_index not in nt_cache:
                    nt_cache[page_index] = self.nametable(page_index)
                return nt_cache[page_index]

            for py in range(SCREEN_H):
                sy = py + coarse_y * 8
                row = sy // 8
                fy = sy % 8
                for px in range(SCREEN_W):
                    if px < 8 and not (mask & 0x02):
                        continue  # leftmost 8 background pixels are masked
                    sx = px + coarse_x * 8 + fine_x
                    col = sx // 8
                    fx = sx % 8
                    nt = page_for(col)
                    cell = (row % 30) * 32 + (col % 32)
                    tile = nt[cell]
                    if tile not in tile_cache:
                        tile_cache[tile] = self.tile_pixels(bg_slot, tile)
                    pix = tile_cache[tile][fy][fx]
                    bg_pixel[py][px] = pix
                    attr = nt[0x3C0 + ((row % 30) // 4) * 8 + ((col % 32) // 4)]
                    shift = (((row % 30) % 4) // 2) * 4 + (((col % 32) % 4) // 2) * 2
                    pal = (attr >> shift) & 3
                    indices[py][px] = (pram[pal * 4 + pix] if pix else backdrop) & 0x3F

        if with_sprites and (mask & 0x10):
            oam = self.oam
            spr_cache: dict[int, list[list[int]]] = {}
            height = 16 if (ctrl & 0x20) else 8
            for i in range(64):
                sy, tile, attr, sx = oam[i * 4:i * 4 + 4]
                top = sy + 1  # OAM y is one less than the displayed row
                if top >= SCREEN_H:
                    continue
                for dy in range(height):
                    y = top + dy
                    if not (0 <= y < SCREEN_H):
                        continue
                    t = (tile & 0xFE) + (dy // 8) if height == 16 else tile
                    fy_src = (height - 1 - dy) % 8 if (attr & 0x80) else dy % 8
                    if t not in spr_cache:
                        spr_cache[t] = self.tile_pixels(spr_slot, t)
                    pattern = spr_cache[t][fy_src]
                    for dx in range(8):
                        x = sx + dx
                        if not (0 <= x < SCREEN_W):
                            continue
                        if x < 8 and not (mask & 0x04):
                            continue  # leftmost sprites are masked
                        pix = pattern[7 - dx] if (attr & 0x40) else pattern[dx]
                        if not pix:
                            continue
                        if (attr & 0x20) and bg_pixel[y][x]:  # behind non-zero BG
                            continue
                        pal = 4 + (attr & 3)
                        indices[y][x] = pram[pal * 4 + pix] & 0x3F
                        sprite_mask[y][x] = True
        return indices, sprite_mask, bg_pixel

    def colour_indices(self):
        """Backwards-compatible (indices, opaque) pair used by validation."""
        indices, sprite_mask, bg_pixel = self.frame_indices(with_sprites=True)
        ctrl, mask = self.ppuctrl, self.ppumask
        bg_enabled = bool(mask & 0x08)
        opaque = [[bg_enabled or sprite_mask[y][x] for x in range(SCREEN_W)]
                  for y in range(SCREEN_H)]
        return indices, opaque

    def render_rgb(self, palette: list[tuple[int, int, int]] | None = None,
                   background: tuple[int, int, int] = (0, 0, 0),
                   sprites: bool = True):
        """Render to a flat list of RGB pixels, row-major."""
        palette = palette or FCEUMM_CLASSIC_PALETTE
        indices, _, _ = self.frame_indices(with_sprites=sprites)
        return [palette[indices[y][x] & 0x3F]
                for y in range(SCREEN_H) for x in range(SCREEN_W)]

    def render_page_rgb(self, palette=None, page: int | None = None,
                        sprites: bool = False):
        """Render one nametable page as a 256x240 image with no scroll.

        This is the stable, camera-independent view used to stitch wide levels:
        it always starts at nametable tile (0,0) regardless of where the camera
        happened to be when the state was captured.
        """
        palette = palette or FCEUMM_CLASSIC_PALETTE
        if page is None:
            page = self.ppuctrl & 3
        nt = self.nametable(page)
        bg_slot = 1 if (self.ppuctrl & 0x10) else 0
        pram = self.pram
        backdrop = pram[0] & 0x3F
        cache: dict[int, list[list[int]]] = {}
        pixels = []
        for y in range(240):
            row, fy = y // 8, y % 8
            for x in range(256):
                col, fx = x // 8, x % 8
                tile = nt[row * 32 + col]
                if tile not in cache:
                    cache[tile] = self.tile_pixels(bg_slot, tile)
                attr = nt[0x3C0 + (row // 4) * 8 + (col // 4)]
                shift = ((row % 4) // 2) * 4 + ((col % 4) // 2) * 2
                pal = (attr >> shift) & 3
                v = cache[tile][fy][fx]
                pixels.append(palette[(pram[pal * 4 + v] if v else backdrop) & 0x3F])
        return pixels

    def sprite_mask(self):
        _, sprite_mask, _ = self.frame_indices(with_sprites=True)
        return sprite_mask

    # ---- PPM capture comparison ----------------------------------------
    def compare_with_ppm(self, ppm_path: str | Path) -> dict:
        """Check rendered colour indices against a captured frame.

        Returns statistics describing, for each NES colour index, which RGB
        values the emulator produced.  A correct render has exactly one RGB
        value per index and no index that mixes several.
        """
        from PIL import Image
        idx, opaque = self.colour_indices()
        frame = Image.open(ppm_path).convert("RGB")
        if frame.size != (SCREEN_W, SCREEN_H):
            raise ValueError(f"unexpected frame size {frame.size}")
        fpx = frame.load()
        seen: dict[int, set] = {}
        conflicts = 0
        hidden = 0
        for y in range(SCREEN_H):
            for x in range(SCREEN_W):
                if not opaque[y][x]:
                    hidden += 1
                    continue
                colour = idx[y][x] & 0x3F
                seen.setdefault(colour, set()).add(fpx[x, y])
        for colour, vals in seen.items():
            if len(vals) > 1:
                conflicts += 1
        return {
            "indices_seen": len(seen),
            "indices_conflicting": conflicts,
            "transparent_pixels": hidden,
            "index_to_rgb": {k: sorted(v) for k, v in sorted(seen.items())},
        }


def load_state(state_path: str | Path, rom_path: str | Path) -> NesState:
    return NesState(parse_fcs(state_path), Path(rom_path).read_bytes())


def read_ppm(path: str | Path):
    from PIL import Image
    return Image.open(path).convert("RGB")


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser(description="dump fields / verify a savestate render")
    ap.add_argument("state")
    ap.add_argument("--rom", required=True)
    ap.add_argument("--frame", help="PPM capture taken at the same emulator frame")
    ap.add_argument("--png", help="write the re-rendered screen here")
    args = ap.parse_args()

    st = load_state(args.state, args.rom)
    print("fields:", sorted(st.fields))
    print("PPUCTRL=%02X PPUMASK=%02X XOFF=%d DREG=%s" % (
        st.ppuctrl, st.ppumask, st.xoff, st.dregs.hex()))
    print("scroll(coarse_x, fine_x, coarse_y) =", st.scroll())
    if args.frame:
        report = st.compare_with_ppm(args.frame)
        print(json.dumps({k: v for k, v in report.items() if k != "index_to_rgb"}, indent=2))
        for colour, vals in report["index_to_rgb"].items():
            print(f"  idx {colour:02X}: {len(vals)} rgb value(s) {vals[:4]}")
    if args.png:
        from PIL import Image
        pix = st.render_rgb()
        im = Image.new("RGB", (SCREEN_W, SCREEN_H))
        im.putdata(pix)
        im.save(args.png)
        print("wrote", args.png)
