# Import guide — GMS 1.4.1760

The files in `gml/` are paste-ready. GMS 1.4 cannot import loose `.gml` files as a complete project, so transfer is manual but mechanical:

## Scripts

For each file in `gml/scripts/`:

1. In the GMS resource tree, create a Script resource.
2. Name it exactly like the file without extension (e.g. `scr_nes_init`).
3. Paste the file contents into the script editor.
4. The first line of each file is a `/// scr_name(args)` doc comment; keep it — GMS 1.4 uses it for the script's argument help.

## Objects

For each folder in `gml/objects/` (e.g. `obj_nes_core/`):

1. Create an Object resource with that name.
2. For each `.gml` file inside (e.g. `Create.gml`, `Step.gml`, `Draw.gml`), add the matching event and paste the code.

## First test room

1. Create a room, 256×240.
2. Enable views; View 0: visible when room starts, view/port 256×240 / 768×720.
3. Place one `obj_nes_core` instance at (0,0).
4. Run. Expected M0 behaviour: a black 256×240 field, `global.NES_FRAME` counting at 60 Hz, and controller bits updating in `global.pad_held` / `global.pad_pressed` (check with the debugger or the temporary Draw overlay in `obj_nes_core`).

## Graphics (later milestones)

- Import PNG sheets from `extracted/` as Backgrounds (tile sheets) or Sprites as instructed per milestone. The M0 CHR sheets are reference/index images; do not treat grayscale tile sheets as final game art — final art is rebuilt when palettes/metasprites are decoded in M2.
