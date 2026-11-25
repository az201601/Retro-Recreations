# fceumm Headless Test Harness

Frame-accurate NES testing for extraction/verification using **libretro-fceumm**.

## Build
```bash
./tools/emu/build_fceumm.sh
```
Outputs (gitignored): `tools/out/emu/fceumm_libretro.so`, `tools/out/emu/fceumm_headless`.

## Run
```bash
tools/out/emu/fceumm_headless \
  --core tools/out/emu/fceumm_libretro.so \
  --rom "Chip 'n Dale - Rescue Rangers 2 (USA).nes" \
  --frames 4200 \
  --shots "3800,4000,4200" \
  --inputs tools/emu/inputs/stage_01_restaurant_to_gameplay.txt \
  --out tools/out/emu/frames \
  --ram-dir tools/out/emu/ram
```

- `--shots`: comma-separated frame numbers to save as PPM.
- `--inputs`: CSV `frame,down|up,BUTTON` (`A,B,SELECT,START,UP,DOWN,LEFT,RIGHT`).
- `--ram-dir`: dumps 2KB NES system RAM at each shot frame (for state/timing verification).
- Convert PPM to PNG with Pillow/ImageMagick as needed.

## Notes
- Use fceumm (not jsnes) for correct colors; jsnes 3.x has red/blue channel swap.
- Frontend is deterministic for a fixed ROM + input script.


## Save states
- `--save-state PATH` - save state at end of run (or at `--save-state-frame`).
- `--save-state-frame N` - frame to save state at.
- `--load-state PATH` - load state before run.
- `--start-frame N` - start loop at N+1 (use with `--load-state` saved at N); input events remain absolute frame numbers.
