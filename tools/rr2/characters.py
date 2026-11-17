"""Curated character animation extraction.

The automatic catalog is useful for reference, but a usable character set needs
explicit frame ranges. This module pulls named animations out of the recorded
traces by (trace, frame) so every pixel comes straight from the emulator.
"""
import os

from . import objects as O, sprites as S

# name -> (trace name, [(first_frame, last_frame, step)])
CURATED = {
    # title screen cast: the two big poses on the logo screen
    "title_chip": ("menu", [(1000, 1000, 1)]),
    "title_dale": ("menu", [(1000, 1000, 1)]),
}


def frame_objects(rec, min_w=12, min_h=12, max_w=48, max_h=56):
    return [o for o in O.cluster(rec)
            if min_w <= o["x1"] - o["x0"] <= max_w
            and min_h <= o["y1"] - o["y0"] <= max_h]


def collect(recs_by_name, spec, render_fn):
    """Returns list of (frame_image, source_frame, box) for one animation spec."""
    out = []
    for trace_name, frames in spec:
        recs = {r.frame: r for r in recs_by_name[trace_name]}
        for (a, b, step) in frames:
            for f in range(a, b + 1, step):
                rec = recs.get(f)
                if rec is None:
                    continue
                for o in frame_objects(rec):
                    img = render_fn(rec, o)
                    out.append((img, rec.frame, o))
    return out


# Curated per-character animation sets, chosen from the on-screen inspection:
#   intro trace: 3..13 = Chip walking/standing, 14/17 = Dale, 18..25 = the
#   doctor + Gadget waving, 26..37 = Gadget standing/waving, 38..57 = the
#   big intro Chip&Dale pose, 58/59 = Dale crouch.
CHARACTERS = {
    "chip_walk": ("intro", [(622, 700, 4)]),
    "chip_stand": ("intro", [(1310, 1350, 8)]),
    "dale_stand": ("intro", [(1630, 1660, 4)]),
    "chip_crouch": ("intro", [(2840, 2860, 4)]),
    "doctor": ("intro", [(3180, 3200, 2)]),
    "gadget": ("intro", [(4860, 4890, 2)]),
    "gadget_wave": ("intro", [(5810, 5820, 1)]),
    "logo_chipdale": ("intro", [(5824, 5862, 2)]),
    "dale_crouch": ("intro", [(5912, 5920, 2)]),
}
