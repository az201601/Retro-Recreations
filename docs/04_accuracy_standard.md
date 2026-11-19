# Accuracy standard and verification

## What must match the ROM

- Frame on which any event starts/ends (state changes, spawns, animation changes, sound triggers).
- Player/enemy velocities, accelerations, positions and collision results in subpixel units.
- Input interpretation: held/pressed/released derived once per frame, before game logic, as in `$C17C`.
- RNG outputs and every consumer's call order (once the RNG routine is located).
- Camera positions, scroll splits and screen-transition frames.
- Animation frame indices and durations; metasprite composition, flipping and priority.
- Music tempo/sequence timing in NES frames; SFX start frames and durations.

## What may differ (documented deviations)

- Absolute display refresh: GMS presents at the monitor's rate; simulation remains per-NES-frame.
- NES hardware artefacts that GMS cannot reproduce natively (PPU scanline timing, sprite-0 hit mid-frame effects, DMC sample playback quirks) are approximated and logged here when encountered.
- Colour output uses a chosen NTSC palette table; the table is data and can be swapped without touching game logic.

## Verification method per system

1. Decode the routine; write down inputs, outputs, RAM touched and cycle/frame counts in `docs/`.
2. Implement the GML equivalent with the same integer operations.
3. Build a small test: fixed input sequence → compare resulting positions/state frames against the emulator+ROM (RAM watch / frame advance).
4. Only then integrate into the main game flow.

## Open accuracy questions

- Exact effect of the `$62–$66` NMI counter block (palette fade vs IRQ/timer helper).
- Exact contract of the `$F001`/`$C576` inline-data helper used by early state handlers (object/spawn record format suspected).
- Per-frame bank-6 routine at `$8000` (expected: sound engine tick).
- RNG routine location and seed handling at boot.
