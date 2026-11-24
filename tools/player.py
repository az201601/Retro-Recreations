"""Locate the player's sprite block in OAM.

The player is drawn as a run of consecutive OAM entries. Tracking a fixed
index is a trap: the block moves between OAM slots as the character changes
state, so a fixed index can latch onto a hidden sprite (y = 240) or an enemy
and then report "no movement" no matter what is pressed. Cluster the active
sprites and take the biggest run instead.
"""

from __future__ import annotations

from pathlib import Path

from nes_state import load_state


def _clusters(oam: bytes, max_y: int = 232):
    runs = []
    run = []
    for i in range(64):
        y = oam[i * 4]
        if y < max_y:
            run.append(i)
        elif run:
            runs.append(run)
            run = []
    if run:
        runs.append(run)
    return [r for r in runs if len(r) >= 3]


def player_box(state_path: Path, rom) -> tuple[int, int, int, int, int]:
    """Return (min_x, min_y, max_x, max_y, sprite_count) for the player.

    Raises LookupError when no plausible block is on screen (death frames).
    """
    st = load_state(state_path, rom)
    oam = st.oam
    runs = _clusters(oam)
    if not runs:
        raise LookupError("no active sprites")
    run = max(runs, key=len)
    xs = [oam[i * 4 + 3] for i in run]
    ys = [oam[i * 4] for i in run]
    return min(xs), min(ys), max(xs), max(ys), len(run)


def player_pos(state_path: Path, rom) -> tuple[int, int, int, int]:
    """(screen_x_centre, screen_y_top, cam, cam_y) for the player."""
    st = load_state(state_path, rom)
    cx, fx, cy = st.scroll()
    cam = (st.ppuctrl & 1) * 256 + cx * 8 + fx
    try:
        x0, y0, x1, y1, _ = player_box(state_path, rom)
    except LookupError:
        return -1, 999, cam, cy * 8
    return (x0 + x1) // 2, y0, cam, cy * 8
