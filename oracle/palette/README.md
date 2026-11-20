# Oracle palette: pinned, and why it matters

The NES PPU never outputs RGB. It outputs a 6-bit *palette entry index* whose
three channels are voltage levels; turning those into colours is the TV's job
(or the emulator's palette table). Two emulators can therefore render exactly
the same PPU output and still disagree on every pixel's RGB value - which
makes "pixel identical" a meaningless claim unless the palette is pinned.

## Pinned table

`nestopia.pal` / `nestopia.json` / `nestopia.c` hold the 64-entry table
recovered from the oracle core by `tools/palette_probe.py`. It is identical to
Nestopia's built-in `yuv-v3`/default table and to FCEUmm's `yuv-v3` preset for
60 of 64 entries (the two disagree by 1-2 LSB on 4 low-green entries).

**The recreation must use this table** (`nes_palette[64][3]` in `nestopia.c`).
Any other table is a different visual target, and pixel comparisons against
the oracle will fail for reasons that have nothing to do with the game.

## How the table was recovered

`tools/palette_probe.py` writes a 65 KiB CNROM ROM from ~40 lines of 6502
that, once per five frames, writes one value to `$3F00` and blanks the
background to that entry, then boots it in a core, captures every frame plus
`$02` (the entry index) from the emulator's RAM map, and samples the middle of
the screen. Output: a 64x3 binary (`.pal`) plus JSON and a C array.

Because the emulator renders the probe, this measures the emulator's own
palette - not a table copied from somewhere.

## Cross-core pixel check

`oracle.sh selftest` points FCEUmm's "custom palette" mode at
`palette/fceumm_sys/nes.pal` (a copy of `nestopia.pal`, which FCEUmm reads as
`<sysdir>/nes.pal`). With both cores on one table, frames 300-340 of the
Gradius attract sequence come out **byte-identical, 41/41**.

## What still differs between cores (and why it does not matter)

Pixels are exact. RAM is not, because the two cores do not return from
`retro_run()` at the same point in the vblank period. Measuring system RAM
(2048 bytes) for frames 60-599 of the attract sequence gives:

| alignment | mean bytes differing | frames with byte-identical RAM |
|---|---|---|
| `nestopia[i]` vs `fceumm[i-1]` | 36.9 | 0 / 540 |
| `nestopia[i]` vs `fceumm[i]` | 25.2 | 0 / 540 |
| **`nestopia[i]` vs `fceumm[i+1]`** | **9.8** | **390 / 539** |
| `nestopia[i]` vs `fceumm[i+2]` | 35.1 | 0 / 538 |

So FCEUmm is exactly **one frame behind** Nestopia, and once that is aligned
390 of 539 frames are byte-for-byte identical, with ~10 bytes left over in the
rest (APU frame-counter phase and the RNG seed - `$0002`, `$000E`, `$01EC-$01F7`).

**Consequence for the recreation:** always align phase before counting
differences - search for the frame offset that maximises agreement, rather
than assuming frame *n* lines up. The recreation itself targets the
VBlank-begin / End-of-Frame model rather than "however many cycles the host
feels like", which removes the whole class of problem.
