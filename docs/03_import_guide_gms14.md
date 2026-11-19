# Import guide — GMS 1.4.1760 (beginner, click-by-click)

The project owner is a **complete beginner** to GameMaker: Studio 1.4. Every transfer uses this style: exact mouse clicks, exact names to type, paste-ready code, and a "you should see" check at the end. No prior GameMaker knowledge is assumed anywhere in this guide or in future transfer instructions.

## How transfers work from now on

Each transfer round you will get:

1. **You will need** — the list of files from this repo (e.g. `gml/scripts/...`).
2. **Steps** — numbered, one action per step ("right-click X, choose Y, type Z").
3. **You should see** — exactly what success looks like on screen, so you can self-check.
4. **If it goes wrong** — copy the *exact* error text GameMaker shows (or describe the window) and send it back.

Terms used below: the **resource tree** is the panel (left side by default) listing Sprites, Sounds, Backgrounds, Scripts, Objects, Rooms, etc. The **green check mark (✓)** button in an editor window means "OK / keep"; the **red X** means "cancel / throw away". GameMaker compiles and opens a separate game window when you run the game.

---

## Part 1 — One-time setup: create the project

Do this once only.

1. Open **GameMaker: Studio 1.4.1760**.
2. If a Welcome window appears, click the **New** tab. (If not: menu **File → New Project**.)
3. Choose an **Empty Project** (blank template — not a demo).
4. Name it e.g. `ChipNDale2_GMS14` and choose a folder you'll be able to find again. Click **Create**.
5. You now see the main window with the resource tree on the left. It contains empty groups: Sprites, Sounds, Backgrounds, Paths, Scripts, Shaders, Fonts, Timelines, Objects, Rooms, Included Files, Extensions, Macros, and more. We only use **Scripts**, **Objects** and **Rooms** for now.
6. Press **Ctrl+S** (or **File → Save**) so the project exists on disk before we add anything.

Nothing else is needed yet: no sprites, no sounds. The M0 test draws its own text with code.

## Part 2 — Add the seven scripts

The script names must match the file names in `gml/scripts/` **exactly**, including the `scr_` prefix and underscores. GameMaker code refers to scripts by these names; one typo causes an "Unknown function" error later.

Repeat these steps for each of the seven scripts listed below:

1. In the resource tree, **right-click** the **Scripts** group.
2. Choose **Create Script**. A code-editor window opens.
3. At the **top of that code window** there is a small name box (it may say `script0` or similar). Delete what's there and type the script name exactly, e.g. `scr_nes_init`.
   - If you don't see a name box: close the window, then in the resource tree **right-click** the new script → **Rename**, and type the name there.
4. Click inside the big code area, select all (**Ctrl+A**), delete (**Delete** key), then **paste** (Ctrl+V) the *entire* contents of the matching `.gml` file from this repo.
5. Click the **green check mark (✓)** to save and close that script.

Create these seven, in this order (order doesn't matter to GameMaker, but this keeps you organised):

| # | Script name to type | File to copy from (in this repo) |
|---|---|---|
| 1 | `scr_nes_init` | `gml/scripts/scr_nes_init.gml` |
| 2 | `scr_input_poll` | `gml/scripts/scr_input_poll.gml` |
| 3 | `scr_fp_make` | `gml/scripts/scr_fp_make.gml` |
| 4 | `scr_fp_to_pix` | `gml/scripts/scr_fp_to_pix.gml` |
| 5 | `scr_s8` | `gml/scripts/scr_s8.gml` |
| 6 | `scr_game_state_step` | `gml/scripts/scr_game_state_step.gml` |
| 7 | `scr_nes_frame` | `gml/scripts/scr_nes_frame.gml` |

Beginner traps to avoid:
- **Keep the first line** of each pasted file (it starts with `///`). That's a normal comment in GML and gives the editor argument hints. It does not break anything.
- Paste the *whole* file, including comments. Comments start with `//` and are ignored by the game.
- Script names have **no spaces**. `scr_nes_init`, never `scr nes init`.

## Part 3 — Create the object `obj_nes_core` with 3 events

An "object" in GameMaker is a thing that runs code. Ours has no picture (sprite) — it just runs the core logic and draws debug text.

1. In the resource tree, **right-click Objects → Create Object**. The Object Properties window opens.
2. In the **Name** box (top-left of that window), type exactly: `obj_nes_core`
3. Make sure the **Visible** check box is ticked (it is by default). Leave **Sprite** empty (`<no sprite>`).
4. Now add the three events. For each row in the table below:
   a. Click the **Add Event** button (bottom area of the object window). A list of event types appears.
   b. Choose the event as described in the table (Step and Draw open a small sub-list — pick the plain one).
   c. The event appears in the **Events** list on the left of the object window, and an empty **Actions** list appears on the right.
   d. On the far right of the object window is a column of action tabs. Click the **Control** tab.
   e. Find the action called **Execute Code** (an icon that looks like a sheet of paper). **Drag it** into the empty Actions list. ⚠️ Use **Execute Code**, *not* "Execute Script" — they are different actions.
   f. **Double-click** the Execute Code action you just added. A code window opens.
   g. Paste the entire contents of the matching file (see table), then click the **green check mark ✓**.
5. After all three events are added, click the **green check mark ✓** on the Object Properties window to save the object.

| Event to add | How to choose it | File to paste |
|---|---|---|
| Create | Add Event → **Create** | `gml/objects/obj_nes_core/Create.gml` |
| Step | Add Event → **Step → Step** (the normal one) | `gml/objects/obj_nes_core/Step.gml` |
| Draw | Add Event → **Draw → Draw** (the plain one) | `gml/objects/obj_nes_core/Draw.gml` |

Beginner traps to avoid:
- An event with **no action in its Actions list does nothing at all**. The pasted code only exists once you've dragged in Execute Code and pasted into it. This is the #1 beginner mistake.
- Each event needs its **own** Execute Code action — don't paste all three files into one event.
- You can re-open any event's code later: select the event, then double-click its Execute Code action.

## Part 4 — Create the room and place the object

A "room" is a screen/level. GameMaker runs the **first room in the Rooms list** when the game starts.

1. In the resource tree, **right-click Rooms → Create Room**. The Room Editor opens.
2. Click the **settings** tab (near the top of the room editor).
   - **Width:** change to `256`
   - **Height:** change to `240`
   - **Speed:** change to `60`
3. Click the **views** tab.
   - Tick **Enable the use of Views**.
   - Click **View 0** in the list, then tick **Visible when room starts**.
   - Under **View in room**: set X `0`, Y `0`, W `256`, H `240`.
   - Under **Port on screen**: set X `0`, Y `0`, W `768`, H `720`. (This is just the window size — 3× the NES resolution.)
   - Leave "Object following" as `<no object>` and Hbor/Hborder etc. as they are.
4. Click the **objects** tab.
   - Click the object picker button (it shows a small icon/dropdown) and choose **obj_nes_core**.
   - **Left-click once** anywhere inside the room area. A marker for the object appears. Its exact position does not matter.
5. Click the **green check mark ✓** to save the room. (If asked to confirm changes, click Yes/OK.)
6. Look at the resource tree: under **Rooms** your room should be the only one. If you ever have several rooms, the top one runs first — drag this room to the top if needed.
7. Save the project: **Ctrl+S**.

## Part 5 — Run it, and what success looks like

1. Make sure the target at the top of the main window says **Windows** (default).
2. Click the **green play arrow ▶** on the top toolbar (or press **F5** — "Run Normally").
3. The first run can take a little while to compile. A game window opens, **768×720**.

**You should see:** a black window with small white text in the top-left corner, roughly:

```
FRAME 1234
PAD 0 PRESS 0
STATE 0
```

- `FRAME` counts up continuously, about 60 numbers per second.
- Press and hold the **Right arrow key**: `PAD` becomes **128**. Release it: back to **0**.
- Check the other controls the same way (hold each, read PAD):

| Key | Pad button | PAD value |
|---|---|---|
| X | A | 1 |
| Z | B | 2 |
| Shift | Select | 4 |
| Enter | Start | 8 |
| Up arrow | Up | 16 |
| Down arrow | Down | 32 |
| Left arrow | Left | 64 |
| Right arrow | Right | 128 |

  Combinations add up (e.g. Right + X = 129). While you *first* press a key, `PRESS` briefly shows that key's value for one frame — you may only catch it flickering; that's expected.
- `STATE` stays **0**.

4. To stop: close the game window (the X on the game window). If GameMaker says the game is still running, click the **red square stop button** in the GameMaker toolbar.

If FRAME counts, PAD changes with the keys, and STATE is 0 — **the M0 transfer worked**. 🎉

## Part 6 — Troubleshooting

| What you see | Likely cause | Fix |
|---|---|---|
| Error window mentioning `Unknown function or script: scr_nes_init` (or similar) | A script is missing or its name doesn't exactly match the file name | Compare each script's name in the tree against Part 2, character by character. Rename with right-click → Rename |
| Compile error window with line numbers | Paste mistake (part of a file missing, or code pasted into the wrong script/event) | Re-paste the whole file from the repo. If stuck, copy the *full* error text and send it back — don't try to guess-edit |
| Game window opens but is **empty black, no text** | `obj_nes_core` isn't in the room, or its Draw event has no Execute Code action | Open the room's objects tab and check the marker exists; open the object and check each event has one Execute Code action with code in it |
| Text shows but FRAME is frozen or PAD never changes | Step event missing/empty, or the game window doesn't have keyboard focus | Check the Step event's code; click on the game window once so it has focus, then press keys |
| Window is tiny / huge / stretched | Port on screen values differ | Re-check Part 4 step 3 (port W 768, H 720) |
| Game runs very slowly, FRAME crawls | Room speed wrong | Room settings tab → Speed 60 (our Create code also sets this, but the room value is the safety net) |
| Something else entirely | — | Describe the window / copy the error text exactly and send it back. That is always useful and never your fault |

## Notes for future transfers

- **You will never need to type code by hand.** Everything is copy-paste from files in this repo; if a step ever seems to ask you to invent code, ask first.
- New graphics will arrive as PNG files in `extracted/` with their own click-by-click import steps (create sprite/background, set size/origin exactly as specified).
- When a transfer adds a script or event, the steps above (Parts 2–3) repeat with the new name/file — the shape of the task never changes.
