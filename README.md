# Retro Recreations — Chip 'n Dale Rescue Rangers 2 (NES) in GMS 1.4

Goal: recreate **Chip 'n Dale Rescue Rangers 2 (USA)** as faithfully as possible in **GameMaker: Studio 1.4.1760**, using the original ROM as the reference implementation.

This repository is the analysis + asset/code production side of the project. The user imports/transfers the generated GML and resources into a GMS 1.4.1760 project.

> **Beginner mode:** the project owner is a complete beginner to GMS 1.4. All transfer instructions — in `docs/03_import_guide_gms14.md` and in chat — are click-by-click: exact menu choices, exact names to type, paste-only code (never type code by hand), and a "you should see" success check for every transfer.

## Accuracy target

For this project, “cycle accurate” is defined at the observable game-behaviour boundary:

- NTSC frame timing: 60.0988 Hz, one simulation update per NES frame.
- Same update order as the ROM: input → game state dispatch → object logic → collision → camera/PPU shadow updates → sound.
- Same integer/fixed-point arithmetic style as the 6502 code (byte values, 8.8 subpixel positions where the ROM uses them, signed-byte velocities, wraparound where the ROM wraps).
- Same frame counters, timers, RNG behaviour, spawn order, collision order, and state-transition frames once each system is reverse-engineered.
- 256×240 internal resolution, integer-scaled output.

A literal transistor-level or 6502-cycle-by-cycle emulator inside GML is a different project; here we reproduce the ROM’s *behaviour and timing decisions* natively in GML and verify them against the ROM.

## Repository layout

- `Chip 'n Dale - Rescue Rangers 2 (USA).nes` — reference ROM (Mapper 1 / MMC1, 128 KB PRG, 128 KB CHR).
- `docs/` — project charter, ROM analysis, architecture, import notes, accuracy standard.
- `tools/` — Python analysis/extraction tools.
  - `tools/disassemble.py` — 6502 disassembler with MMC1 state helpers.
  - `tools/extract_chr.py` — renders CHR ROM pattern data to PNG tile sheets.
- `extracted/` — generated resources for transfer into GMS.
  - `extracted/tiles/` — CHR pattern-table sheets (grayscale index renders).
- `gml/` — GameMaker Studio 1.4 code to paste/import.
  - `gml/scripts/` — one `.gml` file per script resource.
  - `gml/objects/` — event code for core objects, organised by object/event.

## Working loop

1. Analyse a ROM subsystem with the tools (disassembly, CHR/data extraction, RAM watching notes).
2. Record findings in `docs/` and `docs/ram_map_preliminary.csv`.
3. Implement the equivalent GML in `gml/`.
4. Extract/rebuild only the resources needed for that subsystem in `extracted/`.
5. Transfer into GMS 1.4.1760 and compare against the original game running side-by-side.

## Current milestone

**Milestone 0 — boot/core scaffold**

- ROM header, vectors, reset stub, cold-boot and MMC1 banking routines identified.
- CHR pattern data extracted to tile sheets.
- GMS core scaffold created: NES constants, controller polling, fixed-point helpers, frame counter.

Next: extract state 1's graphics (palettes from bank 3 `$B081`, nametable streams from the `$D74C` init, CHR banks 31/29) and the child-object render helpers, so GMS can draw the second screen with the decoded script timing. The first/copyright screen (state 0) is intentionally skipped: the GMS boot state is 1.
