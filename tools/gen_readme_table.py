"""Regenerate the sprite table in code/README_IMPORT.md from sprites.json.

The import instructions list every sprite with its frame size, frame count and
origin.  Keeping that list by hand guarantees it drifts from the actual files,
so it is generated instead.

    python tools/gen_readme_table.py           # rewrite in place
    python tools/gen_readme_table.py --check   # exit 1 if the file is stale
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
JSON = os.path.join(ROOT, "assets_vec", "sprites", "sprites.json")
README = os.path.join(ROOT, "code", "README_IMPORT.md")
BEGIN = "<!-- BEGIN SPRITE TABLE -->"
END = "<!-- END SPRITE TABLE -->"

# extra sprites that are not animation strips and therefore not in sprites.json
EXTRA = [
    ("sprites/../ui/heart.png", "spr_heart", "8x8", 1, "4, 4"),
    ("sprites/../ui/hud_hearts.png", "spr_hud_hearts", "34x18", 1, "0, 0"),
    ("sprites/../ui/pixel.png", "spr_pixel", "1x1", 1, "**0, 0**"),
    ("sprites/../ui/title_screen.png", "spr_title_screen", "256x240", 1, "0, 0"),
]


def rows():
    meta = json.load(open(JSON))
    out = []
    for m in meta:
        out.append(("`%s`" % m["image"],
                    "`spr_%s_%s`" % (m["character"], m["anim"]),
                    "%dx%d" % (m["frame_w"], m["frame_h"]),
                    m["count"],
                    "%d, %d" % tuple(m["origin"])))
    for img, name, size, count, origin in EXTRA:
        out.append(("`%s`" % img.replace("sprites/../", ""), "`%s`" % name,
                    size, count, origin))
    return out


def build():
    lines = [BEGIN,
             "| 文件 | 精灵名 | 帧尺寸 | 帧数 | Origin |",
             "|---|---|---|---|---|"]
    for img, name, size, count, origin in rows():
        lines.append("| %s | %s | %s | %d | %s |" % (img, name, size, count, origin))
    lines.append(END)
    return "\n".join(lines)


def main():
    check = "--check" in sys.argv
    text = open(README, encoding="utf-8").read()
    i, j = text.find(BEGIN), text.find(END)
    if i < 0 or j < 0:
        raise SystemExit("sprite table markers missing from README_IMPORT.md")
    new = text[:i] + build() + text[j + len(END):]
    if check:
        if new != text:
            print("README_IMPORT.md sprite table is out of date")
            return 1
        print("README_IMPORT.md sprite table is up to date")
        return 0
    if new != text:
        open(README, "w", encoding="utf-8").write(new)
        print("regenerated sprite table (%d entries)" % len(rows()))
    else:
        print("sprite table already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
