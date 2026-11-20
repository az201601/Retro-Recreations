#!/usr/bin/env python3
"""
extract_gms_assets.py - generate Nestopia-palette-exact PNGs for gms/Gradius.gmx.

Every pixel in every generated PNG comes strictly from oracle/palette/nestopia.pal
(plus alpha=0 transparent pixels in sprite sheets).  No off-palette colours from
earlier FCEUX/2C02G rips are used.

Requirements:
  - Gradius (USA).nes
  - oracle/palette/nestopia.pal
  - emulator/out/nesrun + emulator/out/cores/nestopia_libretro.so +
    oracle/inputs/boot_to_game.txt (used to capture live PPUNTA/PPUPAL for the
    title screen and stage 1 starfield/HUD layout)
"""

from __future__ import annotations

import os
import struct
import subprocess
import tempfile
import zlib

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM_PATH = os.path.join(REPO_ROOT, "Gradius (USA).nes")
PAL_PATH = os.path.join(REPO_ROOT, "oracle", "palette", "nestopia.pal")
NESRUN_PATH = os.path.join(REPO_ROOT, "emulator", "out", "nesrun")
CORE_PATH = os.path.join(REPO_ROOT, "emulator", "out", "cores", "nestopia_libretro.so")
INPUT_PATH = os.path.join(REPO_ROOT, "oracle", "inputs", "boot_to_game.txt")
GMS_DIR = os.path.join(REPO_ROOT, "gms", "Gradius.gmx")


def load_nestopia_palette() -> list[tuple[int, int, int]]:
    data = open(PAL_PATH, "rb").read()
    if len(data) < 192:
        raise RuntimeError(f"Expected >=192 bytes in {PAL_PATH}, got {len(data)}")
    return [(data[i * 3], data[i * 3 + 1], data[i * 3 + 2]) for i in range(64)]


def write_png_rgba(path: str, w: int, h: int, rgba_rows: list[bytes]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    raw = b"".join(b"\x00" + row for row in rgba_rows)

    def chunk(tag: bytes, body: bytes) -> bytes:
        crc = zlib.crc32(tag + body) & 0xFFFFFFFF
        return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    idat = zlib.compress(raw, 9)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def decode_title_from_rom(prg: bytes) -> tuple[list[int], list[int]]:
    """Decode the Title Screen nametable ($8895 -> $8C8C) and palette (cmd 6)
    directly from Gradius (USA).nes, keeping ONLY the GRADIUS logo (ty=8..12)
    and PLAY SELECT / 1 PLAYER / 2 PLAYERS (ty=14,17,19) while stripping the
    KONAMI logo (ty=4..6) and copyright block (ty=21..27).
    """
    def rb(a: int) -> int:
        return prg[a - 0x8000]

    def rw(a: int) -> int:
        return rb(a) | (rb(a + 1) << 8)

    tbl = rw(0x8895)
    nt: list[int] = []
    for i in range(6):
        p = rw(tbl + i * 2)
        while True:
            b = rb(p)
            p += 1
            if b == 0x39:
                break
            if b == 0x34:
                cnt = rb(p)
                p += 1
                val = rb(p)
                p += 1
                nt.extend([val] * (256 if cnt == 0 else cnt))
            else:
                nt.append(b)
    if len(nt) != 1024:
        raise RuntimeError(f"Expected 1024-byte title nametable, got {len(nt)}")

    # Overlay sub_85E8 commands: 3 (PLAY SELECT), 1 (1 PLAYER), 2 (2 PLAYERS)
    for cmd in (3, 1, 2):
        p = rw(0x864E + cmd * 2)
        hi, lo = rb(p), rb(p + 1)
        p += 2
        addr = ((hi << 8) | lo) - 0x2000
        while True:
            b = rb(p)
            p += 1
            if b in (0xFE, 0xFF):
                break
            nt[addr] = b
            addr += 1

    # Strip KONAMI logo (ty < 8) and copyright notice (ty >= 21)
    for ty in list(range(0, 8)) + list(range(21, 30)):
        for tx in range(32):
            nt[ty * 32 + tx] = 0

    # Decode Title BG+SPR palette from sub_85E8 cmd 6 ($87D8)
    p = rw(0x864E + 6 * 2)
    if rb(p) != 0x3F or rb(p + 1) != 0x00:
        raise RuntimeError("Unexpected cmd 6 palette header in ROM")
    pal32 = [rb(p + 2 + i) for i in range(32)]
    return nt, pal32


def capture_ppu_frames() -> list[tuple[list[int], list[int]]]:
    """Capture live PPUNTA + PPUPAL at frame 300 (stage 1)."""
    with tempfile.TemporaryDirectory() as tmp:
        watch_out = os.path.join(tmp, "ppu.txt")
        cmd = [
            NESRUN_PATH,
            "--core", CORE_PATH,
            "--rom", ROM_PATH,
            "--frames", "305",
            "--input", INPUT_PATH,
            "--watch", "PPUNTA:0:2048",
            "--watch", "PPUPAL:0:32",
            "--watch-out", watch_out,
            "--quiet",
        ]
        subprocess.run(cmd, check=True, cwd=REPO_ROOT)
        lines = open(watch_out).read().splitlines()

        def parse(f: int) -> tuple[list[int], list[int]]:
            vals = [int(x, 16) for x in lines[f].split()[2:]]
            return vals[:2048], vals[2048:2080]

        return [parse(300)]


def decode_chr_tile(chr_rom: bytes, bank: int, table_offset: int, tile_idx: int) -> list[list[int]]:
    base = bank * 8192 + table_offset + tile_idx * 16
    out = []
    for y in range(8):
        p0 = chr_rom[base + y]
        p1 = chr_rom[base + 8 + y]
        out.append([((p0 >> (7 - x)) & 1) | (((p1 >> (7 - x)) & 1) << 1) for x in range(8)])
    return out


def render_bg_nt(
    nes_pal: list[tuple[int, int, int]],
    chr_rom: bytes,
    bank: int,
    nta: list[int],
    pal32: list[int],
    y_start: int = 0,
    y_end: int = 240,
    transparent_zero: bool = False,
) -> list[bytes]:
    bg_univ = nes_pal[pal32[0] & 0x3F]
    rows = []
    for y in range(y_start, y_end):
        ty, py = y >> 3, y & 7
        row = bytearray()
        for tx in range(32):
            tid = nta[ty * 32 + tx]
            attr = nta[960 + (ty // 4) * 8 + (tx // 4)]
            shift = ((ty & 2) << 1) | (tx & 2)
            pidx = (attr >> shift) & 3
            tile_px = decode_chr_tile(chr_rom, bank, 0x0000, tid)[py]
            for c in tile_px:
                if c == 0:
                    r, g, b = bg_univ
                    a = 0 if transparent_zero else 255
                else:
                    r, g, b = nes_pal[pal32[pidx * 4 + c] & 0x3F]
                    a = 255
                row.extend((r, g, b, a))
        rows.append(bytes(row))
    return rows


def render_metasprite(
    nes_pal: list[tuple[int, int, int]],
    prg: bytes,
    chr_rom: bytes,
    bank: int,
    sid: int,
    spr_pal16: list[int],
    attr_or: int = 0,
) -> tuple[int, int, int, int, list[bytes]]:
    """Render metasprite ID `sid` from table $8D9E/$8E9E into tight RGBA image."""
    def rb(a: int) -> int:
        return prg[a - 0x8000]

    def rw(a: int) -> int:
        return rb(a) | (rb(a + 1) << 8)

    if sid >= 0x80:
        ptr = rw(0x8E9E + (sid - 0x80) * 2)
    else:
        ptr = rw(0x8D9E + sid * 2)

    cnt = rb(ptr)
    entries = []
    for k in range(cnt):
        dy = rb(ptr + 1 + k * 4)
        dy = dy - 256 if dy >= 128 else dy
        tile = rb(ptr + 2 + k * 4)
        attr = rb(ptr + 3 + k * 4) | attr_or
        dx = rb(ptr + 4 + k * 4)
        dx = dx - 256 if dx >= 128 else dx
        entries.append((dy, tile, attr, dx))

    min_x = min(e[3] for e in entries)
    max_x = max(e[3] + 8 for e in entries)
    min_y = min(e[0] for e in entries)
    max_y = max(e[0] + 16 for e in entries)
    w = max_x - min_x
    h = max_y - min_y
    xorig = -min_x
    yorig = -min_y

    buf = [[(0, 0, 0, 0) for _ in range(w)] for _ in range(h)]
    # Draw in reverse OAM order so earlier sprites win on overlap (NES priority)
    for dy, tile, attr, dx in reversed(entries):
        tbl = 0x1000 if (tile & 1) else 0x0000
        tbase = tile & 0xFE
        hflip = bool(attr & 0x40)
        vflip = bool(attr & 0x80)
        pidx = attr & 3
        for half in range(2):
            t = decode_chr_tile(chr_rom, bank, tbl, tbase + (1 - half if vflip else half))
            for py in range(8):
                sy = 7 - py if vflip else py
                yy = (dy - min_y) + half * 8 + py
                for px in range(8):
                    sx = 7 - px if hflip else px
                    c = t[sy][sx]
                    if c == 0:
                        continue
                    xx = (dx - min_x) + px
                    r, g, b = nes_pal[spr_pal16[pidx * 4 + c] & 0x3F]
                    buf[yy][xx] = (r, g, b, 255)

    rows = [b"".join(bytes(px) for px in row) for row in buf]
    return w, h, xorig, yorig, rows


def render_hud_tile_strip(
    nes_pal: list[tuple[int, int, int]],
    chr_rom: bytes,
    pal32: list[int],
    tiles: list[int],
    pidx: int,
) -> tuple[int, int, list[bytes]]:
    w = len(tiles) * 8
    h = 8
    bg_univ = nes_pal[pal32[0] & 0x3F]
    rows = [bytearray() for _ in range(h)]
    for tid in tiles:
        t = decode_chr_tile(chr_rom, 1, 0x0000, tid)
        for py in range(8):
            for c in t[py]:
                r, g, b = bg_univ if c == 0 else nes_pal[pal32[pidx * 4 + c] & 0x3F]
                rows[py].extend((r, g, b, 255))
    return w, h, [bytes(r) for r in rows]


def main() -> int:
    nes_pal = load_nestopia_palette()
    pal_set = set(nes_pal)
    rom = open(ROM_PATH, "rb").read()
    prg = rom[16:16 + 32768]
    chr_rom = rom[16 + 32768:]

    nta_title, pal_title = decode_title_from_rom(prg)
    (nta300, pal300), = capture_ppu_frames()
    title_spr_pal = pal_title[16:32]
    stage1_spr_pal = pal300[16:32]

    generated: list[str] = []

    # 1. Backgrounds
    # bg_title_screen: 256x240 from decoded ROM NT0 in bank 3 (no Konami logo or copyright)
    title_rows = render_bg_nt(nes_pal, chr_rom, 3, nta_title, pal_title, 0, 240)
    p = os.path.join(GMS_DIR, "background", "images", "bg_title_screen.png")
    write_png_rgba(p, 256, 240, title_rows)
    generated.append(p)

    # bg_stage1_stars: 512x240 (NT0 + NT1, rows 0..26 stars only; rows 27..29 cleared for clean wrap)
    # transparent_zero=True so behind-BG sprites ($20 priority, e.g. Vic Viper) show behind stars!
    nta300_stars = list(nta300)
    for nt_off in (0, 1024):
        for ty in range(27, 30):
            for tx in range(32):
                nta300_stars[nt_off + ty * 32 + tx] = 0
    nt0_rows = render_bg_nt(nes_pal, chr_rom, 0, nta300_stars[:1024], pal300, 0, 240, transparent_zero=True)
    nt1_rows = render_bg_nt(nes_pal, chr_rom, 0, nta300_stars[1024:], pal300, 0, 240, transparent_zero=True)
    stars_rows = [a + b for a, b in zip(nt0_rows, nt1_rows)]
    p = os.path.join(GMS_DIR, "background", "images", "bg_stage1_stars.png")
    write_png_rgba(p, 512, 240, stars_rows)
    generated.append(p)

    # bg_hud_bar: 256x32 representing scanlines 208..239 (y_nt=220..239 + wrapped rows y_nt=0..11)
    hud_full = render_bg_nt(nes_pal, chr_rom, 1, nta300[:1024], pal300, 0, 240)
    hud_rows = hud_full[220:240] + hud_full[0:12]
    p = os.path.join(GMS_DIR, "background", "images", "bg_hud_bar.png")
    write_png_rgba(p, 256, 32, hud_rows)
    generated.append(p)

    # 2. Sprites (with exact metasprite bounding boxes & origins)
    sprite_specs = [
        ("spr_title_cursor", 3, title_spr_pal, 0, [1]),
        ("spr_vic_viper_level", 0, stage1_spr_pal, 0, [1]),
        ("spr_vic_viper_down", 0, stage1_spr_pal, 0, [2]),
        ("spr_vic_viper_up", 0, stage1_spr_pal, 0, [3]),
        ("spr_option", 0, stage1_spr_pal, 0, [4, 5]),
        ("spr_shot", 0, stage1_spr_pal, 0, [6]),
        ("spr_laser", 0, stage1_spr_pal, 0, [7]),
        ("spr_double", 0, stage1_spr_pal, 0, [0x24]),
        ("spr_missile", 0, stage1_spr_pal, 0, [0x0A, 0x08]),
        ("spr_fan", 0, stage1_spr_pal, 0, [0x0C, 0x0D, 0x0E, 0x0F]),
        ("spr_capsule_red", 0, stage1_spr_pal, 0, [0x10, 0x11, 0x12]),
        ("spr_capsule_blue", 0, stage1_spr_pal, 0, [0x13, 0x14, 0x15]),
        ("spr_shield", 0, stage1_spr_pal, 0, [0x5A, 0x5B, 0x5C, 0x5D]),
        ("spr_shield_low", 0, stage1_spr_pal, 0x03, [0x5A, 0x5B, 0x5C, 0x5D]),
        ("spr_explosion", 0, stage1_spr_pal, 0, [0x2D, 0x2E, 0x2F, 0x30]),
    ]

    meta_report = []
    for name, bank, sp_pal, attr_or, sids in sprite_specs:
        # Unify frame canvas across multi-frame metasprites if needed
        rendered = [render_metasprite(nes_pal, prg, chr_rom, bank, s, sp_pal, attr_or) for s in sids]
        # Compute shared origin / bbox across all frames in this sprite
        min_x = min(-xo for _, _, xo, _, _ in rendered)
        min_y = min(-yo for _, _, _, yo, _ in rendered)
        max_x = max(w - xo for w, _, xo, _, _ in rendered)
        max_y = max(h - yo for _, h, _, yo, _ in rendered)
        cw = max_x - min_x
        ch = max_y - min_y
        cxo = -min_x
        cyo = -min_y
        for idx, (w, h, xo, yo, rows) in enumerate(rendered):
            if (w, h, xo, yo) == (cw, ch, cxo, cyo):
                out_rows = rows
            else:
                canvas = [bytearray(cw * 4) for _ in range(ch)]
                ox = (-xo) - min_x
                oy = (-yo) - min_y
                for r in range(h):
                    canvas[oy + r][ox * 4:(ox + w) * 4] = rows[r]
                out_rows = [bytes(r) for r in canvas]
            p = os.path.join(GMS_DIR, "sprites", "images", f"{name}_{idx}.png")
            write_png_rgba(p, cw, ch, out_rows)
            generated.append(p)
        meta_report.append((name, cw, ch, cxo, cyo, len(sids)))

    # 3. HUD sprites: digits 0..9 + 6 power-up boxes (highlighted in BG pal 1!)
    for d in range(10):
        w, h, rows = render_hud_tile_strip(nes_pal, chr_rom, pal300, [0x30 + d], 0)
        p = os.path.join(GMS_DIR, "sprites", "images", f"spr_hud_digits_{d}.png")
        write_png_rgba(p, w, h, rows)
        generated.append(p)

    # Powerup slots 1..6 tiles in row 28, rendered with BG palette 1 (gold/orange highlight)
    slot_tiles = [
        [0x09, 0x0A, 0x0B, 0x0C],  # 1: SPEED UP
        [0x0D, 0x0E, 0x0F, 0x10],  # 2: MISSILE
        [0x11, 0x12, 0x13, 0x14],  # 3: DOUBLE
        [0x15, 0x16, 0x17, 0x18],  # 4: LASER
        [0x19, 0x1A, 0x1B, 0x1C],  # 5: OPTION
        [0x1D, 0x62, 0x63, 0x1F],  # 6: ?
    ]
    for idx, tiles in enumerate(slot_tiles):
        w, h, rows = render_hud_tile_strip(nes_pal, chr_rom, pal300, tiles, 1)
        p = os.path.join(GMS_DIR, "sprites", "images", f"spr_hud_slot_lit_{idx}.png")
        write_png_rgba(p, w, h, rows)
        generated.append(p)

    meta_report.append(("spr_hud_digits", 8, 8, 0, 0, 10))
    meta_report.append(("spr_hud_slot_lit", 32, 8, 0, 0, 6))

    # 3b. Emit .background.gmx and .sprite.gmx descriptors for GMS 1.4.1760
    bg_specs = [
        ("bg_title_screen", 256, 240),
        ("bg_stage1_stars", 512, 240),
        ("bg_hud_bar", 256, 32),
    ]
    for bg_name, bw, bh in bg_specs:
        bg_xml = f"""<!--This Document is generated by GameMaker, if you edit it by hand then you do so at your own risk!-->
<background>
  <istileset>0</istileset>
  <tilewidth>16</tilewidth>
  <tileheight>16</tileheight>
  <tilexoff>0</tilexoff>
  <tileyoff>0</tileyoff>
  <tilehsep>0</tilehsep>
  <tilevsep>0</tilevsep>
  <HTile>-1</HTile>
  <VTile>-1</VTile>
  <TextureGroups>
    <TextureGroup0>0</TextureGroup0>
  </TextureGroups>
  <For3D>0</For3D>
  <width>{bw}</width>
  <height>{bh}</height>
  <data>images\\{bg_name}.png</data>
</background>
"""
        with open(os.path.join(GMS_DIR, "background", f"{bg_name}.background.gmx"), "w") as f:
            f.write(bg_xml)

    for spr_name, sw, sh, sxo, syo, nf in meta_report:
        frames_xml = "\n".join(
            f'    <frame index="{idx}">images\\{spr_name}_{idx}.png</frame>'
            for idx in range(nf)
        )
        spr_xml = f"""<!--This Document is generated by GameMaker, if you edit it by hand then you do so at your own risk!-->
<sprite>
  <type>0</type>
  <xorig>{sxo}</xorig>
  <yorigin>{syo}</yorigin>
  <colkind>1</colkind>
  <coltolerance>0</coltolerance>
  <sepmasks>0</sepmasks>
  <bboxmode>0</bboxmode>
  <bbox_left>0</bbox_left>
  <bbox_right>{sw - 1}</bbox_right>
  <bbox_top>0</bbox_top>
  <bbox_bottom>{sh - 1}</bbox_bottom>
  <HTile>0</HTile>
  <VTile>0</VTile>
  <TextureGroups>
    <TextureGroup0>0</TextureGroup0>
  </TextureGroups>
  <For3D>0</For3D>
  <width>{sw}</width>
  <height>{sh}</height>
  <frames>
{frames_xml}
  </frames>
</sprite>
"""
        with open(os.path.join(GMS_DIR, "sprites", f"{spr_name}.sprite.gmx"), "w") as f:
            f.write(spr_xml)

    script_names = [
        "scr_nes_palette_init",
        "scr_nes_machine_init",
        "scr_nes_vblank_begin",
        "scr_nes_input_poll",
        "scr_nes_apu_tick",
        "scr_nes_game_tick",
        "scr_player_update",
        "scr_oam_push",
        "scr_nes_end_of_frame",
        "scr_nes_ppu_draw",
    ]
    sounds_xml = "    <sound>sound\\sfx_title_start</sound>"
    sprites_xml = "\n".join(f"    <sprite>sprites\\{n}</sprite>" for n, *_ in meta_report)
    bgs_xml = "\n".join(f"    <background>background\\{n}</background>" for n, _, _ in bg_specs)
    scripts_xml = "\n".join(f"    <script>scripts\\{n}.gml</script>" for n in script_names)

    project_xml = f"""<!--This Document is generated by GameMaker, if you edit it by hand then you do so at your own risk!-->
<assets>
  <Configs name="configs">
    <Config>Configs\\Default</Config>
  </Configs>
  <NewExtensions/>
  <sounds name="sound">
{sounds_xml}
  </sounds>
  <sprites name="sprites">
{sprites_xml}
  </sprites>
  <backgrounds name="background">
{bgs_xml}
  </backgrounds>
  <paths name="paths"/>
  <scripts name="scripts">
{scripts_xml}
  </scripts>
  <fonts name="fonts"/>
  <objects name="objects">
    <object>objects\\obj_nes_machine</object>
  </objects>
  <timelines name="timelines"/>
  <rooms name="rooms">
    <room>rooms\\rm_title</room>
    <room>rooms\\rm_stage1</room>
  </rooms>
  <help>
    <rtf>help.rtf</rtf>
  </help>
  <TutorialState>
    <IsTutorial>0</IsTutorial>
    <TutorialName></TutorialName>
    <TutorialPage>0</TutorialPage>
  </TutorialState>
</assets>
"""
    with open(os.path.join(GMS_DIR, "Gradius.project.gmx"), "w") as f:
        f.write(project_xml)

    # 4. Verify every single generated PNG contains ONLY nestopia.pal RGBs (for alpha > 0)
    import sys
    sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))
    import pngcmp

    off_count = 0
    for path in generated:
        im = pngcmp.load_png(path)
        bad = [c for c in set(im.px) if c not in pal_set]
        if bad:
            print(f"ERROR off-palette in {path}: {bad[:4]}")
            off_count += 1
    if off_count:
        return 1

    print(f"Generated {len(generated)} Nestopia-palette-verified PNGs in {GMS_DIR}")
    for name, w, h, xo, yo, nf in meta_report:
        print(f"  {name:22s}: {w:2d}x{h:2d} origin=({xo:2d},{yo:2d}) frames={nf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
