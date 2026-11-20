# Chip 'n Dale Rescue Rangers 2 — GameMaker Studio 1.4.1760 Recreation

A faithful recreation of the NES classic **Chip 'n Dale Rescue Rangers 2** (Capcom/Make Software, 1993),
rebuilt in **GameMaker Studio 1.4.1760** with modern GML structure but **original NES physics, speeds,
gravity and animation timing** preserved.

- **Resolution:** 256×240 (native NES), scaled up with aspect ratio kept.
- **Frame rate:** 60 steps/second (matches the NES).
- **Graphics:** extracted from the original ROM, reorganised the modern GMS way —
  tilesets, pre-assembled sprite sheets and backgrounds in their own sections.
- **Code:** clean, commented, state-machine based GML that runs on GMS 1.4.1760
  (no GameMaker 2-only functions).

---

## Folder layout

| Folder | What's inside |
|---|---|
| `EXTRACTED/` | Graphics ripped from the ROM: tilesets, sprite sheets, backgrounds, font, palette, ROM info. |
| `GML/` | Ready-to-paste GameMaker Language files (one per object/script event). |
| `tools/` | Python scripts used to extract the graphics (so you can re-run / extend them). |
| `GUIDE_STEP_BY_STEP.md` | **Start here if you're new to GMS 1.4** — full beginner walkthrough. |
| `PHYSICS_REFERENCE.md` | Original NES movement values + how to verify them in Mesen. |
| `SPOTLIGHT_SCENE.md` | The title attract scene: how it really works, measured timings, and the GMS 1.4 implementation. |

## Quick start (short version)

1. Read `GUIDE_STEP_BY_STEP.md` — it walks you through everything click-by-click.
2. Create a new GMS 1.4 project, set the room to **256×240** at **60 speed**.
3. Import the PNGs from `EXTRACTED/` (sprites → Sprites, tilesets → Tilesets,
   backgrounds → Backgrounds).
4. Create the objects/scripts listed in the guide and paste in the code from `GML/`.
5. Press **Run** (F5) and play.

## Controls (default)

| Action | Keyboard | Gamepad |
|---|---|---|
| Move | Arrow keys / WASD | D-pad / left stick |
| Jump | `X` or `Space` | A button |
| Throw / pick up | `Z` or `Ctrl` | B button |
| Duck | Down | D-pad down |
| Jump down through platform | Down + Jump | Down + A |

## A note on the graphics

All art was extracted directly from the provided ROM
(`Chip 'n Dale - Rescue Rangers 2 (USA).nes`, verified SHA-1
`a60ba28aca558fe3527d46b0df33bdd038d4c635`, matching the No-Intro USA dump).

**How NES graphics work (important):** every 8×8 tile is stored as 2 bits per
pixel — just the *shape* (which of 4 shades each pixel is). The actual
*colours* come from a palette, and the game picks which of 8 sub-palettes to
use for each tile via "attribute tables" in the level data. Because of this,
the extracted tilesets are provided in **grayscale** (the accurate shape
data), alongside `palette.png` (the game's real 32 colours).

To get tiles in their exact original colours, use **Mesen** (see the guide's
Appendix B): its PPU Viewer shows the tiles exactly as the game renders
them, with the correct sub-palette applied. Screenshot or export from there
for pixel-perfect coloured art.

### Fully-coloured, scene-accurate art

For scenes that are actually *assembled* (rather than just tile dumps), the art
is extracted by **running the ROM**, not by guessing at data offsets.
`tools/nes_emu.py` is a small headless NES (6502 + MMC1 + PPU register model)
that boots the ROM, runs it to an exact video frame, and reads back the real PPU
state — nametables, palette RAM, OAM and bank registers. That gives
pixel-perfect, fully-coloured output with no emulator GUI involved.

The first scene done this way is the title attract sequence; see
`SPOTLIGHT_SCENE.md`. Everything it produces lands in
`EXTRACTED/spotlight/`.

The included `Mesen.exe` is used throughout the guide's **verification
appendix** to double-check sprite frames, palette colours and physics values
against the original game running in the emulator.
