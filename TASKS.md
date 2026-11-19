# Task list

## M0 — Core scaffold (in progress)

- [x] Identify ROM header, mapper, vectors.
- [x] Disassemble reset stub, cold boot, MMC1 routines, NMI entry, controller polling.
- [x] Write `tools/disassemble.py`.
- [x] Write `tools/extract_chr.py` and extract CHR sheets.
- [x] GMS core scaffold: constants, input, fixed-point helpers, `obj_nes_core`.
- [x] Decode dispatcher `$C54E` and the inline state table after `JSR $C54E` at `$D07C` (boot state $00 → handler `$D0C3`).
- [ ] Decode `$F001`/`$C576` inline-data helper used by the early state handlers.
- [ ] Decode `$C23F`, `$EFCE`, `$F0C8`, `$D63D`, `$D624` (post-boot init chain).
- [ ] Identify bank-6 `$8000` per-frame routine (suspected sound tick).

## M1 — Boot to first screen

- [ ] Map the first game state(s): Capcom logo / title / attract flow.
- [ ] Extract the palettes and nametable data used by the first screen.
- [ ] GMS: state machine shell that reaches the same first screen.

## M2 — Rendering model

- [ ] Decode PPU update queue routine `$C521` and scroll applier `$C2E5/$C34F`.
- [ ] Metatile/nametable format; build level renderer.
- [ ] Metasprite table format; build sprite renderer with priority/flips.

## M3 — Player physics

- [ ] Locate player object update routine; transcribe velocities/gravity/jump data.
- [ ] Frame-verify run/jump/land/crouch against the ROM.

## M4 — Level 1

- [ ] Extract Level 1 map, objects, enemies, items.
- [ ] Collision model (metatile attributes) transcribed and verified.

## Later

- [ ] Bosses, cutscenes, stage flow, 2-player behaviour.
- [ ] Music/SFX engine data and GMS playback model.
- [ ] Full-game parity pass with recorded inputs.
