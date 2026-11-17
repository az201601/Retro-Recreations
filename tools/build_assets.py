"""Final, curated asset build for the GameMaker 1.4 port.

Everything is pulled from the emulator traces by explicit (trace, frame, box)
rules, so the output is pixel exact and reproducible:

  assets_vec/
     sprites/<char>/<anim>.png        horizontal animation strip (1:1 pixels)
     sprites/<char>/<anim>_fNN.png    individual frames
     sprites/sprites.json             frame rects, origins, timings
     backgrounds/*.png                level panoramas (sprite free)
     ui/*.png                         HUD, title, logo art
     palettes/palettes.json           NES palette RAM snapshots + RGB values
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import trace as tracemod  # noqa: E402
from nesrom import NesRom  # noqa: E402
from rr2 import sprites as S, objects as O  # noqa: E402

OUT = os.path.join(ROOT, "assets_vec")
ROM = NesRom()

TRACES = {}
for name in ("menu", "intro", "play", "game", "hc_jump", "hc_runR", "hc_runL",
             "hc_throw", "hc_updown", "scan", "pan", "pi_holdR", "jt_A", "pb",
             "mv_g", "mv_a", "mv_b", "mv_c", "mv_d", "mv_e", "mv_f", "hero"):
    p = os.path.join(ROOT, "out", name, "trace.bin")
    if os.path.exists(p):
        TRACES[name] = {r.frame: r for r in tracemod.load(p)}


def path(*p):
    full = os.path.join(OUT, *p)
    os.makedirs(os.path.dirname(full) if os.path.splitext(full)[1] else full, exist_ok=True)
    return full


def render(trace_name, frame, box=None, min_size=(8, 8), max_size=(96, 96)):
    """Render one OAM object from a trace frame.

    box: (x0, y0) of the wanted object, or None.
    Objects are clustered and merged, so a stable anchor is either the exact
    top-left corner or (when the sprite moves) the vertical band it sits in.
    """
    rec = TRACES[trace_name][frame]
    ch = S.ChrWindows(ROM.chr, rec.chr_lo, rec.chr_hi, rec.chr_mode)
    cands = []
    for o in O.cluster(rec):
        w, h = o['x1'] - o['x0'], o['y1'] - o['y0']
        if not (min_size[0] <= w <= max_size[0] and min_size[1] <= h <= max_size[1]):
            continue
        if box:
            if abs(o['y0'] - box[1]) > 1:
                continue
            if box[0] is not None and abs(o['x0'] - box[0]) > 1:
                continue
        cands.append(o)
    if not cands:
        return None
    # prefer the largest object in the band (the character, not a particle)
    cands.sort(key=lambda o: -((o['x1'] - o['x0']) * (o['y1'] - o['y0'])))
    o = cands[0]
    img = O.render_object(rec, ch, o)
    a = img[:, :, 3] > 0
    if not a.any():
        return None
    ys, xs = a.nonzero()
    return img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def render_band(trace_name, frame, y0=120, y1=196, x1=220):
    """Render the character from an OAM band (HUD sprites excluded).

    The HUD lives below y=196 and is drawn with the same palette, so an
    automatic cluster happily merges it into the hero.  Selecting the sprites
    by band is both simpler and exact.
    """
    rec = TRACES[trace_name][frame]
    ch = S.ChrWindows(ROM.chr, rec.chr_lo, rec.chr_hi, rec.chr_mode)
    hh = 16 if rec.long_sprites else 8
    sp = [s for s in rec.visible_sprites
          if y0 <= s["y"] < y1 and s["x"] < x1]
    if not sp:
        return None
    box = dict(sprites=sp,
               x0=min(s["x"] for s in sp), y0=min(s["y"] for s in sp),
               x1=max(s["x"] for s in sp) + 8, y1=max(s["y"] for s in sp) + hh)
    img = O.render_object(rec, ch, box)
    if not (img[:, :, 3] > 0).any():
        return None
    return trim_to(img)


def trim_to(img):
    a = img[:, :, 3] > 0
    ys, xs = a.nonzero()
    return img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def pad_to(img, w, h):
    out = np.zeros((h, w, 4), np.uint8)
    oy = h - img.shape[0]
    ox = (w - img.shape[1]) // 2
    out[oy:oy + img.shape[0], ox:ox + img.shape[1]] = img
    return out


# ---------------------------------------------------------------- animations
# (name, trace, frames, box filter) - boxes taken from the OAM inspection
ANIMS = {
    # Chip, in-level (chapter 1, the burger-counter house).
    # Every entry is (trace, frame) and is rendered from the OAM band y=120..196
    # so the HUD never leaks in.  Frames were located by grouping identical OAM
    # poses over the whole recording (see tools/RECON.md).
    "chip": {
        # standing / waiting
        "idle":  [("pi_holdR", 5617), ("pi_holdR", 5991)],
        # 4-step run cycle, captured while Chip actually accelerates (5600..5633)
        "walk":  [("pi_holdR", 5601), ("pi_holdR", 5609),
                  ("pi_holdR", 5625), ("pi_holdR", 5633)],
        # jump: crouch -> launch -> tuck
        "jump":  [("mv_g", 5734), ("mv_g", 5744)],
        # fall / descend
        "fall":  [("mv_g", 5752), ("mv_g", 5860)],
        # landing squash: knees bent, right after touching down
        "land":  [("mv_a", 5718)],
        # pushing / carrying a crate
        "push":  [("pi_holdR", 5625)],   # carrying: same pose, arms up
        # overhead throw, two frames
        "throw": [("pb", 5700), ("pb", 5609)],
        # NOTE: no clean knock-back pose was captured yet (the only hit frames
        # are one-line OAM glitches); the GML aliases chip_hurt -> chip_fall.
    },
    # Cut-scene cast (Gadget, Dale, the doctor, the title artwork) lives in the
    # FATCAM intro, which starts after the 6000-frame window of out/intro; see
    # tools/RECON.md.  scr_anim_init already looks for those sprite names and
    # simply skips the ones that are not imported yet, so nothing breaks while
    # this section is empty.
}


def build_sprites():
    meta = []
    for char, anims in ANIMS.items():
        for anim, keys in anims.items():
            frames = []
            for key in keys:
                if len(key) == 2:
                    tn, fr = key
                    box = None
                else:
                    tn, fr, box = key
                if tn not in TRACES or fr not in TRACES[tn]:
                    print("  .. missing trace/frame", tn, fr)
                    continue
                if len(key) == 2:
                    img = render_band(tn, fr)
                else:
                    img = render(tn, fr, box)
                if img is None:
                    continue
                frames.append((trim_to(img), tn, fr))
            if not frames:
                print("  !! no frames for", char, anim)
                continue
            w = max(f[0].shape[1] for f in frames)
            h = max(f[0].shape[0] for f in frames)
            padded = [pad_to(f[0], w, h) for f in frames]
            d = path("sprites", char)
            for i, f in enumerate(padded):
                Image.fromarray(f, "RGBA").save(os.path.join(d, "%s_f%02d.png" % (anim, i)))
            strip = np.concatenate(padded, axis=1)
            Image.fromarray(strip, "RGBA").save(os.path.join(d, "%s.png" % anim))
            meta.append(dict(
                character=char, anim=anim,
                image="sprites/%s/%s.png" % (char, anim),
                frame_w=int(w), frame_h=int(h), count=len(frames),
                origin=[int(w // 2), int(h)],
                sources=[dict(trace=f[1], frame=f[2]) for f in frames],
            ))
            print("  %-12s %-8s %d frames %dx%d" % (char, anim, len(frames), w, h))
    with open(path("sprites", "sprites.json"), "w") as f:
        json.dump(meta, f, indent=1)
    return meta


# ---------------------------------------------------------------- ui + bg
def build_ui():
    from rr2 import bg as BG

    # ---- HUD -------------------------------------------------------------
    # The HUD is made of sprites: a small portrait box at x=16..32, y=201..217
    # and three hearts at y=209..217.  Render just that OAM band on a clean
    # transparent canvas so it can be dropped straight into a room.
    rec = TRACES["game"][5400]
    ch = S.ChrWindows(ROM.chr, rec.chr_lo, rec.chr_hi, rec.chr_mode)
    hh = 16 if rec.long_sprites else 8
    hud = np.zeros((18, 34, 4), np.uint8)
    sp = [s for s in rec.visible_sprites if s["y"] >= 197 and s["x"] < 40]
    if sp:
        box = dict(sprites=sp,
                   x0=min(s["x"] for s in sp), y0=min(s["y"] for s in sp),
                   x1=max(s["x"] for s in sp) + 8,
                   y1=max(s["y"] for s in sp) + hh)
        img = O.render_object(rec, ch, box)
        a = img[:, :, 3] > 0
        ys, xs = a.nonzero()
        crop = img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        hud[:crop.shape[0], :crop.shape[1]] = crop
    Image.fromarray(hud, "RGBA").save(path("ui", "hud_hearts.png"))

    # single heart: an 8 x 8 sprite (gold outline + red fill), drawn at
    # x = 16, 24, 32 / y = 209 in the NES HUD
    Image.fromarray(hud[8:16, 0:8], "RGBA").save(path("ui", "heart.png"))

    # ---- 1x1 white pixel: scaled by obj_ground to build solid rectangles
    px = np.zeros((1, 1, 4), np.uint8)
    px[0, 0] = (255, 255, 255, 255)
    Image.fromarray(px, "RGBA").save(path("ui", "pixel.png"))

    # full title screen reference (background only, no sprites)
    v = rec.vram_addr
    # menu screen from the title trace
    for tn, fr, name in (("menu", 1000, "title_screen"), ("intro", 1630, "scene_house")):
        rec = TRACES[tn][fr]
        ch = S.ChrWindows(ROM.chr, rec.chr_lo, rec.chr_hi, rec.chr_mode)
        img = BG.render_screen(rec, ch)
        Image.fromarray(img, "RGBA").save(path("ui", name + ".png"))


def build_backgrounds():
    src = os.path.join(ROOT, "assets", "levels")
    for name in os.listdir(src) if os.path.isdir(src) else []:
        if name.endswith(".png"):
            Image.open(os.path.join(src, name)).save(path("backgrounds", name))


def build_palettes():
    out = {}
    for tn in ("menu", "intro", "game", "play"):
        if tn not in TRACES:
            continue
        sets, seen = [], set()
        for fr in sorted(TRACES[tn]):
            rec = TRACES[tn][fr]
            key = bytes(rec.palette)
            if key in seen:
                continue
            seen.add(key)
            sets.append(dict(
                frame=fr,
                hex=["%02X" % b for b in rec.palette],
                hex_bg=[["%02X" % b for b in rec.palette[i * 4:i * 4 + 4]] for i in range(4)],
                hex_sprite=[["%02X" % b for b in rec.palette[16 + i * 4:16 + i * 4 + 4]]
                            for i in range(4)],
                rgb_bg=[[list(S.color(rec.palette[i * 4 + k])) for k in range(4)]
                        for i in range(4)],
                rgb_sprite=[[list(S.color(rec.palette[16 + i * 4 + k])) for k in range(4)]
                            for i in range(4)],
            ))
        out[tn] = sets
    with open(path("palettes", "palettes.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("  palettes:", {k: len(v) for k, v in out.items()})


def main():
    print("sprites:")
    build_sprites()
    print("ui:")
    build_ui()
    build_backgrounds()
    print("palettes:")
    build_palettes()
    print("done ->", OUT)


if __name__ == "__main__":
    main()
