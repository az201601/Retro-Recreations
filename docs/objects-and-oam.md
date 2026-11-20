# Gradius object layout (`$0100-$04FF`), player state, and OAM staging (`$0200-$02FF`)

Derived from the traced 6502 disassembly (`sub_8B10`, `sub_8AAC`, `sub_8BAB`,
`sub_9B3E`, `sub_9FFC`, `sub_A527`, `sub_ADAB`, `sub_B0AF`, `sub_C0C7`) and
verified against live per-frame RAM/OAM captures of `Gradius (USA).nes` under
`nestopia_libretro.so`.

## 1. Object architecture: 32-slot Structure-of-Arrays (SoA)

Gradius does **not** store objects as contiguous 16-byte structs. It maintains
**32 object slots (`X = 0..31`, `$00..$1F`)** across parallel page-aligned
arrays in `$0100-$019F` and `$0300-$04FF`:

| slot range | count | role |
|---|---|---|
| `0` | 1 | Player (Vic Viper) — also title screen cursor during `mode=$00/$01` |
| `1..2` | 2 | Options 1 & 2 |
| `3..5` | 3 | Primary shot stream A (Normal / Laser / Double horizontal) for Player, Opt1, Opt2 |
| `6..8` | 3 | Primary shot stream B (2nd shot / Double 45° diagonal) for Player, Opt1, Opt2 |
| `9..11` | 3 | Missiles for Player, Opt1, Opt2 |
| `12..21` (`$0C..$15`) | 10 | Active enemies & power capsules (indexed as `base + $0C + 0..9`) |
| `22..31` (`$16..$1F`) | 10 | Enemy projectiles / secondary actors (indexed as `base + $16 + 0..9`) |

Because each array is 32 bytes wide (`base + X`), **`$0370-$037F` is the upper
half of the `$0360,X` X-coordinate array** (object slots `16..31`: enemy slots
4–9 at `$0370-$0375` and enemy projectiles 0–9 at `$0376-$037F`), **not** a
single player struct. The player occupies **Slot 0** (`X = 0`) across the
arrays plus zero-page state `$0017-$004C`.

### Array map (`X = 0..31`)

| base | range | meaning |
|---|---|---|
| `$0100,X` | `$0100-$011F` | Slot 0: player state (`0`=off, `1`=alive, `2`=dying). Enemy slots `12..21`: anim bank / solid flag (`bit 7`), `$06`=blue capsule |
| `$0120,X` | `$0120-$013F` | Metasprite ID (`0`=invisible; `$01-$03`=Vic Viper; `$04-$05`=Option; `$06/$07/$24`=Shot/Laser/Double; `$08/$0A`=Missile; `$2D-$30`=player explosion) |
| `$0140,X` | `$0140-$015F` | Animation frame delay counter |
| `$0160,X` | `$0160-$017F` | Slot 0: Option trail ring-buffer head (`0..23`); Slots 3..11: weapon type (`0`=shot, `1`=laser, `2`=double, `3`=missile); Slots 12..31: anim frame / subtype |
| `$0180,X` | `$0180-$019F` | OAM attribute OR-mask (palette/flip/priority override passed to `sub_8AAC`) |
| `$0300,X` | `$0300-$031F` | Object AI / behaviour ID (`$00`=free, `$01`=power capsule, `$02`=explosion, `$03+` / `bit 7`=active hazard dispatched via `$AE19`) |
| `$0320,X` | `$0320-$033F` | **Y position** (integer screen pixels; `$0320`=Player Y, `$0321..$0322`=Options Y, `$032C..$033F`=Enemies/Projectiles Y) |
| `$0340,X` | `$0340-$035F` | **Y subpixel** (8-bit fractional coordinate) |
| `$0360,X` | `$0360-$037F` | **X position** (integer screen pixels; `$0360`=Player X, `$0361..$0362`=Options X, `$036C..$037F`=Enemies/Projectiles X) |
| `$0380,X` | `$0380-$039F` | **X subpixel** (8-bit fractional coordinate) |
| `$03A0,X` | `$03A0-$03B5` | Slots 3..8 (`$03A3..$03A8`): shot cooldowns; Slots 12..21 (`$03AC..$03B5`): capsule-drop wave group |
| `$03B0,X` | `$03BC-$03CF` | Slots 12..31: signed Y velocity integer (8.8 with `$03EC`) / timer |
| `$03E0,X` | `$03EC-$03FF` | Slots 12..31: Y velocity subpixel |
| `$0400,X` | `$040C-$041F` | Slots 12..31: AI phase / flags |
| `$0420,X` | `$042C-$043F` | Slots 12..31: signed X velocity integer (8.8 with `$044C`) / explosion anim index |
| `$0440,X` | `$044C-$045F` | Slots 12..31: X velocity subpixel |
| `$0460,X` | `$0460-$047F` | Slots `0..9` at `$0460,Y`: hitbox size class (`$BFDA/$BFDE`); Slots `0..9` at `$046C,X`: damage / HP / AI timer |
| `$0480,X` | `$048C-$049F` | Slots 12..31: AI sub-state / Y acceleration |
| `$04A0,X` | `$04AC-$04BF` | Slots 12..31: AI counter / hit count |
| `$04C0,X` | `$04CC-$04DF` | Slots 12..31: AI sub-timer |
| `$04E0,X` | `$04EC-$04FF` | Slots 12..31: AI flags / variant |

Stage 5 (`$0019 == 4`) additionally stores 4 multi-segment tentacle/arm actors
in `$0600-$06BF` (stride `$30`: bases `$0600, $0630, $0660, $0690`) rendered by
`sub_8C06`.

## 2. Player record (Slot 0 + zero page + Option trail)

Verified in `sub_9FFC` and live gameplay watches:

| address | role | values / behaviour |
|---|---|---|
| `$0017` | Difficulty rank | Computed each frame by `sub_9C45` from weapon/option/shield/stage flags |
| `$0018` | Active player | `0` = 1P, `1` = 2P |
| `$0019` | Stage index | `0..6` (Stage 5 = `4`) |
| `$001A` | Loop count | `0` = first loop |
| `$001B` | Stage phase flags | `$80` = active scrolling/play; `$10/$20/$40` = intro/death/game-over |
| `$0020/$0021` | Lives | Remaining ships for 1P (`$0020`) / 2P (`$0021`) |
| `$003E/$003F` | Camera scroll X | `$003E` = fine `0..255` -> `$0012` (`PPUSCROLL_X`); `$003F` bit 0 -> `$0010` nametable X |
| `$0040` | Speed-Up count | `0+`; movement speed = `min($0040 + 2, $10) * 0.5` px/frame (`1.0` px/frame at 0 speedups) |
| `$0041` | Missile armed | `0` = none, `1` = missiles enabled |
| `$0042` | Power-up gauge | `0` = none, `1`=SPEED, `2`=MISSILE, `3`=DOUBLE, `4`=LASER, `5`=OPTION, `6`=SHIELD (activates on B, resets to `0`) |
| `$0044` | Primary weapon | `0` = Normal (`$06`), `1` = Laser (`$07`), `2` = Double (`$06` + `$24`) |
| `$0045` | Options count | `0..2` |
| `$0046` | Shield HP | `0` = off, `5` = full; flashes attribute `$03` when `== 1` |
| `$0100` | Player alive state | `0` = inactive, `1` = active, `2` = dying (`$C0FA` explosion anim `2D..30`) |
| `$0120` | Player metasprite | `1` = level, `2` = banking down, `3` = banking up (updates after 8-frame `$0140` delay) |
| `$0320/$0340` | Player Y (8.8) | Clamped `[$10, $C0]` (`16..192`) |
| `$0360/$0380` | Player X (8.8) | Clamped `[$10, $F0]` (`16..240`) |
| `$07A0-$07B7` | Option X trail | 24-entry ring buffer updated whenever D-pad held (`$0160` head); Opt1 = `head - 11`, Opt2 = `head - 22` |
| `$07C0-$07D7` | Option Y trail | 24-entry ring buffer paired with `$07A0-$07B7` |

## 3. Sprite staging (`$0200-$02FF`, 64 × 4 bytes)

The NES PPU uses 8×16 sprites (`PPUCTRL` bit 5 set in gameplay `$0010 = $A8`,
and `$0010 = $88` on title). Each 4-byte entry follows hardware OAM order:
`[Y, tile, attr, X]`.

### One-frame VBlank OAM DMA pipeline

1. During Frame `N` CPU logic (`sub_8B10` before `sub_80BE`, then `sub_8BAB`
   to clear unused trailing slots), the game populates `$0200-$02FF`.
2. At **VBlank-begin of Frame `N+1`** (`$8085-$8087`), the NMI handler executes
   `LDA #$00 / STA $2003 / LDY #$02 / STY $4014`, copying `$0200-$02FF` into
   PPU OAM before Frame `N+1` renders.
3. Live verification across 700 frames confirms
   `(cpu_$0200[N-1] & mask) == ppu_oam[N]` on every active frame (where `mask`
   clears unimplemented hardware attribute bits 2–4, `0xE3`, on byte 2).

### Slot 0 (`$0200-$0203`): fixed Sprite-0 split

Slot 0 is **never rotated**. `sub_8B10` copies 4 bytes from `$8B08`:
- `$001F == 0` (title screen / no status bar): `F4 F4 F4 F4` (offscreen, `Y=244`).
- `$001F != 0` (gameplay HUD visible): `CE 6D 23 F8`:
  - `Y = $CE` (206 -> drawn at scanline 207, top boundary of the HUD bar)
  - `Tile = $6D` (`$1000` sprite table)
  - `Attr = $23` (behind-background priority `$20`, sprite palette 3)
  - `X = $F8` (248)
- In-frame at `$9AA3`, gameplay spins on `LDA $2002 / AND #$40 / BEQ` until
  Sprite 0 hits, then writes `PPUSCROLL = (0, 0)`, clears nametable X bit in
  `PPUCTRL`, and switches the HUD CHR bank via `sub_8A9E`.

### Slots 1..63 (`$0204-$02FF`): rotating OAM pool & metasprites

- `$002F` holds the rotating starting byte offset: each frame `$002F = ($002F + $44) & $FF`,
  adding `$04` if it lands on `$00` so Slot 0 is preserved.
- `sub_8AAC` pushes each OAM entry at `$0200,X` and steps `X` by
  `X = (X + $C4) & $FF` (`-15` slots = `+49` mod 64, repeating if `X == 0` to
  skip Slot 0). Because `gcd(49, 64) = 1`, every sprite cycles uniformly across
  all 63 OAM slots to avoid permanent 8-sprites-per-scanline dropout.
- `sub_8AAC` looks up metasprite ID `sid` (`$0120,X`) in the 16-bit pointer
  table at `$8D9E` (`$8E9E` for `sid >= $80`). Each definition begins with
  tile count `N`, followed by `N` tuples `[dy, tile, attr, dx]` (signed `dy/dx`
  added to slot Y/X; `attr |= $0180,X`). Sub-sprites clipped horizontally off
  screen (`X + dx < 0` or `X + dx >= 256`) are dropped without consuming an
  OAM slot.
- Remaining unused slots (up to 63) are hidden by writing `Y = $F4` (`244`)
  to `$0200,X` across `$8B93-$8BAF` and `sub_8BAB`.
