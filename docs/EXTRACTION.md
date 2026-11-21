# Asset extraction guide (run this on YOUR machine)

Goal: pixel-exact C&D Rescue Rangers 2 assets **without** squinting at a running
game. Everything below is deterministic — if it feels fiddly, stop and use the
tooling; missed frames come from eyeballing, never from dumps.

## Why manual capture loses frames
The NES PPU doesn't synthesise sprites. Every animation frame the game can show
already exists in the ROM as raw CHR tile data, and every on-screen object is
described to the PPU as OAM entries (x, y, tile index, attributes). A 60 Hz
camera misses nothing of the *data* — it's reading tea leaves. Dump the data
instead and it is byte-exact by construction.

## 1. Install FCEUX
- Windows/Linux/macOS builds: <https://github.com/TASVideos/fceux/releases>
- Debian: `sudo apt install fceux` (works on a normal desktop; this dev sandbox
  has no apt mirror access, which is why the helper scripts below exist).

## 2. Dump the CHR (all tiles, guaranteed complete)
```bash
pip install pillow
python3 tools/nes_chr_dump.py "Chip 'n Dale - Rescue Rangers 2 (USA).nes" --out Assets/drop-in/
```
Output: one `chr_bank_NN.png` sheet per 8KB CHR bank (16 tiles/row) + manifest.
The ROM has 16 CHR banks = 2048 8×8 tiles. Every animation frame of the
spotlight-scene sprites is in there somewhere — nothing to miss.

Tiles are 2bpp greyscale at this stage; colour comes from the palette RAM,
next step.

## 3. Dump the palettes (exact colours, not guessed)
- Quick and visual: load the ROM, pause on the frame you want, then
  **Tools → PPU Viewer**. It shows both pattern tables with the *live*
  background/sprite palettes applied. Sprites tab lists the 64 OAM entries
  with coordinates. Screenshot both.
- Scripted: run `tools/fceux_palette_dump.lua` (File → Load Lua Script).
  It logs all 32 palette-RAM bytes (`$3F00-$3F1F`) per frame to
  `palette_log.txt`. Find the sweep-scene frames (~f212-590 from the attract
  loop) and read its palettes straight from the log.

## 4. Dump sprite placement (exact x/y/tile per frame)
- Run `tools/fceux_oam_dump.lua`. It logs all 64 OAM entries each frame to
  `oam_dump.txt`. ~6-8 OAM records per chipmunk silhouette per frame; diffing
  consecutive frames tells you exactly which CHR tiles form each pose and its
  screen position — no estimating.
- Verify `OAM_BASE` in the script first (usually `$0200` shadow RAM; open
  Debugger → Memory Watch and confirm with the game's OAM-heavy moment).
  If your FCEUX blocks the read, fall back to PPU Viewer → Sprites screenshots.

## 5. Map tiles → sprites
CHR tile order ≠ on-screen order (MMC1 swaps 4KB CHR banks at runtime), so:
1. Use the CHR sheets to identify the brick pattern, the sprite frames, etc.
2. Use the OAM log to see exactly which tile indices the scene uses, in which
   order, at which coordinates — that *is* the sprite frame definition.
3. Reassemble multi-tile sprites in GMS 1.4 sprite editor as single frames,
   matching the NES sprite frame count 1:1.

## 6. What to hand back
Put EVERYTHING under `Assets/drop-in/` (git-ignored — do not commit
ROM-derived art to this repo):
```
Assets/drop-in/
  chr_bank_00.png … chr_bank_15.png   # tile sheets
  palette_log.txt                     # or PPU Viewer screenshots
  oam_dump.txt                        # or OAM screenshots
  scene_video_or_frames/              # optional reference captures
```
Then tell me which frames are the spotlight-scene sprites and I'll wire them
into the GMS 1.4 project as real resources (auto-generating the .sprite.gmx
files, .png frames and .project.gmx entries).

## Legal note (short version)
This is your local copy of the game, for your own recreation project.
Keep the extracted assets out of any repository or release you don't have
distribution rights to — the .gitignore here already enforces that.
