# Retro-Recreations — Chip 'n Dale Rescue Rangers 2 (NES → GameMaker Studio 1.4.1760)

Current focus: **Stage 01, The Restaurant**. This repository contains the USA NES ROM supplied for the project, a pinned headless emulator/capture harness, a deterministic ROM/PPU asset extractor, sprite/audio strips, placement data and a **structurally checked, provisional** GameMaker Studio 1.4.1760 project at [`gms_export/Stage01Restaurant.project.gmx`](gms_export/Stage01Restaurant.project.gmx). The project has a room, resources and prototype interactions, but **has not been imported, compiled or played in GameMaker**; playable/fidelity claims are pending that test.

[Stage 01 status, screenshots and GameMaker import instructions](docs/STAGE_01_RESTAURANT.md) · [Static room overview](assets/stages/stage_01_restaurant/previews/stage_01_static_overview.png) · [Sprite overview](assets/stages/stage_01_restaurant/previews/stage_01_sprite_overview.png)

## Rebuild the Stage 01 kit

Install Python 3 and Pillow, GCC/make/git; then run:

```bash
./tools/emu/build_fceumm.sh                 # pinned core; first run clones from GitHub
python3 tools/extract/capture_stage_01.py   # checkpoints → raw ignored captures
python3 tools/extract/export_stage_01_rom.py --verify
python3 tools/extract/export_stage_01_sprites.py
python3 tools/extract/export_stage_01_audio.py
python3 tools/extract/export_stage_01_gml.py
python3 tools/extract/export_stage_01_gmx.py   # packages native .project.gmx + resources
python3 -m unittest discover -s tools/extract/tests -v
```

Static ROM scenery can be exported **without** building the emulator: `python3 tools/extract/export_stage_01_rom.py` (omit `--verify`). GML placement scripts can then be regenerated from its map. The other exports need the captured PPU/audio data. Large traces, state replays, core binaries, and exploratory tiles are gitignored; included checkpoints and route scripts make them reproducible.

## Where to look

- `assets/stages/stage_01_restaurant/background/` — bottom scenic PNGs (`bg_restaurant_*`), distinct from the older tracked frame references.
- `assets/stages/stage_01_restaurant/tilesets/` — palette-correct 16×16 metatile atlases (`ts_restaurant_*`).
- `assets/stages/stage_01_restaurant/maps/stage_01_restaurant.json` — ROM exact world placements, collision thresholds, prize and actor spawn coordinates.
- `assets/stages/stage_01_restaurant/sprites/` — assembled transparent OAM sprite strips and approximate-alpha BG prize cutouts.
- `assets/stages/stage_01_restaurant/audio/` — time-bounded gameplay audio excerpts and provenance manifest; boss/clear clips include SFX.
- `gms_export/Stage01Restaurant.project.gmx` — native GMX resource tree and Stage 01 test room. `scripts/stage_01/` has generated placement scripts, provisional physics/interaction scripts, and older **unwired** prototypes; packaged copies live in `scripts/`.
- `tools/emu/README.md` — headless emulator, capture, trace and audio-frame-index formats.

Room layout: one `rm_stage_01_restaurant` (2048×2048), already first in the GMX. The verified **NES** route reaches Water Rabbit; its recorded six-hit defeat uses a player-health cheat, so a cheat-free ROM clear is **not** claimed. The GameMaker boss has an experimental six-box-hit pattern and has **not** been runtime-tested. See the stage notes for controls, fidelity limits and remaining work.
