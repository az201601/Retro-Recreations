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
- [x] Identify bank-6 `$8000` per-frame routine: the sound-engine tick (docs/08).

## M1 — Boot to second screen (state 0 copyright SKIPPED by decision)

- [x] Map the boot flow: state 0 (copyright, skipped) → state 1 (second screen) → state 2.
- [x] GMS: boot directly at state 1 (`scr_nes_init`), matching the ROM right after state 0 exits.
- [x] Extract state-1 palettes: bank 3 `$B081-$B0A0` (32 bytes) — `tools/extract_state1.py`.
- [x] Decode `$C46A` nametable stream format; extract state-1 maps (loads to `$2000`, `$2400`, `$2144` from `$D74C`).
- [x] Decode child render helpers: `$F191` metasprite renderer (bank 5), `$F37C` follow, `$E4C6/$E749` flag helpers → spotlight disc composite.
- [x] GMS: state-1 screen rendered (disc + silhouette overlay, fade-in, trajectory phases, button skip → state 2). See `docs/07_state1_graphics.md`.
- [x] Sound for state 1: `$7F` = engine reset (silence), `$74`/`$73` rendered to WAV by executing the real engine (`tools/render_sound.py`) and played at frames 464/614 (docs/08).

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
- [ ] Music/SFX for the remaining screens (engine harness ready — docs/08; render per screen with `tools/render_sound.py --id ...` as each screen lands).
- [ ] Full-game parity pass with recorded inputs.
