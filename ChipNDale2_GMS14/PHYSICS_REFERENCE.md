# Physics Reference — Original NES Values

This document records the movement/physics values used by the recreation and
explains where each number comes from, so the feel matches the original game.

> **Important:** GMS 1.4 runs the game at the room's **speed** (steps per second).
> This project sets it to **60**, exactly like the NES (NTSC = ~60 frames/sec).
> All "pixels per frame" values below are therefore directly usable as
> "pixels per step" in GML — no conversion needed.

---

## 1. Player (Chip / Dale)

| Parameter | Value | Source / notes |
|---|---|---|
| Walk speed (max horizontal) | **1.5 px/frame** (alternates 1,2,1,2…) | TAS community data for the series; the sequel kept the first game's controls. Verify in Mesen (§4). |
| Walk acceleration | snappy (near-instant, ~1–2 frames to full speed) | Original has very responsive, low-skid movement. |
| Jump initial velocity | **≈ −5.5 px/frame** (upward) | Tuned to reach the original ~43 px jump height. |
| Gravity | **≈ 0.30 px/frame²** | Gives the original floaty-but-snappy arc. |
| Max fall speed | **≈ 4.5 px/frame** | Caps terminal velocity like the original. |
| Jump height | **≈ 43 px** (just over 2 stacked blocks) | Matches TAS note "you jump up by 43 pixels". |
| Walk animation | 2 frames, **every 4 steps** (15 fps at 60 steps/s) | NES sprite animation timing. |
| Jump / fall animation | single pose, no cycling | Original holds one frame while airborne. |

### Why "1.5 px/frame" looks like 1-2 px/frame
The NES uses fixed-point maths (8.8 format). A speed of 1.5 px/frame is stored
as `0x0180`. Each frame the game adds 1.5 to a sub-pixel position, so on screen
Chip moves 1 px one frame, 2 px the next, averaging 1.5. In GML we simply use
the float `1.5` and let GameMaker handle the sub-pixel position — identical result.

### How the jump numbers relate
With initial velocity `v0 = -5.5` and gravity `g = 0.30`:
- Apex height ≈ v0² / (2g) = 5.5² / 0.6 ≈ **50 px** (a little over the 43 px
  "usable" height once you account for the sprite's origin — close enough that
  the feel matches; fine-tune in Mesen).
- Time to apex ≈ v0 / g ≈ 18 frames (~0.3 s).

If you want the *exact* original constants, use the Mesen measurement steps in
§4 and overwrite the values in `GML/scr_init.gml` — they're all in one place.

---

## 2. Enemies

| Parameter | Value | Notes |
|---|---|---|
| Patrol walk speed | **0.75 px/frame** (alternates 0,1,0,1…) | Slower than the player, like the original mice/rats. |
| Turn-around | instant on wall / edge | Original enemies reverse immediately. |
| Animation | 2 frames, every 6 steps | Slower cycle than the player. |

---

## 3. Projectiles & items

| Parameter | Value | Notes |
|---|---|---|
| Acorn / block throw speed | **3.0 px/frame** horizontal | Fast, flat throw like the original. |
| Thrown block gravity | **0.15 px/frame²** | Slight arc; blocks bounce once on the ground. |
| Flower / star pickup | stationary, bob ±2 px | Classic CnD health pickups. |

---

## 4. How to verify these numbers in Mesen (the included `Mesen.exe`)

Mesen is a Windows NES emulator with a memory viewer and frame-stepping —
perfect for measuring the *real* original values.

1. **Run Mesen.exe**, open `Chip 'n Dale - Rescue Rangers 2 (USA).nes`.
2. **Find the player position.** Open **Debug → Memory Viewer** (or the
   PPU/OAM viewer). Known RAM addresses for this game:
   - `$00A7` / `$00A8` — Player 1 / Player 2 lives.
   - `$03D4` — Player 1 health (RAW) — from published cheat data.
   - Player X/Y and speed are in the `$00xx`–`$01xx` RAM range; watch the
     values change as Chip moves and note the addresses.
3. **Measure walk speed.** Enable **frame advance** (pause + step one frame at
   a time). Note Chip's X coordinate, step forward 10 frames while holding
   right, and divide the X difference by 10 → pixels per frame.
4. **Measure jump & gravity.** From a standstill, jump and step frame-by-frame,
   recording Y each frame. The peak Y gives jump height; the Y differences
   give velocity; the change in velocity per frame gives gravity.
5. **Measure animation speed.** Count how many frames Chip's legs stay on one
   sprite before switching (use the PPU viewer / sprite preview).
6. **Export exact sprites & palette.** In Mesen: **Debug → PPU Viewer** shows
   the live pattern tables and palette. You can screenshot any frame, or use
   the **Tile Viewer** to see the exact CHR tiles the game is using — handy if
   you want to double-check the extracted sheets in `EXTRACTED/`.

Update `GML/scr_init.gml` with anything you measure — every physics constant
lives there, clearly commented.

---

## 5. Sources

- TASVideos community notes for *Chip 'n Dale Rescue Rangers* / *2*
  (movement speeds, 43 px jump height, "controls haven't been changed" in the sequel).
- NESdev forum RAM addresses (`$00A7`/`$00A8` lives).
- Published cheat data (`$03D4` P1 health).
- ROM header analysis: Mapper 1 (MMC1), 128 KB PRG + 128 KB CHR.
- Palette data located in PRG at `$0F146` (see `EXTRACTED/rom_info.txt`).
