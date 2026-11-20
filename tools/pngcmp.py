#!/usr/bin/env python3
"""
pngcmp.py - dependency-free PNG comparison for frame-accurate work.

    ./tools/pngcmp.py A.png B.png                 exact pixel diff + report
    ./tools/pngcmp.py A.png B.png --palette       ignore NES palette values
    ./tools/pngcmp.py DIR_A DIR_B                 whole directories (same names)
    ./tools/pngcmp.py DIR_A DIR_B --palette --first 20

Why a custom decoder: the sandbox has no PIL, and this has to keep working
with zero installs.  zlib handles the decompression; the PNG filter
reconstruction below covers all five filter types.

The `--palette` mode is the important one.  Two NES emulators can render
identical PPU output yet produce different RGB values because they ship
different palette tables.  Colour-by-colour comparison therefore lies about
accuracy.  In this mode each image is reduced to colour *classes*, a
bijection between the two images' colour sets is derived, and the images are
compared through that mapping.  What is left is genuine structural
difference (wrong tile, wrong position, wrong sprite), which is what a
recreation has to be judged on.
"""

from __future__ import annotations

import argparse
import os
import struct
import sys
import zlib
from collections import Counter, defaultdict

# --------------------------------------------------------------------------- #
# PNG decoding
# --------------------------------------------------------------------------- #


class Image:
    __slots__ = ("w", "h", "px")

    def __init__(self, w: int, h: int, px: list[tuple[int, int, int]]):
        self.w, self.h, self.px = w, h, px

    def row(self, y: int):
        return self.px[y * self.w:(y + 1) * self.w]

    def colour_counts(self) -> Counter:
        return Counter(self.px)


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def load_png(path: str) -> Image:
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not a PNG")

    pos = 8
    idat = bytearray()
    width = height = depth = ctype = 0
    palette: list[tuple[int, int, int]] = []
    trns = b""

    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        tag = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if tag == b"IHDR":
            width, height, depth, ctype, _comp, _filt, interlace = struct.unpack(">IIBBBBB", body)
            if interlace:
                raise ValueError(f"{path}: interlaced PNG not supported")
            if depth != 8:
                raise ValueError(f"{path}: bit depth {depth} not supported")
        elif tag == b"PLTE":
            palette = [tuple(body[i:i + 3]) for i in range(0, len(body), 3)]
        elif tag == b"tRNS":
            trns = body
        elif tag == b"IDAT":
            idat += body
        elif tag == b"IEND":
            break

    raw = zlib.decompress(bytes(idat))
    nch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    stride = width * nch
    out = bytearray(width * height * 3)
    prev = bytearray(stride)
    p = 0
    for y in range(height):
        ft = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if ft == 1:
            for i in range(nch, stride):
                line[i] = (line[i] + line[i - nch]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                c = prev[i - nch] if i >= nch else 0
                line[i] = (line[i] + _paeth(a, prev[i], c)) & 0xFF
        elif ft != 0:
            raise ValueError(f"{path}: bad filter {ft}")

        base = y * width * 3
        for x in range(width):
            o = x * nch
            if ctype == 2:
                r, g, b = line[o], line[o + 1], line[o + 2]
            elif ctype == 6:
                r, g, b = line[o], line[o + 1], line[o + 2]
            elif ctype == 3:
                idx = line[o]
                r, g, b = palette[idx] if idx < len(palette) else (0, 0, 0)
            elif ctype == 0:
                r = g = b = line[o]
            else:  # 4: grey + alpha
                r = g = b = line[o]
            out[base + x * 3: base + x * 3 + 3] = bytes((r, g, b))
        prev = line

    px = [tuple(out[i:i + 3]) for i in range(0, len(out), 3)]
    return Image(width, height, px)


# --------------------------------------------------------------------------- #
# Comparison
# --------------------------------------------------------------------------- #


def derive_palette_map(a: Image, b: Image, min_share: float = 0.9) -> dict:
    """Map each colour in `a` to the colour in `b` occupying the same pixels.

    The mapping is taken from co-occurrence counts.  A colour pair is
    accepted only if it dominates a colour's co-occurrences, so a genuine
    structural difference (a tile drawn with yet another colour) cannot be
    silently absorbed into the mapping.
    """
    pairs: dict[tuple, Counter] = defaultdict(Counter)
    for ca, cb in zip(a.px, b.px):
        pairs[ca][cb] += 1
    mapping = {}
    for ca, counter in pairs.items():
        (cb, n), = counter.most_common(1)
        mapping[ca] = cb if n >= min_share * sum(counter.values()) else None
    return mapping


def compare(a: Image, b: Image, palette_mode: bool) -> dict:
    if (a.w, a.h) != (b.w, b.h):
        return {"error": f"size mismatch {a.w}x{a.h} vs {b.w}x{b.h}"}

    mapping = derive_palette_map(a, b) if palette_mode else None
    diff_px = 0
    first = None
    per_row = Counter()
    per_col = Counter()
    unexplained = Counter()
    for i, (ca, cb) in enumerate(zip(a.px, b.px)):
        want = mapping[ca] if mapping is not None else ca
        if want is None:
            unexplained[ca] += 1
            diff_px += 1
        elif want != cb:
            diff_px += 1
            y, x = divmod(i, a.w)
            per_row[y] += 1
            per_col[x] += 1
            if first is None:
                first = (x, y, ca, cb)
    return {
        "pixels": a.w * a.h,
        "diff": diff_px,
        "first": first,
        "rows": per_row,
        "cols": per_col,
        "unexplained": unexplained,
        "map_size": len(mapping) if mapping is not None else 0,
    }


def summarise(name: str, r: dict, quiet_ok: bool = False) -> bool:
    if "error" in r:
        print(f"  {name}: {r['error']}   FAIL")
        return False
    pct = 100.0 * r["diff"] / r["pixels"]
    if r["diff"] == 0:
        if not quiet_ok:
            print(f"  {name}: identical ({r['pixels']} px)")
        return True
    print(f"  {name}: {r['diff']}/{r['pixels']} px differ ({pct:.2f}%)"
          + (f", palette classes {r['map_size']}" if r["map_size"] else ""))
    if r["unexplained"]:
        worst = r["unexplained"].most_common(3)
        print(f"      colours with no palette counterpart: {worst}")
    if r["first"]:
        x, y, ca, cb = r["first"]
        print(f"      first diff at ({x},{y}): {ca} vs {cb}")
    if r["rows"]:
        y = r["rows"].most_common(1)[0][0]
        print(f"      worst row y={y} ({r['rows'][y]} px)")
    return False


def frame_name(path: str) -> str:
    return os.path.basename(path)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--palette", action="store_true",
                    help="ignore NES palette values (compare structure only)")
    ap.add_argument("--first", type=int, default=0, help="stop after N differing files")
    ap.add_argument("--quiet", action="store_true", help="only report failures")
    args = ap.parse_args(argv)

    if os.path.isdir(args.a) and os.path.isdir(args.b):
        names = sorted(set(os.listdir(args.a)) & set(os.listdir(args.b)))
        names = [n for n in names if n.endswith(".png")]
        if not names:
            print("no common .png files", file=sys.stderr)
            return 2
        ok = bad = 0
        reported = 0
        for n in names:
            r = compare(load_png(os.path.join(args.a, n)),
                        load_png(os.path.join(args.b, n)), args.palette)
            if "error" not in r and r["diff"] == 0:
                ok += 1
                if not args.quiet:
                    print(f"  {n}: ok")
            else:
                bad += 1
                if reported < args.first or args.first <= 0:
                    summarise(n, r)
                    reported += 1
        print(f"{ok}/{len(names)} frames identical"
              f" ({'palette-normalised' if args.palette else 'exact'})")
        return 0 if bad == 0 else 1

    r = compare(load_png(args.a), load_png(args.b), args.palette)
    return 0 if summarise(f"{frame_name(args.a)} vs {frame_name(args.b)}", r) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
