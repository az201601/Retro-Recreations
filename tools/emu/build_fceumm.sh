#!/usr/bin/env bash
set -euo pipefail
# Build libretro-fceumm core and headless frontend.
# Requires: git, gcc, make. Network access to github.com for clone.
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/tools/out/emu"
SRC="$ROOT/tools/emu/libretro-fceumm"
PATCH="$ROOT/tools/emu/patches/fceumm_capture_layers.patch"
# Pin the libretro core: savestate layout, palette and input timings must not
# silently change between capture sessions. This checkout is separate from the
# project's working branch and is gitignored.
CORE_COMMIT=fb919fb6fa881aaa6279b765d480220579e5c606
mkdir -p "$OUT"
if [ ! -d "$SRC/.git" ]; then
  git clone --depth 1 https://github.com/libretro/libretro-fceumm.git "$SRC"
fi
if [ "$(git -C "$SRC" rev-parse HEAD)" != "$CORE_COMMIT" ]; then
  git -C "$SRC" fetch --depth 1 origin "$CORE_COMMIT"
  git -C "$SRC" checkout --detach "$CORE_COMMIT"
fi
if ! git -C "$SRC" apply --reverse --check "$PATCH" 2>/dev/null; then
  git -C "$SRC" apply "$PATCH"
fi
make -C "$SRC" -j4
cp "$SRC/fceumm_libretro.so" "$OUT/fceumm_libretro.so"
gcc -O2 -Wall -Wextra \
  -I"$SRC/src/drivers/libretro/libretro-common/include" \
  -o "$OUT/fceumm_headless" "$ROOT/tools/emu/fceumm_headless.c" -ldl
echo "Built: $OUT/fceumm_libretro.so $OUT/fceumm_headless"
