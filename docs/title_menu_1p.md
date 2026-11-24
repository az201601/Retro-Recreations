# Single-player title menu — GMS 1.4.1760

This is the next boot-flow room after the spotlight intro. The original title menu offers both 1P and 2P; this build keeps the original selected **1player** row and removes the 2player row as requested. The menu background is static while it is shown, so one 256×240 capture is sufficient.

## Files

- `extracted/title_menu/title_1player.png` — full-screen title/menu image, with only the 1player choice visible.
- `extracted/audio/music_menu.wav` — clean title-menu music from the no-input run, beginning with the title-screen appearance; 48 kHz mono, 16-bit, about 37.3 seconds.
- `extracted/audio/sfx_menu_select.wav` — the separate 0.25-second selection sound isolated from the START transition, 48 kHz mono, 16-bit.
- `code/06_obj_title_Create.gml` — starts the menu music loop.
- `code/07_obj_title_Step.gml` — Enter/Space plays the selection sound and chooses the sole 1-player option.
- `tools/extract_one_player_menu.py` — repeatable extraction/masking/audio capture script that writes separate music and SFX files.

The reference was captured at NES frame 1006 after START was pressed at frame 1000. The title screen is present by frame 900; the clean music capture now begins there instead of at the later START press, preserving the music's opening. The separate 0.25-second selection SFX is isolated by subtracting synchronized no-input audio from the START run over source frames 1000–1015. The 2player label alone is removed by filling its rectangle (x=96..175, y=204..220) with the sampled NES backdrop color; the rest of the title screen remains the original emulator image.

## Import/build in GMS

1. Create a background resource named `BG_title_1P`; load `extracted/title_menu/title_1player.png`.
2. Create sound resources named `MUS_menu` and `SFX_menu_select`; load `extracted/audio/music_menu.wav` and `extracted/audio/sfx_menu_select.wav` respectively.
3. Create an object named `obj_title` with no sprite. Add the Create event from `code/06_obj_title_Create.gml` and the Step event from `code/07_obj_title_Step.gml`.
4. Create `rm_title` at 256×240 and 60 steps per second. Set its background to `BG_title_1P`, place one `obj_title` instance, and set its room order immediately after `rm_intro`.
5. Put `rm_character_select` next in room order when that scene is ready. The Step code uses `room_goto_next()`, so pressing Enter/Space continues to that next room. There is no 2-player path.

## Re-extract

With the emulator frontend built as documented in `tools/README.md`, run from the repository root:

```bash
python3 tools/extract_one_player_menu.py
```

The raw screenshot and the complete boot-to-menu WAV are temporary files under ignored `tools/out/`; the script writes the masked title image and the isolated menu-music segment to their checked-in output paths.
