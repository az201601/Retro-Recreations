# Emulator reconnaissance notes

How the captures in `out/` are taken and what they contain.  Reproduce with the
scripts listed below; every asset in `assets_vec/` cites the trace + frame it
came from in `sprites.json` / `info.json`.

## Capture tool

```
tools/nes/capture <rom> <frames> <outdir> "<script>" <traceFrom> <traceTo> <ppmEvery>
```

* `script` is `frame:buttons` or `from-to:buttons`, comma separated, OR-ed
  together.  Buttons: A=1 B=2 SELECT=4 START=8 UP=16 DOWN=32 LEFT=64 RIGHT=128.
* Writes `<outdir>/trace.bin` (4400 byte records) and, every `ppmEvery`
  frames, `<outdir>/frames/fNNNNN.ppm`.
* The output directory must contain a `frames/` subdirectory (it exits 2
  otherwise).

## Getting into the stage

The boot sequence cannot be skipped with START mashing.  The reliable recipe is

```
200:8,260:8,400:32,420:32,440:8,520:1,700:8
```

which ends on the 1P/2P select screen; holding RIGHT from frame 5600 starts the
stage.  Frames < 2300 are still the title screen, < 5600 the cut scene, so
gameplay traces start at 5400-5600.

## Scripts

| script | output |
|---|---|
| `tools/capture_all.sh` | every trace the builders read (about 70 s) |

`capture_all.sh` writes:

| trace | content |
|---|---|
| `out/boot` | boot animation + title |
| `out/menu` | title / 1P-2P select art |
| `out/intro` | cut scene window (frames 300-5999) |
| `out/game` | first stage, running + jumping + throwing |
| `out/pi_holdR` | holding RIGHT: the 4-frame walk cycle and the idle loop |
| `out/mv_g` | RIGHT + A held: the full jump arc |
| `out/mv_a` | hop in place while running: landing squash |
| `out/pb` | RIGHT + B taps: crate wind-up / throw |
| `out/level` | first stage walking, PPM every 6 frames (for the background) |

## Facts learned the hard way

* `HIDE_SPRITES=1` breaks sprite-0 hit timing; the game freezes on the title
  screen.  Never use it for gameplay.
* The PPU `v` register logged at the end of a frame is the *mid-frame* write,
  not the scroll of the finished picture.  The real screen offset must be found
  by matching the rendered canvas against the PPM (`bg.find_offset`).
* Chapter 1 is a **single-screen** room: 3400 consecutive gameplay frames have
  an identical name table.  Chip walks right until x=50 and then cannon-fires
  crates at the wall, which is why longer "walks" do not scroll the level.
* Large OAM clusters merge the hero with the HUD (both use sprite palette 4).
  Render the hero from the `y = 120..196` band instead of clustering.
* Name tables 2/3 are empty in this level (vertical mirroring, the game streams
  into 0/1 only), so `canvas.png` is mostly padding - the clean screen is a
  straight 256x240 crop at (0,0).
