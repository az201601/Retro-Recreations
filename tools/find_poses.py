"""List the distinct OAM poses of the player in a trace.

Rendering an animation frame needs a (trace, frame) pair; this prints the first
frame of every distinct pose, which is exactly what goes into ANIMS in
tools/build_assets.py.

    python tools/find_poses.py pi_holdR
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import trace as tracemod  # noqa: E402


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "game"
    y0 = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    y1 = int(sys.argv[3]) if len(sys.argv) > 3 else 196
    path = os.path.join(ROOT, "out", name, "trace.bin")
    recs = tracemod.load(path)

    poses = {}
    for rec in recs:
        sp = [s for s in rec.visible_sprites if y0 <= s["y"] < y1]
        if not sp:
            continue
        top = min(s["y"] for s in sp)
        key = tuple(sorted((s["tile"], s["pal"], s["flipx"], s["x"] - min(q["x"] for q in sp),
                            s["y"] - top) for s in sp))
        if key not in poses:
            poses[key] = (rec.frame,
                          min(s["x"] for s in sp), top,
                          max(s["x"] for s in sp) + 8,
                          max(s["y"] for s in sp) + 16,
                          len(sp))
    print("%s: %d frames, %d distinct poses in y=%d..%d"
          % (name, len(recs), len(poses), y0, y1))
    for _, v in sorted(poses.items(), key=lambda kv: kv[1][0]):
        print("  trace=%-10s frame=%-6d box=(%3d,%3d)-(%3d,%3d) sprites=%d"
              % ((name,) + v))


if __name__ == "__main__":
    main()
