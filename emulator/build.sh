#!/usr/bin/env bash
#
# Build the headless NES oracle used for frame-accurate recreation work.
#
#   ./emulator/build.sh            # build everything into emulator/out
#   ./emulator/build.sh --clean    # wipe the build tree first
#
# Produces:
#   emulator/out/nesrun                          the headless libretro host
#   emulator/out/cores/nestopia_libretro.so      Nestopia core (pixel oracle)
#   emulator/out/cores/fceumm_libretro.so        FCEUmm core   (cross-check)
#   emulator/out/palette.md                      palette probe results
#
# Nothing here is vendored into the repo: cores are cloned at pinned commits
# and built from source, so a rebuild years from now still gives the same
# emulator.  Requires git, gcc/g++, make and curl.  No root needed.
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(dirname "$ROOT")"
OUT="$ROOT/out"
SRC="${NES_ORACLE_SRC:-$ROOT/.build}"     # override to reuse an existing tree
JOBS="${JOBS:-$(nproc 2>/dev/null || echo 2)}"

# Pinned upstream commits - bump deliberately, never implicitly.
NSTOPIA_URL="https://github.com/libretro/nestopia.git"
NSTOPIA_REV="f1e02d12664834536edbf7352995a3d0cd1caef4"
FCEUMM_URL="https://github.com/libretro/libretro-fceumm.git"
FCEUMM_REV="77468e568d9fe9c48d684ca911f1a3fe7259fdf7"

if [ "${1:-}" = "--clean" ]; then
   echo "== cleaning"
   rm -rf "$SRC" "$OUT"
fi

mkdir -p "$OUT/cores" "$SRC"

need() { command -v "$1" >/dev/null 2>&1 || { echo "missing build tool: $1" >&2; exit 1; }; }
need git; need gcc; need g++; need make; need curl

# ---------------------------------------------------------------- host ----
echo "== building nesrun"
gcc -O2 -std=gnu99 -Wall -Wextra -Wno-unused-parameter \
    -o "$OUT/nesrun" "$ROOT/libretro_host.c" -ldl
echo "   -> $OUT/nesrun"

# ------------------------------------------------------------ helpers ----
# fetch NAME URL REV : clone at an exact commit (shallow where possible)
fetch() {
   local name="$1" url="$2" rev="$3" dir="$SRC/$1"
   if [ -d "$dir/.git" ] && [ "$(git -C "$dir" rev-parse HEAD 2>/dev/null || true)" = "$rev" ]; then
      echo "   $name already at $rev"
      return
   fi
   rm -rf "$dir"
   echo "   cloning $name"
   git init -q "$dir"
   git -C "$dir" remote add origin "$url"
   if ! git -C "$dir" fetch -q --depth 1 origin "$rev" 2>/dev/null; then
      git -C "$dir" fetch -q origin 2>/dev/null || true
   fi
   git -C "$dir" checkout -q "$rev" 2>/dev/null || git -C "$dir" checkout -q FETCH_HEAD
}

# -------------------------------------------------------------- cores ----
echo "== cores"
fetch nestopia "$NSTOPIA_URL" "$NSTOPIA_REV"
fetch fceumm   "$FCEUMM_URL"   "$FCEUMM_REV"

echo "== building nestopia (pixel oracle)"
if [ ! -f "$OUT/cores/nestopia_libretro.so" ]; then
   make -C "$SRC/nestopia/libretro" -j"$JOBS" >"$OUT/cores/nestopia.build.log" 2>&1 \
      || { echo "nestopia build failed - see $OUT/cores/nestopia.build.log" >&2; exit 1; }
   cp "$SRC/nestopia/libretro/nestopia_libretro.so" "$OUT/cores/"
fi
echo "   -> $OUT/cores/nestopia_libretro.so"

echo "== building fceumm (cross-check)"
if [ ! -f "$OUT/cores/fceumm_libretro.so" ]; then
   make -C "$SRC/fceumm" -j"$JOBS" >"$OUT/cores/fceumm.build.log" 2>&1 \
      || { echo "fceumm build failed - see $OUT/cores/fceumm.build.log" >&2; exit 1; }
   cp "$SRC/fceumm/fceumm_libretro.so" "$OUT/cores/"
fi
echo "   -> $OUT/cores/fceumm_libretro.so"

# --------------------------------------------------------- smoke test ----
ROM="$REPO/Gradius (USA).nes"
if [ -f "$ROM" ]; then
   echo "== smoke test"
   "$OUT/nesrun" --core "$OUT/cores/nestopia_libretro.so" --rom "$ROM" \
      --frames 120 --hash /tmp/nesrun_smoke.txt --quiet
   echo "   120 frames ok: $(tail -1 /tmp/nesrun_smoke.txt)"
fi

cat <<EOF

Done.
  host    : $OUT/nesrun
  nestopia: $OUT/cores/nestopia_libretro.so   ($NSTOPIA_REV)
  fceumm  : $OUT/cores/fceumm_libretro.so     ($FCEUMM_REV)

Next: ./emulator/oracle.sh selftest
EOF
