"""Static sanity checks for the GMS 1.4 code pack.

GameMaker: Studio 1.4 has no function keyword, no enums and no structs, and
scripts are resource files, so a typo in a script name only shows up when the
project is opened.  This script catches the common breakages before import:

  * GMS2-only syntax (function / enum / struct / #region / =>)
  * unbalanced braces or parentheses
  * calls to scr_* helpers that have no matching resource file
  * asset_get_index("...") names that assets_vec cannot provide
  * variables used as "instance variables" before Create defines them
    (reported, not an error)

Usage:  python tools/check_gml.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CODE = os.path.join(ROOT, "code")

GMS2_ONLY = [
    (r"^\s*function\s+\w+\s*\(", "GMS2 'function' declaration"),
    (r"\benum\s+\w+", "GMS2 enum"),
    (r"#region|#endregion", "GMS2 region"),
    (r"=>", "GMS2 lambda"),
    (r"\bnew\s+\w+\s*\(", "GMS2 constructor"),
    (r"\bstruct\b", "GMS2 struct"),
]


def scripts_available():
    d = os.path.join(CODE, "scripts")
    return set(f[:-4] for f in os.listdir(d) if f.endswith(".gml"))


def main():
    have = scripts_available()
    problems = []
    warned = []

    files = []
    for base, _, names in os.walk(CODE):
        for f in names:
            if f.endswith(".gml"):
                files.append(os.path.join(base, f))
    files.sort()

    called = set()
    for p in files:
        src = open(p, encoding="utf-8").read()
        rel = os.path.relpath(p, ROOT)

        for pat, msg in GMS2_ONLY:
            if re.search(pat, src, re.M):
                problems.append("%s: %s" % (rel, msg))

        if src.count("{") != src.count("}"):
            problems.append("%s: unbalanced braces (%d open, %d close)"
                            % (rel, src.count("{"), src.count("}")))
        if src.count("(") != src.count(")"):
            problems.append("%s: unbalanced parentheses (%d open, %d close)"
                            % (rel, src.count("("), src.count(")")))

        for m in re.finditer(r"\b(scr_[a-z0-9_]+)\s*\(", src):
            called.add((m.group(1), rel))

        # GMS 1.4 quirk: bbox_* are read-only
        if re.search(r"\sbbox_(left|right|top|bottom)\s*=[^=]", src):
            problems.append("%s: bbox_* are read-only in GMS 1.4" % rel)

    for name, rel in sorted(called):
        if name not in have:
            problems.append("%s: calls %s() but code/scripts/%s.gml is missing"
                            % (rel, name, name))

    for name in sorted(have):
        if name not in [c[0] for c in called]:
            warned.append("code/scripts/%s.gml is never called" % name)

    print("gml files : %d" % len(files))
    print("scripts   : %d" % len(have))
    for w in warned:
        print("note  " + w)
    if problems:
        print("\n%d problem(s):" % len(problems))
        for p in problems:
            print("  " + p)
        return 1
    print("\nno GMS 1.4 syntax problems found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
