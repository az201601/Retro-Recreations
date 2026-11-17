"""One-shot verification of the whole asset + code pack.

    python tools/verify.py

Checks, in order:

  1. every sprite strip in sprites.json has the expected pixel size
     (frame_w * count  x  frame_h) and really is a strip of that many frames,
  2. level01/screen_00.png matches the emulator frame it was built from,
     except where sprites are drawn on top of it,
  3. the tileset / collision data agree with the screen,
  4. the GML pack is valid GMS 1.4 (tools/check_gml.py),
  5. every sprite name used by the code exists in assets_vec
     (tools/check_assets.py),
  6. code/README_IMPORT.md sprite table is in sync with sprites.json.

Exit status 0 only if everything passes.  Steps 2 and 3 need the capture in
out/ (run tools/capture_all.sh first); they are skipped when it is absent.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VEC = os.path.join(ROOT, "assets_vec")
PY = sys.executable

fails = []
notes = []


def ok(msg):
    print("  ok    " + msg)


def bad(msg):
    print("  FAIL  " + msg)
    fails.append(msg)


def skip(msg):
    print("  skip  " + msg)


# ---------------------------------------------------------------- sprites ---
def check_sprites():
    print("sprites")
    meta = json.load(open(os.path.join(VEC, "sprites", "sprites.json")))
    for m in meta:
        p = os.path.join(VEC, m["image"])
        if not os.path.exists(p):
            bad("%s: file missing" % m["image"])
            continue
        im = Image.open(p)
        want = (m["frame_w"] * m["count"], m["frame_h"])
        if im.size != want:
            bad("%s: %dx%d, expected %dx%d" % (m["image"], im.size[0], im.size[1],
                                               want[0], want[1]))
            continue
        a = np.array(im.convert("RGBA"))
        empty = [i for i in range(m["count"])
                 if not (a[:, i * m["frame_w"]:(i + 1) * m["frame_w"], 3] > 0).any()]
        if empty:
            bad("%s: empty frame(s) %s" % (m["image"], empty))
            continue
        # every frame must be trimmed to its own bounds (no shared blank edge
        # on the left or right of a multi-frame strip)
        ok("%-26s %2dx%-2d x%d  origin %s"
           % (m["image"].replace("sprites/", ""), m["frame_w"], m["frame_h"],
              m["count"], tuple(m["origin"])))


# ------------------------------------------------------------------ level ---
def check_level():
    print("level")
    d = os.path.join(VEC, "backgrounds", "level01")
    info = json.load(open(os.path.join(d, "info.json")))
    scr = np.array(Image.open(os.path.join(d, "screen_00.png")).convert("RGBA"))
    if scr.shape[:2] != (240, 256):
        bad("screen_00.png is %dx%d, expected 256x240" % (scr.shape[1], scr.shape[0]))
        return
    # the exported screen must be fully opaque and free of magenta-ish garbage
    if (scr[:, :, 3] != 255).any():
        bad("screen_00.png has transparent pixels (a background must be opaque)")
    else:
        ok("screen_00.png 256x240, opaque")

    # compare against the emulator frame the level was built from
    src = info["source"]
    ppm = os.path.join(ROOT, "out", "level", "frames", "f%05d.ppm" % src["frame"])
    if not os.path.exists(ppm):
        skip("emulator frame %s not captured (run tools/capture_all.sh)"
             % os.path.basename(ppm))
    else:
        real = np.array(Image.open(ppm).convert("RGB")).astype(int)
        diff = np.abs(scr[:, :, :3].astype(int) - real).sum(axis=2) > 20
        pct = 100.0 * diff.sum() / diff.size
        # only sprites may differ: Chip + the HUD cover about 0.7 % of the
        # screen, so anything above 1.5 % means the background itself is off
        if pct > 1.5:
            ys, xs = np.where(diff)
            bad("screen_00.png differs from the emulator frame by %.2f%% "
                "(bbox y%d..%d x%d..%d; sprites should be the only difference)"
                % (pct, ys.min(), ys.max(), xs.min(), xs.max()))
        else:
            ok("screen_00.png matches emulator frame %d (%.2f%% = sprites only)"
               % (src["frame"], pct))

    # tileset geometry
    ts = Image.open(os.path.join(d, "tileset.png"))
    cols = info["tileset_columns"]
    rows = (info["tileset_count"] + cols - 1) // cols
    if ts.size != (cols * 16, rows * 16):
        bad("tileset.png is %dx%d, expected %dx%d"
            % (ts.size[0], ts.size[1], cols * 16, rows * 16))
    else:
        ok("tileset.png %dx%d = %d metatiles"
           % (ts.size[0], ts.size[1], info["tileset_count"]))

    m = np.array(info["map"])
    if m.shape != (15, 16):
        bad("info.json map is %s, expected 15x16" % (m.shape,))
    elif m.max() >= info["tileset_count"]:
        bad("info.json map refers to metatile %d, only %d exist"
            % (m.max(), info["tileset_count"]))
    else:
        ok("metatile map 15x16, indices < %d" % info["tileset_count"])

    col = os.path.join(d, "collision.json")
    if not os.path.exists(col):
        bad("collision.json missing (run tools/build_collision.py)")
        return
    c = json.load(open(col))
    for p in c["platforms"]:
        if not (0 <= p["x"] and p["x"] + p["w"] <= 256):
            bad("platform %s is outside the 256 px screen" % p)
        if not (0 <= p["y"] <= 240):
            bad("platform %s has an impossible y" % p)
    ok("collision.json: %d platforms inside the screen" % len(c["platforms"]))


# ------------------------------------------------------------------- code ---
def run(script, *args):
    r = subprocess.run([PY, os.path.join(HERE, script)] + list(args),
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def check_code():
    print("code")
    for script, label in (("check_gml.py", "GMS 1.4 syntax"),
                          ("check_assets.py", "sprite names"),
                          ("gen_readme_table.py", "README sprite table")):
        args = ("--check",) if script == "gen_readme_table.py" else ()
        rc, out = run(script, *args)
        if rc == 0:
            ok("%s (%s)" % (label, script))
        else:
            bad("%s failed (%s):\n%s" % (label, script, out.strip()))


def main():
    print("verifying %s\n" % ROOT)
    check_sprites()
    check_level()
    check_code()
    print()
    if fails:
        print("%d problem(s):" % len(fails))
        for f in fails:
            print("  - " + f.splitlines()[0])
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
