# Retro-Recreations — Stage 01 Restaurant resources for GameMaker Studio 1.4.1760

**You create and own your GameMaker project. This repository does not package or generate a `.project.gmx`, room resource or ready-made GMS object resources.** It supplies extracted NES artwork, placement data, audio references and GML text for you to transfer into the project you make.

**Start here:** [Step-by-step transfer into your GMS 1.4.1760 project](docs/STAGE_01_TRANSFER_GMS14.md) · [Extraction/fidelity status](docs/STAGE_01_RESTAURANT.md) · [Static room overview](assets/stages/stage_01_restaurant/previews/stage_01_static_overview.png) · [Sprite overview](assets/stages/stage_01_restaurant/previews/stage_01_sprite_overview.png)

## Ready-to-import resources

- `assets/stages/stage_01_restaurant/background/bg_restaurant_*.png`: five **scenic-only** backdrops.
- `assets/stages/stage_01_restaurant/tilesets/ts_restaurant_*.png`: five palette-correct 16×16 metatile atlases for placed furniture/platforms.
- `assets/stages/stage_01_restaurant/sprites/import_frames/`: **87** individually numbered transparent frames in 18 named sprite folders; `manifest.json` lists exact size/origin. The full OAM strips and pose history are in `sprites/`.
- `assets/stages/stage_01_restaurant/audio/`: one stationary Seating music excerpt and two **mixed gameplay** boss/clear references (not isolated loops/SFX).
- `assets/stages/stage_01_restaurant/maps/stage_01_restaurant.json`: ROM-derived world placements, prizes/actor spawn coordinates and collision metadata.
- `gms_export/scripts/stage_01/scr_stage01_*.gml`: **23** scripts for ROM tile/spawn data and provisional player/enemy/crate/sink/boss code. Paste these into Script resources **you** create; follow the transfer guide for object events. The scripts have not been compiled/run in GameMaker in this workspace.

## Optional reproduction and verification

Requires Python 3 + Pillow, GCC/make/git and the checked-in USA ROM. The emulator build downloads a pinned fceumm core from GitHub. Raw emulator captures and build binaries are ignored; included replay inputs/checkpoints reproduce them.

```bash
./tools/emu/build_fceumm.sh
python3 tools/extract/capture_stage_01.py
python3 tools/extract/export_stage_01_rom.py --verify
python3 tools/extract/export_stage_01_sprites.py
python3 tools/extract/export_stage_01_import_frames.py
python3 tools/extract/export_stage_01_audio.py
python3 tools/extract/export_stage_01_gml.py
python3 -m unittest discover -s tools/extract/tests -v
```

Without raw captures, omit `--verify` when exporting the ROM map; the static-only Python tests still run. The original emulator route reaches **Water Rabbit**; its captured six-hit victory used a player-health cheat and should **not** be presented as a cheat-free ROM clear. The GML gameplay is a separate, untested prototype, not a claim of a finished recreation. See [the emulator harness README](tools/emu/README.md) for trace formats and safeguards.
