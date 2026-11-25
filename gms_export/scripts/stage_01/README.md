# Stage 01 GML source (for **your** GameMaker Studio 1.4.1760 project)

These `.gml` files are **text scripts**, not a `.project.gmx` or imported GameMaker resources. This repository does not create or package a GameMaker project. Create resources in your own project and transfer the assets/source by following **[`docs/STAGE_01_TRANSFER_GMS14.md`](../../../docs/STAGE_01_TRANSFER_GMS14.md)**, including its exact sprite origins, object/event table and test checklist.

## Which scripts to copy

Create 23 GMS Script resources named after every `scr_stage01_*.gml` filename (without `.gml`), then paste their contents. Five are regenerated from the ROM-derived map by `python3 tools/extract/export_stage_01_gml.py`:

- `scr_stage01_hex_byte` — decode a ROM metatile ID from a hex row.
- `scr_stage01_place_static` — place scenic wallpaper at depth 10000, furniture/platform tiles at 1000, and allocate the 128×128 collision grid. All placements are ROM world pixels in one 2048×2048 room.
- `scr_stage01_collision_at` — grid query: 0 empty, 1 downward-only platform, 2 solid. Generic NES collision thresholds `$A0`/`$D0`, `$F9` exception.
- `scr_stage01_spawn_prizes` / `scr_stage01_spawn_actors` — ROM initial coordinates and prize contents; all actors spawn at room creation rather than during ROM column scrolling.

The other `scr_stage01_*` scripts are **provisional GameMaker-side code** for Chip motion, box pickup/throw, simple enemy AI, sink/jet, Monterey refill, boss hits, camera/HUD and chapter transitions. They have *not been compiled or played in GMS 1.4 here*, and are not verified NES physics. Sound `snd_restaurant_excerpt` is played once as a stationary music reference; the mixed boss/clear captures are **not** used as clean BGM/SFX. See the transfer guide for the required events, parent hierarchy and limitations.

Source artwork: `assets/stages/stage_01_restaurant/` contains independent Background PNGs, 16×16 metatile atlases, OAM strips, manual-import individual sprite frames and WAV references. None of those image files alone constitutes a GameMaker sprite/background resource; you make them in your project. The five generated scripts have no JSON/file-I/O dependency at GameMaker runtime.
