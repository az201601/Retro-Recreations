#!/usr/bin/env python3
"""Decode the pinned fceumm asset-capture PPU snapshot into pixel-exact NES tiles.

The core patch exposes 0xFCE1 in retro_get_memory_data; this is *not* the
standard libretro VIDEO_RAM block. These values come from the running ROM,
including mapper-selected CHR pages and the actual fceumm RGB palette.
In this game BG uses pattern table 0 and 8x8 sprites use pattern table 1.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from PIL import Image

CAPTURE_SIZE = 0x31E0
PATTERN_SIZE = 0x2000
NT_OFFSET, NT_SIZE = 0x2000, 0x1000
PALETTE_OFFSET, OAM_OFFSET, RGB_OFFSET = 0x3000, 0x3020, 0x3120


@dataclass(frozen=True)
class PpuCapture:
    pattern: bytes
    nametable: bytes
    nes_palette: bytes
    oam: bytes
    rgb_palette: tuple[tuple[int, int, int], ...]

    @classmethod
    def from_bytes(cls, data: bytes) -> "PpuCapture":
        if len(data) != CAPTURE_SIZE:
            raise ValueError(f"expected {CAPTURE_SIZE:#x} PPU bytes, got {len(data):#x}")
        rgb = data[RGB_OFFSET:]
        return cls(data[:PATTERN_SIZE], data[NT_OFFSET:PALETTE_OFFSET],
                   data[PALETTE_OFFSET:OAM_OFFSET], data[OAM_OFFSET:RGB_OFFSET],
                   tuple(tuple(rgb[i:i + 3]) for i in range(0, 192, 3)))

    @classmethod
    def from_file(cls, filename: Path | str) -> "PpuCapture":
        return cls.from_bytes(Path(filename).read_bytes())

    def bg_at(self, world_x: int, world_y: int) -> tuple[int, int] | None:
        """Return (CHR tile, BG palette number) at an unscrolled world pixel.

        A nametable covers 256x240 pixels in each 256x256 scrolling page; the
        last 16 scanlines are non-visual and may cross into the next page.
        Returns None in that space rather than assuming scenery was blank.
        """
        page = (world_x // 256) % 2 + 2 * ((world_y // 256) % 2)
        tile_x, tile_y = (world_x % 256) // 8, (world_y % 256) // 8
        if tile_y >= 30:
            return None
        nt = self.nametable[page * 1024:(page + 1) * 1024]
        index = nt[tile_y * 32 + tile_x]
        attr = nt[0x3C0 + (tile_y // 4) * 8 + (tile_x // 4)]
        quadrant = (tile_x // 2 % 2) + 2 * (tile_y // 2 % 2)
        return index, (attr >> (2 * quadrant)) & 3

    def pixel_color(self, tile_id: int, palette: int, x: int, y: int,
                    *, sprite: bool = False) -> tuple[int, int, int] | None:
        """Color at a pixel of an 8x8 CHR tile; sprite index zero is transparent."""
        addr = (0x1000 if sprite else 0) + tile_id * 16 + y
        value = ((self.pattern[addr] >> (7 - x)) & 1) | (((self.pattern[addr + 8] >> (7 - x)) & 1) << 1)
        if sprite and value == 0:
            return None
        pal_idx = (0x10 if sprite else 0) + (palette & 3) * 4 + value
        # For BG, zero is the universal color (not palette-specific index 0).
        if not sprite and not value:
            pal_idx = 0
        return self.rgb_palette[self.nes_palette[pal_idx] & 0x3F]

    def tile_image(self, tile_id: int, palette: int, *, sprite: bool = False) -> Image.Image:
        img = Image.new("RGBA", (8, 8))
        for y in range(8):
            for x in range(8):
                color = self.pixel_color(tile_id, palette, x, y, sprite=sprite)
                if color is not None:
                    img.putpixel((x, y), (*color, 255))
        return img

    def bg_image(self, scroll_x: int, scroll_y: int, *, height: int = 208) -> Image.Image:
        """Render captured BG alone for visual verification (ignores split HUD).

        Return transparent pixels where NES nametable attribute bytes occupy
        the last 16 rows of each 256px page. Those rows are undocumented by a
        static snapshot and require a nearby frame or room map to reconstruct.
        """
        img = Image.new("RGBA", (256, height))
        cache: dict[tuple[int, int], Image.Image] = {}
        for y in range(height):
            wy = scroll_y + y
            for x in range(256):
                wx = scroll_x + x
                info = self.bg_at(wx, wy)
                if info is None:
                    continue
                if info not in cache:
                    cache[info] = self.tile_image(*info)
                img.putpixel((x, y), cache[info].getpixel((wx % 8, wy % 8)))
        return img

    def oam_sprites(self) -> list[tuple[int, int, int, int, int]]:
        """(OAM index, screen x, screen y, CHR tile, attributes), 8x8 mode.

        On the NES the first visible scanline is OAM y+1. Sprite 0 wins over
        sprite 1 on overlapping pixels; compose in reverse index order.
        """
        sprites = []
        for i in range(64):
            y, tile, attr, x = self.oam[i * 4:i * 4 + 4]
            if y < 239:
                sprites.append((i, x, y + 1, tile, attr))
        return sprites

    def sprites_image(self, *, canvas: tuple[int, int] = (256, 240),
                      indices: set[int] | None = None) -> Image.Image:
        """Reconstruct the 8x8 OAM sprite layer as transparent RGBA."""
        img = Image.new("RGBA", canvas)
        cache: dict[tuple[int, int], Image.Image] = {}
        for idx, x, y, tile, attr in reversed(self.oam_sprites()):
            if indices is not None and idx not in indices:
                continue
            key = (tile, attr & 3)
            if key not in cache:
                cache[key] = self.tile_image(tile, attr & 3, sprite=True)
            spr = cache[key]
            if attr & 0x40:
                spr = spr.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            if attr & 0x80:
                spr = spr.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            img.alpha_composite(spr, (x, y))
        return img


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("snapshot", type=Path)
    ap.add_argument("--sprites", type=Path, help="export transparent sprite-only PNG")
    ap.add_argument("--background", type=Path, help="export background PNG")
    ap.add_argument("--scroll-x", type=lambda v: int(v, 0), default=0)
    ap.add_argument("--scroll-y", type=lambda v: int(v, 0), default=0)
    args = ap.parse_args()
    ppu = PpuCapture.from_file(args.snapshot)
    if args.sprites:
        ppu.sprites_image().save(args.sprites)
    if args.background:
        ppu.bg_image(args.scroll_x, args.scroll_y).save(args.background)


if __name__ == "__main__":
    main()
