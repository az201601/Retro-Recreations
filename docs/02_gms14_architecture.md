# GMS 1.4 architecture

Target IDE/runtime: **GameMaker: Studio 1.4.1760**. All GML in `gml/` avoids post-1.4 language features: no `function` declarations, no structs, no method variables, no ternary operator, no `??`. Scripts are one file per script resource and use `argument0...` / `var` locals.

## Room/view setup (first test room)

- Room size: 256×240 (NES visible resolution).
- View 0 enabled, view in room 256×240, port on screen 768×720 (3× integer scale) for desktop testing.
- `obj_nes_core` placed in the room; it owns global state, input polling and the master frame counter.
- Room speed: 60 for now. NTSC NES is 60.0988 Hz; the tiny difference is handled later by an optional frame-accumulator in `obj_nes_core` Step (see `gml/objects/obj_nes_core/Step.gml` notes). Gameplay logic must always advance in whole NES frames, never by `delta_time` fractions.

## Coordinate and math model

- Screen/entity positions are stored as integer subpixels: `value = pixel * 256 + subpixel` (8.8 fixed point), matching the way NES code commonly keeps a low fractional byte and a high pixel byte.
- Draw code converts with `scr_fp_to_pix()` (`floor(value / 256)` for non-negative world coordinates) and adds the camera offset.
- Speeds are signed integers in subpixels/frame. Gravity, acceleration, max speeds and jump velocities will be transcribed from the player routines when decoded — do not tune by feel.
- Byte-sized values that wrap on NES are masked with `& $FF` at the same points the 6502 would wrap (counters, timers, some positions). Signed-byte reads use `scr_s8()`.

## Controller model

NES bit order used everywhere in this project (matches the ROM's post-processed pad bytes):

| Bit | Value | Button |
|---:|---:|---|
| 0 | `$01` | A |
| 1 | `$02` | B |
| 2 | `$04` | Select |
| 3 | `$08` | Start |
| 4 | `$10` | Up |
| 5 | `$20` | Down |
| 6 | `$40` | Left |
| 7 | `$80` | Right |

`scr_input_poll()` produces `global.pad_held`, `global.pad_pressed`, `global.pad_released` for player 1 (player 2 arrays/globals are added when co-op logic is decoded). Pressed/released are derived exactly like `$C17C`: `pressed = held & ~previous`, `released = previous & ~held`.

Default keyboard map: X=A, Z=B, Right Shift or Shift=Select, Enter=Start, arrow keys=D-pad. Gamepad device 0 is ORed in when connected (face1=A, face2=B, select/start, D-pad + left stick threshold optional later).

## Object plan (grows per milestone)

- `obj_nes_core` — boot, frame counter, input, global state machine shell.
- `obj_game` — (M1) top-level state dispatcher equivalent to `$C54E` call sites.
- `obj_player` — (M3) Chip/Dale controller.
- `obj_camera` — (M2/M4) scroll/shadow-register equivalent.
- `obj_level` — (M4) metatile map, collision and spawns.
- `obj_metasprite` / draw scripts — (M2) NES OAM-style sprite composition with priority, flipping and 8-sprites-per-scanline flicker policy where it matters.

## Rendering model (planned, M2)

GMS will not use NES tiles directly at runtime. Instead:

1. ROM nametable/metatile data is extracted to data files.
2. Tile sheets in `extracted/tiles/` are references for rebuilding background/sprite graphics in GMS with the correct NES palettes.
3. The game draws in NES order: background layer, then sprites sorted by OAM order with behind-background priority respected per metasprite piece.

Until palettes and metasprite tables are decoded, CHR sheets remain grayscale index images (values 0–3), which is exactly the information stored in CHR ROM.
