# Project charter

## Product

A GMS 1.4.1760 recreation of **Chip 'n Dale Rescue Rangers 2 (USA)** for NES, built from reverse-engineering notes and resources extracted from the reference ROM in this repository.

## Non-negotiable accuracy rules

1. **Frame first.** Every gameplay quantity is derived per NES frame. If the ROM waits 17 frames, GML waits 17 frames — not “about 0.28 seconds”.
2. **Integer math first.** Positions/velocities are stored as integers (subpixel fixed-point) until the final draw step. No floating-point physics drift.
3. **Same order of operations.** When a system is implemented, its update order follows the ROM routine order as closely as GML allows.
4. **Same data.** Level layouts, tile maps, metasprite definitions, palettes, music/SFX sequencing data and enemy tables are extracted or transcribed from the ROM, not redrawn from memory.
5. **Verify against the original.** Each milestone is compared against the ROM running in an accurate emulator, ideally frame-by-frame for movement/collision tests.

## Practical interpretation of “100% cycle accurate” in GMS 1.4

GMS cannot execute the original 6502 machine code and does not give us control over NES CPU/PPU cycle timing. The achievable and meaningful target is:

- identical frame-by-frame decisions,
- identical timing constants converted from CPU-cycle/frame behaviour,
- identical visible/audible results within GMS rendering/audio limits,
- documented deviations where GMS/NES hardware models differ (e.g. sprite-per-scanline overflow, PPU raster effects, APU DMC behaviour).

If a future decision is made to instead write a full 6502/PPU/APU emulator in GML, that replaces this charter; it is not assumed here.

## Milestones

- **M0 — Core scaffold:** ROM identified, boot/banking documented, CHR extracted, GMS core object + input + fixed-point helpers. *(current)*
- **M1 — Boot to first screen:** state dispatcher decoded; title/attract flow reproduced with extracted tiles/palette.
- **M2 — Rendering model:** nametable/metatile renderer, scrolling, palette handling, sprite/metaspite renderer with priority and flicker rules.
- **M3 — Player physics:** Chip movement, running, jumping, crouching, picking up/throwing objects; frame-data verified.
- **M4 — Level 1:** map, collision, enemies, items, camera, deaths/exits.
- **M5 — Game shell:** lives, score, stage select flow, cutscenes, bosses, endings.
- **M6 — Audio:** music/SFX engine data transcribed or re-sequenced; channel behaviour approximated in GMS.
- **M7 — Parity passes:** input recordings compared ROM vs GMS; fix frame-off errors.

## Deliverables produced in this repo

- Analysis notes and maps in `docs/`.
- Extraction/analysis scripts in `tools/`.
- PNG/data resources in `extracted/`.
- Paste-ready GML in `gml/`.
