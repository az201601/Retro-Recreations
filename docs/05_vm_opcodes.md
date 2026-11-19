# Type-1 script VM — reference

Type-1 objects are **script machines**. Their per-frame update (`$EE89`) sets PRG bank 4 and jumps to the interpreter at `$DB90`, which executes bytecode from the object's script pointer until a yield/end opcode. Use `tools/decode_script.py --start <addr>` to decode any script.

## Interpreter core (`$DB90`)

1. If wait timer `$029C,X` ≠ 0: decrement it, done for this frame.
2. Fetch opcode via script pointer copy `$34/$35` (from `$0284,X`/`$0290,X`).
3. Dispatch through the 64-entry table at `$DB05` (opcode × 2, RTS-trick).
4. Handlers end in one of three ways:
   - `JMP $DBB7` — save script pointer back, **yield** (resume next frame).
   - `JMP $DBA7` — **continue** executing the next opcode in the same frame.
   - `JMP $DB9B` — reload pointer from `$0284/$0290,X` and continue (after jump/gosub).

## Object slot layout (12 slots, arrays have stride $0C)

Selected fields (all `,X` with X = slot 0–11):

| Addr | Meaning |
|---|---|
| `$0278` | script return-stack index (gosub depth pointer) |
| `$0284/$0290` | script pointer lo/hi |
| `$029C` | wait timer (frames) |
| `$02A8` | saved flag byte (restored with PLP by conditional jumps) |
| `$02CC/$02D8` | LOOPA / LOOPB counters |
| `$02E4` | object state field |
| `$02F0` | type: low nibble = type 1–15, bit 7 set while active; `$80` alone = empty |
| `$02FC/$0308` | Y position lo/hi |
| `$0314/$0320` | X position lo/hi |
| `$0344` | flags (bit 6/7 manipulated by opcodes $1F–$24; bit 3/4 tested by `$ED6A`) |
| `$0350/$035C` | X / Y velocity (nibble-packed, see `$E068`: stored byte is nibble-swapped before use) |
| `$0368/$0374` | X / Y subpixel accumulators used by MOVE |
| `$0380` | set by SETANIM ($2F) |
| `$0398` | physics/gravity table index (used by PHYS $1A) |
| `$03B0/$03BC` | X / Y position fractions (SETSUB $32) |
| `$03C8/$03D4` | state / counter fields used by collision & type-6 logic |
| `$03E0` | link byte: low nibble = linked child slot, bits $10/$20/$40/$50 link flags |
| `$03EC` | owner slot (copied from `$33` at spawn) |
| `$0404` | mirror of `$02F0` |

Spawn (`$F001` + free-slot finder `$EFEE`): finds first slot with type nibble 0, stores type| $80, the script pointer, zeroes the fields above, sets `$03E0=$40`, `$03EC=$33`. `$ED` holds the most recently spawned slot (used by the link helper `$E4E0`).

Per-frame object loop `$ED6A`: hides OAM entries 1–63 (`$F0CA` from X=4), then for slots 0–11 with a non-zero type: dispatch by type (type 1 → `$EE89` VM; type 2 → bank 2 `$A7A9`; type 6 → `$EDE0` collision-ish pre-check then VM; most other types also land on the VM), then `$F085` flag/timer upkeep, `$EFAB` (unless `$0344` bit 3), and `$F191` render/metasprite step (rate-limited by `$0344` bit 4 / frame counter `$2D`).

## Opcode map (64 opcodes)

Operand key: `u8` byte, `ptr` little-endian address, `cnt` loop count.

| Op | Name | Operands | Action |
|---|---|---|---|
| $00 | END | – | deactivate self (type := $80) |
| $01 | YIELD | – | end frame |
| $02 | WAIT | u8 | wait that many frames (`$029C`) |
| $03 | JSRN | ptr | jump to native code; script resumes next frame |
| $04 | SPAWN | type, ptr | spawn type-1-style object with script |
| $05 | CALLN | ptr | call native code, continue same frame |
| $06 | JUMP | ptr | script jump |
| $07 | GOSUB | ptr | script call (return addr pushed via `$0278` stack) |
| $08 | RET | – | script return |
| $09 | LOOPA | cnt, ptr | loop body at ptr, counter `$02CC` |
| $0A | LOOPB | cnt, ptr | same, counter `$02D8` |
| $0B–$10 | CJ_* | ptr | conditional script jumps (test saved flags `$02A8`) |
| $11 | PADJ | idx, mask, ptr | if `($38+idx) & mask` == 0 jump (idx 4 = `$3C` pad-1 pressed) |
| $12 | SWITCH | special | variable-length table jump (decoder stops here) |
| $13 | WRITE | value, ptr | store byte to address (e.g. `WRITE $01 -> $0040` changes state) |
| $14 | SET1D | idx, value | `$1D,X = value` (CHR bank shadows `$1D/$1E`) |
| $15/$16 | CLRLA/CLRLB | – | clear loop counters |
| $17 | SOUND | u8 | sound/music request (`$CE31` if $22–$78, else `$CE20`) |
| $18 | MOVE_YLD | – | apply velocity (`$DDC9/$DE1C`), yield |
| $19 | MOVE | – | apply velocity, continue |
| $1A | PHYS | – | gravity/physics step using `$0398` table |
| $1B/$1C | E41B/E412 | – | native helpers, continue |
| $1D/$1E | SET32C/SET338 | u8 | field stores |
| $1F–$24 | FLG_* | – | set/clear/toggle `$0344` bits 6/7 |
| $25 | SETX | u8,u8 | X position := `$0320:$0314` bytes |
| $26 | SETY | u8,u8 | Y position := `$0308:$02FC` bytes |
| $27/$28 | ADDX/ADDY | s8 | signed position add |
| $29/$2A | SETVX/SETVY | u8 | velocity bytes `$0350/$035C` |
| $2B–$2E | INC/DEC VX/VY | – | velocity ±1 |
| $2F | SETANIM | u8 | `$0380` = value; velocities/subpixels cleared |
| $30–$34 | SET398/3A4/SETSUB/3C8/3D4 | u8… | field stores (SETSUB takes 2 bytes) |
| $35/$36 | SET344/SET3E0 | u8 | flag/link byte stores |
| $37 | SETSTATE | u8 | `$40` = value, then fade-exit via `$D039` |
| $38/$39 | TIMER0/TIMER1 | u8,u8 | timed-effect setup `$C1B0/$C1BF` (fade engine) |
| $3A/$3B | LOADC44D/LOADC625 | ptr | screen/nametable loaders |
| $3C/$3D | IN3C/IN3D | u8,u8 | input-condition helpers `$C5CE/$C5F8` |
| $3E | TEXTCTL | 4×u8 | text engine regs `$55/$54/$52/$53` |
| $3F | MSGCTL | 3×u8 | `$4E/$4F/$57`, sets `$4D=4` (message substate) |

## Frame loop around the VM (`$D095`, per screen state)

```
JSR $ED6A   (update all objects)      JSR $C253 (rendering on, wait frame)
fade-in setup ($C1B0 #$FF, $C1CE wait-for-effect)
loop:
  wait 1 frame ($C1E7); if $71==0: bank 3, JSR $B508 (banked per-frame work)
  JSR $ED6A (objects);  JSR $CEBC (message system, dispatch on $4D)
  until $75 != 0  -> JMP $D043 (reset stack, init next $40 state)
```

Screen changes therefore always pass through: script sets `$40` (WRITE or SETSTATE) → jump to shared exit script (bank 4 `$AF68`: clear `$98`, TIMER1 fade, WAIT 20, WRITE `$40->$0075`) → `$75` ends the loop → `$D043` re-inits with the new state. SETSTATE ($37) instead exits via `$D039` (fade with `$C1BF`, `$C1CE` wait, fall into `$D043`).
