# Screen/state sequence (boot path) — and the skip decision

The top-level state byte is `$40`. On every state entry `$D043` resets the stack and runs: `$C23F` (hide sprites/rendering tweak) → clear state bytes → `$EFCE` (clear RAM `$0200-$040F`) → `$F0C8` (hide all OAM) → MMC1 init → `$D63D` (load per-state config from `$D610` table) → `$D624` (per-state native init) → dispatch on `$40` via `$C54E` table at `$D081` → handler spawns the screen's controller script → `$D095` frame loop (see `docs/05_vm_opcodes.md`).

## Per-state config records (`$D610` table, loaded by `$D63D`)

Format: byte0 = PPU flag bits (bit5 → PPUCTRL sprite size; bits1-2 → PPUMASK left-column), ptr1/ptr2 = palette source pointers (bank 3, copied to `$05AE/$05BE` shadows; `$0F` forced into `$058E/$059E`), byte5-7 = nametable fill params for `$C309`, bytes8-11 → `$1D-$20` (CHR banks: `$1D`=PPU $0000 bank, `$1E`=PPU $1000 bank), byte12+ = scroll bytes `$10/$13…` and sprite-0 OAM bytes.

| State | Config | CHR $1D/$1E | Notes |
|---|---|---|---|
| 0 | `$D719` | $1F / $1F | palettes `$B081/$B091`, fill byte5=$40 |
| 1 | `$D738` | $1F / $1D | same palettes, byte12=01 |
| 2 | `$D785` | $1E / $1F | byte0=$02 variant ($A1 B0 B1 B0 ptr bytes) |
| 3,4,6 | `$D8A0` | $1E / $1F | shared config |
| 5 | `$D813` | $1E / $1F | |
| 7 | `$D855` | $1F / $0B | |
| 8 | `$D871` | $1F / $00 | |
| 9 | `$D705` | $09 / $09 | |

Native init handlers (`$D624` dispatch): state 0 → `$D72D` (bank 3, one `$C44A` screen load with inline data), state 1 → `$D74C` (builds nametables `$2000` and `$2400` via `$C46A` loads, plus a third load at `$2144`), state 2 → `$D799` (jumps to `$CE82` text/message setup with pointers `$B2B6` area).

State handlers (`$D081` dispatch) spawn the controller script and optionally request sound via `$CE20` **before** the loop:

| State | Script | Sound req | Then |
|---|---|---|---|
| 0 | `$F2D2` | – | first screen (copyright) |
| 1 | `$F2DB` | `$7F` | **second screen — our start point** |
| 2 | `$F3B2` | `$01` | |
| 3 | `$B670` (bank 4) | – | |
| 4, 6 | (native, `$D139`) | – | bank-2 setup `$A73D` X=0 / X=1 (gameplay entry) |
| 5 | `$F5D0` (slot 2 direct) | – | |
| 7 | `$F480` | `$1D` | |
| 8 | `$F49F` | – | |
| 9 | `$F2C9` | – | variant of state 0's script |

## Decoded: state 0 (first/copyright screen) — SKIPPED by decision

```
$F2D2: WAIT 120          ; ~2 seconds, static screen from state-0 init
$F2D4: WRITE $01 -> $0040 ; next state = 1
$F2D8: JUMP $AF68         ; shared exit (bank 4): fade, WAIT 20, set $75
```

Nothing else happens: the screen content comes entirely from the state-0 init. **Project decision (user): the recreation skips this screen.** In GMS terms the boot state is `1` instead of `0` (`scr_nes_init`), which is exactly equivalent to the ROM after state 0's script finishes, because state 1's entry re-runs the whole `$D043` init chain with state-1 config.

## Decoded: state 1 (second screen) — recreation starts here

Entry actions: config state 1 (CHR banks $1F/$1D, palettes `$B081/$B091`), init `$D74C` builds the screen, sound request `$7F`, spawn script `$F2DB`:

```
SETX $C0,$00 / SETY $C0,$FF      ; parent starts at X=192, Y=-64 (off-screen)
SPAWN $F36D, $F372, $F371        ; 3 linked child objects (logo pieces)
CALLN $E4E0 (after each spawn)   ; link child to parent
GOSUB $F360                      ; CALLN $E4C6, CALLN $E749, SETSUB $20,$20, E41B
; movement phases (each: set velocity, then loop { GOSUB $F352 } N times)
SETVX $00 SETVY $20  loop 128    ; $F352 = MOVE_YLD + press-any-button check
SETVX $EA SETVY $EA  loop 96
SETVX $20 SETVY $00  loop 64
SETVX $EA SETVY $16  loop 48
SETVX $E0 SETVY $00  loop 128
SOUND $74
WRITE $00 -> $0013 / SETY $68,$00 / SETVX $20  loop 134
SETVX $C0                        loop 16
SOUND $73
WAIT 60
JUMP $F358: WRITE $02 -> $0040   ; next state = 2
JUMP $AF68                       ; shared fade exit
```

Button skip: `$F352` runs every frame of every phase — `PADJ idx4 mask$FF` tests pad-1 *pressed* (`$3C`); any press jumps straight to the state-2 exit. Total unskipped length ≈ 128+96+64+48+128+134+16+60 ≈ 674 frames (~11.2 s) plus fade.

State 2 then starts with sound request `$01` and script `$F3B2` (spawns, `SOUND $32`, input-wait `PADJ` on Start ($08 mask at `$F3BF`), a SWITCH at `$F3CF`) — likely the title/menu screen; decoding it fully is the next analysis step after state 1 renders.

## Recreating state 1 — done in `docs/07_state1_graphics.md`

Palettes, the `$C46A` nametable streams, CHR banks 31/29 and the child metasprite rendering are all extracted/decoded there (`tools/extract_state1.py`). State 1 is the **spotlight intro**: a pale mirrored-sprite disc moves behind a black silhouette background (brick wall + character silhouettes), implemented in GMS as disc sprite + black-ink overlay. Sounds: `$7F` is the engine reset (silence), `$74`/`$73` are rendered WAVs played at frames 464/614 — see `docs/08_sound_engine.md`. Remaining: exact fade-out timing.
