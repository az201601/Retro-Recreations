# Mesen 2 as the second opinion (on your machine, not the sandbox)

Mesen 2 is the reference the NES homebrew and TAS communities trust most for
detail: its PPU is accurate to the point of modelling individual PPU revisions
(2C02G/2C02H), it has a per-dot PPU viewer, an APU oscilloscope, a memory
viewer, a step-by-step frame advance, and a rewind buffer. When the recreation
and the oracle disagree, Mesen's debuggers settle it.

It is *not* set up inside this sandbox: release binaries live on GitHub's
release CDN, which this environment cannot reach (`curl` gets an SSL error
from `objects.githubusercontent.com`), and the available upstream source
build is Avalonia-based. So the sandbox uses Nestopia + FCEUmm (see
`../emulator/README.md`), and Mesen 2 is used on your PC as the tie-breaker.

## Get it

Download **Mesen 2.1.1** for your OS from
<https://github.com/SourMesen/Mesen2/releases> and unpack it. Linux x64 is a
plain `Mesen` binary in a folder; macOS is an `.app`; Windows has an `.exe`.

First run: drag `Gradius (USA).nes` onto the window.

## Settings that make it a valid reference

Match the oracle, or the comparison is meaningless:

| setting | value | where |
|---|---|---|
| Video filter | **None** | Video > Filters |
| Palette | **YUV-V3** (NES) | Video > Palette - this is the table in `palette/` |
| Overscan cropping | **off** (`0,0,0,0`) | Video > Overscan |
| Sprite limit | **enabled** (8 per scanline) | NES > Sprites (Mesen hides overscan sprites by default) |
| Audio filter | **off** | Audio > Filters |
| Turbo/rewind/overclock | **off** | Emulation |
| Save states | none loaded | - |

Then confirm the timing: **Help > About** should show the NTSC NES frame rate
of 60.0988 Hz; the emulation should sit at exactly that rate, not 60.000.

## Using it to check work

* **Frame advance**: `F10` (or Emulation > Frame Advance) steps exactly one
  emulated frame. Combined with a save state (`F5`/`F8`) at a known frame, this
  is how you put the emulator on the same frame as a capture.
* **PPU viewer** (Debug > PPU Viewer): shows the nametable, pattern tables,
  palette RAM and OAM exactly as the PPU holds them at that instant. This is
  the reference for every tile and sprite in the recreation.
* **Memory viewer** (Debug > Memory Viewer): watch the game's variables while
  frame-advancing - much faster than inferring them from pictures.
* **Event viewer / trace logger** (Debug > Trace Logger): per-instruction CPU
  trace with PPU/APU markers, for the cases where a sprite glitches on frame
  N and nothing obvious explains it.
* **APU viewer** (Debug > APU Viewer): per-channel state and waveform; the
  reference for each sound effect's register writes.

## Comparing Mesen to a capture

Frames are 256x240 with no overscan, so any Mesen screenshot drops straight
into the same comparison as the oracle:

```
./tools/pngcmp.py capture/f000120.png mesen_shots/mesen_120.png
./tools/pngcmp.py capture/f000120.png mesen_shots/mesen_120.png --palette
```

If the first reports differences but `--palette` reports none, the palette
setting is wrong - go back to the table above, not to the game code.

## If you want Mesen running headless too

Mesen 2 ships a libretro-ish core path and a `--testrunner` option, but for a
one-off cross-check the GUI plus frame advance is faster than wiring up its
command line. The sandbox harness (`emulator/`) already covers the
machine-driven side, so Mesen is best kept as the human-in-the-loop reference.
