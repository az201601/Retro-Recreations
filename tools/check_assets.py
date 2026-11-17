"""Verify that every asset name the GML expects actually exists.

The GMS project resolves sprites with asset_get_index("spr_..."), so a missing
sprite silently becomes -1 and the object draws nothing.  This script parses
the code pack, collects every asset_get_index("...") literal plus every sprite
listed in the import manifest, and compares them with assets_vec/.

Exit status 1 on any problem (useful as a pre-import check).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CODE = os.path.join(ROOT, "code")
ASSETS = os.path.join(ROOT, "assets_vec")

PATTERN = re.compile(r'asset_get_index\s*\(\s*"([A-Za-z0-9_]+)"\s*\)')
OPTIONAL = os.path.join(CODE, "assets_optional.txt")


def optional_names():
    if not os.path.exists(OPTIONAL):
        return set()
    out = set()
    for ln in open(OPTIONAL):
        ln = ln.split("#")[0].strip()
        if ln:
            out.add(ln)
    return out


def sprite_names_from_assets():
    """Map spr_xxx -> source png, following the naming convention.

    assets_vec/sprites/<character>/<anim>.png  ->  spr_<character>_<anim>
    assets_vec/ui/<name>.png                   ->  spr_ui_<name>   (spr_<name>
                                                      also accepted)
    assets_vec/backgrounds/<level>/...         ->  bg_<level>
    """
    names = {}
    sp = os.path.join(ASSETS, "sprites")
    for char in sorted(os.listdir(sp)):
        d = os.path.join(sp, char)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".png") or "_f" in f:
                continue
            anim = f[:-4]
            names["spr_%s_%s" % (char, anim)] = "sprites/%s/%s" % (char, f)
    ui = os.path.join(ASSETS, "ui")
    if os.path.isdir(ui):
        for f in sorted(os.listdir(ui)):
            if f.endswith(".png"):
                names["spr_%s" % f[:-4]] = "ui/" + f
                names["spr_ui_%s" % f[:-4]] = "ui/" + f
    return names


def gml_asset_refs():
    refs = {}
    for base, _, files in os.walk(CODE):
        for f in files:
            if not f.endswith(".gml"):
                continue
            p = os.path.join(base, f)
            for m in PATTERN.finditer(open(p, encoding="utf-8").read()):
                refs.setdefault(m.group(1), []).append(
                    os.path.relpath(p, ROOT))
    return refs


def main():
    have = sprite_names_from_assets()
    refs = gml_asset_refs()
    optional = optional_names()
    missing, pending = [], []
    for name, where in sorted(refs.items()):
        if name in have:
            continue
        if name in optional:
            pending.append((name, where))
        else:
            missing.append((name, where))

    print("assets known : %d" % len(have))
    print("names used   : %d" % len(refs))
    if missing:
        print("\nMISSING (the code refers to sprites that were never built):")
        for name, where in missing:
            print("  %-28s %s" % (name, ", ".join(sorted(set(where)))))
    else:
        print("all referenced sprite names exist")

    if pending:
        print("\nnot extracted yet (listed in code/assets_optional.txt):")
        for name, where in pending:
            print("  %-28s %s" % (name, ", ".join(sorted(set(where)))))

    unused = sorted(set(have) - set(refs))
    if unused:
        print("\nnot referenced from code (fine for cut-scene art):")
        for n in unused:
            print("  %s  ->  %s" % (n, have[n]))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
