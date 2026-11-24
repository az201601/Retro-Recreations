# Opening spotlight / silhouette sequence — GMS 1.4.1760

## What is in this extract

The included USA ROM was replayed from power-on in FCEUmm. Native 256×240 frames **1–900** are captured in order, covering the copyright screen, the moving brick-wall spotlight/silhouette reveal, and the completed title screen. The capture is a full-screen composite for each frame, so the reveal is pixel-identical to the emulator output rather than a hand-rebuilt approximation.

- Sprite-strip atlases: `extracted/spotlight_intro/spotlight_00.png` … `spotlight_14.png`
- Frame-to-ROM mapping: `extracted/spotlight_intro/frame_map.csv`
- `extracted/spotlight_intro/storyboard.png` is a labeled preview only; do not import it into the animation.
- Opening music: `extracted/audio/music_intro.wav` (48 kHz mono, 16-bit, 15.003 s)
- GML events: `code/04_obj_intro_Create.gml` and `code/05_obj_intro_Step.gml`
- Capture/rebuild script: `tools/capture_spotlight_intro.py`

**Verification:** all 900 imported frame cells were compared pixel-for-pixel with their original emulator PPM captures. All match. The ROM SHA-256 used for the capture was `34ca559b733ed910b0a493a0cb1f5d64e5cd9e7e4796032d986c08079573e047`.

## Import in GMS

1. Create a sprite named `SPR_spotlight_intro`.
2. Open its Sprite Editor and set the origin to **(0, 0)**. Keep smoothing/interpolation off.
3. Add each atlas **in numeric order**, `spotlight_00.png` through `spotlight_14.png`, using **Add from Strip**. Set the cell size to **256 × 240**. Each atlas is a row-major grid of full-screen frames; the final atlas contains only four frames. Do not add the atlas as one still image.
4. Confirm the resulting sprite has exactly **900 subimages**. Its frame 0 is emulator frame 1; frame 899 is emulator frame 900.
5. Create a sound named `MUS_intro` from `extracted/audio/music_intro.wav`.
6. Create `obj_intro`, assign `SPR_spotlight_intro`, place it at **(0, 0)**, and add the Create and Step event code from the two `code/04_...` and `code/05_...` files.
7. Create a 256 × 240 room named `rm_intro` at **60 steps per second**, and place `obj_intro` at (0,0). Make this the first room in the game's room order.
8. `obj_intro` holds the final title frame after playback. Enter or Space skips/continues to `rm_title`; adjust that destination room name in `code/05_obj_intro_Step.gml` if your project uses a different title room.

The atlas cell order is row-major. In the Sprite Editor, append all frames from one atlas before appending the next. The black surrounding pixels are intentional and are part of the original full-screen frames. Since GMS expands PNGs into texture data, 900 full-screen subimages can consume roughly 200 MiB or more at runtime; import only this one animation sprite and avoid duplicating it across instances.

## Rebuild the strips

After building the ignored emulator frontend as documented in `tools/README.md`, run from the repository root:

```bash
python3 tools/capture_spotlight_intro.py
```

This replays the ROM in deterministic chunks, captures every rendered frame, and writes the atlases and mapping CSV. It requires Pillow. Raw PPM captures go under ignored `tools/out/` and are not part of the deliverable.
