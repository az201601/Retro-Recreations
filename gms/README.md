# Gradius (NES) — GameMaker: Studio 1.4.1760 Skeleton

Open `gms/Gradius.gmx/Gradius.project.gmx` in **GameMaker: Studio 1.4.1760**.

## Frame & PPU Timing Architecture

`obj_nes_machine` implements the NES PPU/OAM 1-frame pipeline across GameMaker's
four step/draw phases (see `docs/objects-and-oam.md` and `oracle/README.md`):

| GMS Event | NES Hardware Phase | Script | Behaviour |
|---|---|---|---|
| **Begin Step** | **VBlank-Begin** (NMI `$806A`) | `scr_nes_vblank_begin` | Copies `oam_sh_*` (`$0200-$02FF`) -> `ppu_oam_*` (OAM DMA `$4014`); latches staged `PPUSCROLL`, HUD split, and mode; increments `global.nes_frame` and NTSC clock (`60.098814 Hz`). |
| **Step** | **CPU Frame** (`$81BF`, `$ED02`, `$80BE`) | `scr_nes_input_poll`, `scr_nes_apu_tick`, `scr_nes_game_tick`, `scr_player_update` | Polls P1 buttons, ticks APU/SFX queue, updates mode (`0`=Title scroll-in, `1`=Menu, `3/4`=Start transition, `5`=Stage 1 gameplay), 32-slot SoA objects, 24-sample Option trail, and weapons. |
| **End Step** | **End-of-Frame** (`$8B10`/`$8BAB`) | `scr_nes_end_of_frame`, `scr_oam_push` | Stages Slot 0 Sprite-0 split (`CE 6D 23 F8`), rotates OAM cursor (`+$44`/`+$C4` skipping Slot 0), writes `$0200` shadow + `next_*` registers for **next** VBlank-begin. |
| **Draw** | **PPU Scanline Render** | `scr_nes_ppu_draw` | Renders `256x240` solely from VBlank-latched `ppu_*` state (`texture_set_interpolation(false)`), behind-BG (`$20`) priority before starfield, `+1` scanline OAM Y delay, and Sprite-0 HUD split at `y=208`. |

## Palette & Assets

- **Colours**: `scr_nes_palette_init.gml` and all 52 PNGs in `gms/Gradius.gmx/`
  are strictly derived from `oracle/palette/nestopia.pal` (Nestopia `2.0.0 f1e02d1`).
- **Regenerate assets & descriptors**:
  ```bash
  python3 tools/extract_gms_assets.py
  ```

## Title Screen

- Built directly from `Gradius (USA).nes` (`$8895`/`$8C8C` RLE + `sub_85E8` commands
  `1`, `2`, `3`, `6`) using `oracle/palette/nestopia.pal`, retaining only the
  `GRADIUS` wing logo and `PLAY SELECT` / `1 PLAYER` / `2 PLAYERS` (Konami logo
  and copyright lines stripped).
- Slides in right-to-left (`ppu_scroll_x = 254 -> 0` at `2 px/frame`, snapped on
  input), supports `Select` or `Up/Down` cursor movement at `(80, 134)/(80, 150)`,
  and runs the 80-frame `$004C` selection blink + `sfx_title_start` on `Start`.

## Controls

- **Arrows / WASD**: D-Pad (also moves `1 PLAYER / 2 PLAYERS` cursor on Title)
- **Z / Space**: A (Fire)
- **X / Shift**: B (Activate Power-Up)
- **C / Backspace**: Select (toggle `1 PLAYER / 2 PLAYERS` on Title)
- **Enter**: Start / Pause (Konami code `U U D D L R L R B A` works while paused)
- **F1**: Toggle NES frame/RAM debug readout
- **F2**: Dev helper to cycle power-up gauge (`$0042`) in Stage 1
