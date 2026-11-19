# ROM analysis — confirmed facts

Reference file: `Chip 'n Dale - Rescue Rangers 2 (USA).nes`

## iNES header

| Item | Value |
|---|---|
| File size | 262,160 bytes (16-byte header + 262,144 bytes ROM) |
| MD5 | `e78eb3226a9e09113be319fee1a84f4d` |
| SHA-1 | `a60ba28aca558fe3527d46b0df33bdd038d4c635` |
| PRG ROM | 8 × 16 KB = 128 KB, SHA-1 `cc9dcddc871036032d9ed6714f30ae8b2986b1f6` |
| CHR ROM | 16 × 8 KB = 128 KB, SHA-1 `c49107f8280c56fc3ac72d4e8c80e20b4ed4ad58` |
| Mapper | 1 — Nintendo MMC1 |
| Trainer / battery / four-screen | No / No / No |
| PRG RAM size byte | 0 (no battery RAM declared) |

MMC1 means mirroring, CHR banking and the switchable PRG bank are software-controlled; the iNES mirroring bit is not the final word during gameplay.

## Vectors (fixed PRG bank, CPU `$FFFA–$FFFF`)

| Vector | Address | Notes |
|---|---:|---|
| NMI | `$C003` | Main per-frame interrupt body in fixed bank. |
| RESET | `$FFE0` | Tiny stub in the very last bytes of PRG. |
| IRQ | `$FFE0` | Same stub as RESET; BRK/IRQ effectively reset the game. |

## Reset stub at `$FFE0`

```asm
$FFE0: SEI
$FFE1: INC $FFE1     ; read-modify-write to ROM space; final write has bit 7 set,
                     ; which resets the MMC1 shift register. Also self-referential:
                     ; $FFE1 is this instruction's own opcode byte in ROM.
$FFE4: CLD
$FFE5: JMP $C000
```

`$C000` immediately jumps to the cold-boot routine at `$C106`.

## Cold boot at `$C106` (fixed bank)

Confirmed sequence:

1. `SEI`; write `$08` to `$2000` (PPUCTRL shadow starts as `$08`: NMI off, sprite pattern table at `$1000`, background pattern table at `$0000`, 8×8 sprites).
2. Write `$1E` to `$2001` (PPUMASK value used by the game: BG + sprites enabled, left-edge BG/sprite columns enabled).
3. Wait through PPU warm-up/vblank polling loops using `$2002`.
4. Silence/initialise APU registers `$4000–$4013`, write `$08` to `$4001` and `$4005`, write `$8F` to `$4015`, write `$C0` to `$4017` (frame-IRQ inhibited / 5-step sequencer behaviour to be confirmed against the sound engine later).
5. Clear all RAM `$0000–$07FF` to zero.
6. Set stack pointer to `$FF`; store `$FF` at `$0600` as a sentinel.
7. `JSR $C272` — initialise MMC1.
8. Initialise key shadows: `$40=$00`, `$2A=$1E` (PPUMASK shadow), `$29=$08` (PPUCTRL shadow).
9. `JSR $C1DD` — set bit 7 of PPUCTRL shadow (`$29 |= $80`) and write `$2000`, enabling NMI.
10. Jump to `$D043`, the post-boot initialisation / main-entry path in the fixed bank.

## MMC1 routines (fixed bank)

### `$C272` — MMC1 reset/init

- Stores `$7F` sentinels in `$24`, `$25`, `$26` (CHR/PRG bank shadows start “invalid” so the first real bank set always writes the mapper).
- Increments guard byte `$27`, stores control value `$1E` in shadow `$23`.
- Serialises `$1E` to `$9FFF` (MMC1 control register range `$8000–$9FFF`) with the usual 5-write LSB-first sequence (`STA`, then four `LSR A` + `STA`).
- `$1E = %11110`: CHR mode 1 (two separate 4 KB CHR banks), PRG mode 3 (fix last 16 KB at `$C000`, switch the $8000 16 KB bank), mirroring mode 2.
- Clears `$27` before returning.

### `$C298` — set both CHR banks

- Input: X = CHR bank for PPU `$0000–$0FFF` (register range `$A000–$BFFF`, written via `$BFFF`), Y = CHR bank for PPU `$1000–$1FFF` (register range `$C000–$DFFF`, written via `$DFFF`).
- Uses the `$27` guard (`INC $27` on entry, `DEC $27` on exit) so NMI-time code can avoid interrupting a bank sequence.

### `$C2C5` — set PRG bank

- Input: A = desired 16 KB PRG bank at CPU `$8000–$BFFF`.
- If A equals shadow `$26`, it returns immediately (no mapper writes). Otherwise it updates `$26` and serialises A to `$EFFF` (PRG register range `$E000–$FFFF`).
- Preserves processor flags (`PHP`/`PLP`) because callers use it inside flag-sensitive code.

## NMI body at `$C003` — first-pass reading

- Pushes A/Y/X, writes `$00` to `$2001` (rendering off during the update window), writes `$00` to `$2003`, clears `$2B`, then writes `$06` to `$4014`: **OAM DMA source page is `$0600`**.
- If PPUMASK shadow `$2A` has BG/sprite enable bits (`$18`) set, it performs the heavier path: `JSR $C521` (PPU update queue — to decode), `JSR $C34F` (apply PPUCTRL/scroll state), restores `$2001` from `$2A`, calls `$C2E5` with X=0 (apply scroll/CTRL for view 0), and if `$2F` is non-zero calls `$C17C` to poll controllers.
- `$0600` doubles as a frame-progress counter in the NMI tail: while `$0600 < $EF`, `$2B` is incremented and the routine waits for the vblank flag to clear/set in a specific rhythm. Treat `$0600` carefully — it is both the OAM DMA page base and a game variable location.
- If `$27` (bank-switch guard) is zero, the NMI calls `$C298` with X=`$1D`, Y=`$1E` (CHR bank pair shadows), saves `$26`, forces PRG bank 6 (`LDA #$06; JSR $C2C5`), then `JSR $8000` — a per-frame routine living in switchable PRG bank 6 (very likely sound-engine tick and/or other banked per-frame work). It restores the previous PRG bank afterwards.
- A second counter block at `$62–$66` decrements `$66`; when it reaches zero it reloads from `$65` and calls into more per-frame logic. Names pending decode.

## Controller polling at `$C17C`

- Standard strobe: write `$01` then `$00` to `$4016`; read eight bits from `$4016` (player 1 → `$38`) and `$4017` (player 2 → `$39`).
- Post-processes two pad bytes (`$38/$39` current, `$36/$37` previous) and computes newly-pressed bits into `$3C/$3D` using `EOR #$FF` + `AND` (pressed = current AND NOT previous).
- GMS equivalent is already scaffolded in `gml/scripts/scr_input_poll.gml` using the same held/pressed/released derivation.

## Main-entry path at `$D043`

- Resets stack, calls `$C23F` (to decode), sets `$60=$01`, clears a set of state bytes (`$30`, `$61`, `$053A/$053B`, `$90`, `$92`, `$41`, `$B5`, `$B7`, `$4D`, `$75`, `$98`, `$7F`).
- Calls `$EFCE` and `$F0C8` (fixed-bank routines, to decode), re-runs MMC1 init `$C272`, decrements `$60`.
- Calls `$D63D` and `$D624`, then loads game-state byte `$40` and calls the dispatcher `JSR $C54E`.
- **Important:** bytes immediately after that `JSR $C54E` are data, not code. `$C54E` is a return-address/state-table dispatcher (decoded below).

## State dispatcher at `$C54E` — decoded

`$C54E` pops the JSR return address into zero-page pointer `$00/$01`. Because the 6502 pushes “next instruction minus 1”, the pointer lands one byte before the inline table. It then computes `Y = state * 2 + 1` and reads a little-endian handler address from `($00),Y` / `($00),Y+1`, stores it in `$02/$03`, and finishes with `JMP ($0002)`. Handlers therefore receive control directly and normally jump to a shared continuation instead of returning to the byte after the table.

For the boot call site at `$D07C`, the inline table starts at `$D081`:

| State `$40` | Handler | First-pass notes |
|---:|---:|---|
| $00 | `$D0C3` | Boot entry state: `LDY #$01; JSR $F001` with inline bytes `$D2 $F2`, then `JMP $D095`. |
| $01 | `$D0D7` | `JSR $F001` with inline `$DB $F2`; then `LDA #$7F; JSR $CE20`; `JMP $D095`. |
| $02 | `$D0E6` | `JSR $F001` with inline `$B2 $F3`; then `LDA #$01; JSR $CE20`; `JMP $D095`. |
| $03 | `$D0F8` | `JSR $F001` with inline `$70 $B6` (linear disassembly is misleading here; these are data for `$F001`). |
| $04 | `$D139` | To decode. |
| $05 | `$D102` | Builds pointer `$F5D0`, clears `$02–$06`, `LDX #$02`, `LDY #$01`, `JSR $F015` (mid-routine entry into the `$F001` helper). |
| $06 | `$D139` | Shares handler with state $04. |
| $07 | `$D120` | To decode. |
| $08 | `$D12F` | To decode. |
| $09 | `$D0CD` | `JSR $F001` with inline bytes that linear disassembly shows as `CMP #$F2`; treat as data until `$F001` is decoded. |

`$F001` also starts with `JSR $C576`, another return-address helper: it reads a 16-bit inline pointer from after its call site and advances the stacked return address by 2. So the recurring pattern in this engine is **JSR to a helper followed by inline data**. Any future disassembly pass must stop linear decoding at these call sites or it will invent false instructions.

## Preliminary RAM shadows

See `docs/ram_map_preliminary.csv`. Everything marked “shadow” is confirmed by boot/NMI code; gameplay meanings are added only when a routine proves them.
