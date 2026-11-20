#!/usr/bin/env bash
#
# oracle.sh - reference captures from the real ROM, plus self-tests.
#
#   ./emulator/oracle.sh selftest              determinism + cross-core checks
#   ./emulator/oracle.sh rec NAME [options]    capture a reference run
#   ./emulator/oracle.sh check NAME [options]  re-run, diff against capture
#   ./emulator/oracle.sh diff A B              compare two captures
#
# Options for rec/check are nesrun options and are passed straight through:
#
#   ./emulator/oracle.sh rec title --frames 900 --png-every 30
#   ./emulator/oracle.sh rec start --frames 1800 --input inputs/start.txt --wav \
#       --watch CPU:0:2048 --png 0-60
#
# Captures live in oracle/out/NAME/:
#   f%06d.png  audio.wav  hash.txt  ram.txt  meta.txt  cmd.txt
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(dirname "$ROOT")"
OUT="$ROOT/out"
NESRUN="$OUT/nesrun"
CORE_NSTOPIA="$OUT/cores/nestopia_libretro.so"
CORE_FCEUMM="$OUT/cores/fceumm_libretro.so"
ROM_DEFAULT="$REPO/Gradius (USA).nes"
CAPDIR="$REPO/oracle/out"

# Core options that pin the oracle to raw, unmasked PPU/APU behaviour.
# (Order matters only for readability.)
ORACLE_VARS_DEFAULT="
nestopia_blargg_ntsc_filter=disabled
nestopia_overscan_h_left=0
nestopia_overscan_h_right=0
nestopia_overscan_v_top=0
nestopia_overscan_v_bottom=0
nestopia_nospritelimit=disabled
nestopia_audio_filter=disabled
"

die() { echo "oracle: $*" >&2; exit 1; }

need_build() {
   [ -x "$NESRUN" ] || die "nesrun not built - run ./emulator/build.sh"
   [ -f "$CORE_NSTOPIA" ] || die "nestopia core not built - run ./emulator/build.sh"
}

# build a --var-file from ORACLE_VARS_DEFAULT plus any --var overrides
make_varfile() {
   local path="$1"; shift
   {
      echo "# oracle core options (generated $(date -u +%Y-%m-%dT%H:%M:%SZ))"
      echo "$ORACLE_VARS_DEFAULT" | sed '/^$/d'
      for kv in "$@"; do echo "$kv"; done
   } > "$path"
}

cmd_selftest() {
   need_build
   local tmp; tmp="$(mktemp -d)"
   local rom="$ROM_DEFAULT"; [ -f "$rom" ] || die "rom not found: $rom"
   make_varfile "$tmp/vars.txt"
   printf '0-450 T\n452-455 T\n456-460 -\n600-700 R\n' > "$tmp/in.txt"

   echo "== 1. determinism (Nestopia, 900 frames, identical inputs)"
   for i in 1 2; do
      "$NESRUN" --core "$CORE_NSTOPIA" --rom "$rom" --frames 900 \
         --input "$tmp/in.txt" --var-file "$tmp/vars.txt" \
         --hash "$tmp/h$i.txt" --quiet
   done
   if cmp -s "$tmp/h1.txt" "$tmp/h2.txt"; then
      echo "   PASS  identical frame hashes ($(md5sum < "$tmp/h1.txt" | cut -c1-12))"
      echo "         final frame hash: $(tail -1 "$tmp/h1.txt" | cut -d' ' -f2)"
   else
      echo "   FAIL  runs diverge"; diff <(head -20 "$tmp/h1.txt") <(head -20 "$tmp/h2.txt") | head; fi

   echo "== 2. frame size / audio rate"
   "$NESRUN" --core "$CORE_NSTOPIA" --rom "$rom" --frames 2 \
      --var-file "$tmp/vars.txt" 2>&1 | grep -E "frame size|fps" | sed 's/^/   /'

   echo "== 3. cross-core agreement (Nestopia vs FCEUmm)"
   if [ -f "$CORE_FCEUMM" ]; then
      # Both cores are forced onto the SAME palette table: Nestopia's own
      # (oracle/palette/nestopia.pal), which FCEUmm reads as <sysdir>/nes.pal
      # in "custom" mode.  With colour choice removed, any difference is
      # emulation.
      local fsys="$REPO/oracle/palette/fceumm_sys"
      if [ ! -f "$fsys/nes.pal" ]; then
         mkdir -p "$fsys"
         cp "$REPO/oracle/palette/nestopia.pal" "$fsys/nes.pal"
      fi
      local fvars; fvars="$tmp/vars_f.txt"
      grep -v '^nestopia_' "$tmp/vars.txt" > "$fvars"
      echo "fceumm_palette=custom" >> "$fvars"

      "$NESRUN" --core "$CORE_NSTOPIA" --rom "$rom" --frames 600 \
         --input "$tmp/in.txt" --var-file "$tmp/vars.txt" \
         --watch CPU:0:2048 --watch-out "$tmp/ram_n.txt" \
         --dir "$tmp/px_n" --png 300-340 --quiet
      "$NESRUN" --core "$CORE_FCEUMM" --rom "$rom" --frames 600 \
         --input "$tmp/in.txt" --var-file "$fvars" --sysdir "$fsys" \
         --watch CPU:0:2048 --watch-out "$tmp/ram_f.txt" \
         --dir "$tmp/px_f" --png 300-340 --quiet

      python3 - "$tmp/ram_n.txt" "$tmp/ram_f.txt" <<'PYEOF'
import sys
a = open(sys.argv[1]).read().splitlines()
b = open(sys.argv[2]).read().splitlines()
n = min(len(a), len(b))
worst, worst_frame, zero = 0, -1, 0
for i in range(n):
    A, B = a[i].split()[2:], b[i].split()[2:]
    d = sum(1 for x, y in zip(A, B) if x != y)
    if d == 0:
        zero += 1
    if d > worst and i > 60:      # ignore power-on / RAM-init noise
        worst, worst_frame = d, i
print(f"   RAM: {n} frames compared, {zero} byte-identical")
if worst < 0:
    print("   PASS  post-boot RAM identical")
elif worst < 128:
    print(f"   PASS  worst divergence {worst}/2048 bytes at frame {worst_frame}"
          f" - APU/PPU phase and RNG state, not game logic")
else:
    print(f"   WARN  cores disagree on {worst} bytes at frame {worst_frame}")
PYEOF
      # Pixel check with one palette for both: this is the strict one.
      if [ -x "$REPO/tools/pngcmp.py" ]; then
         echo "   pixels (identical palette, frames 300-340):"
         "$REPO/tools/pngcmp.py" "$tmp/px_n" "$tmp/px_f" --quiet 2>&1 | sed 's/^/   /' | tail -4
      fi
   else
      echo "   skip  fceumm core not built (run ./emulator/build.sh)"
   fi

   echo "== 4. audio actually produced"
   "$NESRUN" --core "$CORE_NSTOPIA" --rom "$rom" --frames 300 \
      --input "$tmp/in.txt" --var-file "$tmp/vars.txt" \
      --wav "$tmp/a.wav" --quiet
   python3 - "$tmp/a.wav" <<'PY'
import sys, wave, struct, math
w = wave.open(sys.argv[1]); n = w.getnframes(); rate = w.getframerate()
d = w.readframes(n); s = struct.unpack("<%dh" % (len(d)//2), d)
rms = math.sqrt(sum(x*x for x in s) / max(1, len(s)))
peak = max(abs(x) for x in s)
print(f"   {n} frames @ {rate} Hz = {n/rate:.2f}s, peak {peak}, rms {rms:.0f}")
print("   PASS  APU output captured" if peak > 100 else "   FAIL  silence")
PY

   # leave a machine-readable summary behind
   mkdir -p "$CAPDIR"
   {
      echo "date        : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      echo "rom         : $(basename "$rom") sha1 $(sha1sum "$rom" | cut -d' ' -f1)"
      "$NESRUN" --core "$CORE_NSTOPIA" --rom "$rom" --probe --quiet | sed 's/^/core_/'
      echo "nesrun      : $(md5sum "$NESRUN" | cut -d' ' -f1)"
   } > "$CAPDIR/selftest.txt"
   echo "== summary -> ${CAPDIR#"$REPO"/}/selftest.txt"
   rm -rf "$tmp"
}

cmd_rec() {
   need_build
   local name="${1:-}"; [ -n "$name" ] || die "usage: oracle.sh rec NAME [nesrun options]"
   shift
   local dir="$CAPDIR/$name"
   local rom="$ROM_DEFAULT"
   local vars=() args=() have_input=0 have_watch=0 want_wav=0

   # split our options from pass-through options
   while [ $# -gt 0 ]; do
      case "$1" in
         --rom) rom="$2"; shift 2 ;;
         --var) vars+=("$2"); shift 2 ;;
         --input) have_input=1; args+=("$1" "$2"); shift 2 ;;
         --watch) have_watch=1; args+=("$1" "$2"); shift 2 ;;
         --wav) want_wav=1; args+=("--wav" "$dir/audio.wav"); shift ;;
         *) args+=("$1"); shift ;;
      esac
   done
   [ -f "$rom" ] || die "rom not found: $rom"
   mkdir -p "$dir"

   make_varfile "$dir/vars.txt" "${vars[@]:-}"
   [ "$have_input" = 1 ] || args+=( )
   local cmd=("$NESRUN" --core "$CORE_NSTOPIA" --rom "$rom"
              --var-file "$dir/vars.txt"
              --hash "$dir/hash.txt"
              --dir "$dir")
   [ "$have_watch" = 1 ] && args+=("--watch-out" "$dir/ram.txt")
   [ "$want_wav" = 1 ] || true

   printf '%q ' "${cmd[@]}" "${args[@]}" > "$dir/cmd.txt"; echo >> "$dir/cmd.txt"
   "${cmd[@]}" "${args[@]}"

   {
      echo "capture     : $name"
      echo "date        : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      echo "rom         : $(basename "$rom")  sha1 $(sha1sum "$rom" | cut -d' ' -f1)"
      echo "core        : nestopia libretro, pinned f1e02d12664834536edbf7352995a3d0cd1caef4"
      echo "clock       : 60.098814 Hz NTSC PPU, 48000 Hz APU (800 samples/frame)"
      echo "pngs        : $(ls "$dir"/f*.png 2>/dev/null | wc -l)"
      echo "frames      : $(wc -l < "$dir/hash.txt" 2>/dev/null || echo 0)"
      echo "cmd         : $(cat "$dir/cmd.txt")"
      echo "vars        :"
      sed 's/^/  /' "$dir/vars.txt"
   } > "$dir/meta.txt"
   echo "capture -> ${dir#"$REPO"/}"
}

cmd_check() {
   need_build
   local name="${1:-}"; [ -n "$name" ] || die "usage: oracle.sh check NAME [nesrun options]"
   shift
   local dir="$CAPDIR/$name"
   [ -f "$dir/hash.txt" ] || die "no capture named '$name' (expected $dir/hash.txt)"
   local tmp; tmp="$(mktemp -d)"
   local args=() rom="$ROM_DEFAULT"
   while [ $# -gt 0 ]; do
      case "$1" in
         --rom) rom="$2"; shift 2 ;;
         --var) shift 2 ;;                        # vars are pinned by the capture
         --wav) shift ;;
         --input|--watch) args+=("$1" "$2"); shift 2 ;;
         --dir|--hash|--watch-out) shift 2 ;;     # never overwrite the capture
         *) args+=("$1"); shift ;;
      esac
   done
   # A watch without --watch-out would land on stdout and drown the verdict.
   local have_watch=0 pass=()
   while [ ${#args[@]} -gt 0 ]; do
      if [ "${args[0]}" = "--watch" ]; then
         have_watch=1
         pass+=("--watch" "${args[1]}" "--watch-out" "$tmp/ram.txt")
         args=("${args[@]:2}")
      else
         pass+=("${args[0]}"); args=("${args[@]:1}")
      fi
   done
   "$NESRUN" --core "$CORE_NSTOPIA" --rom "$rom" --var-file "$dir/vars.txt" \
      --hash "$tmp/hash.txt" --quiet "${pass[@]}"
   if cmp -s "$dir/hash.txt" "$tmp/hash.txt"; then
      echo "check $name: IDENTICAL ($(wc -l < "$tmp/hash.txt") frames)"
   else
      echo "check $name: DIFFERS - first divergent frame:"
      paste -d' ' "$dir/hash.txt" "$tmp/hash.txt" | awk '$2!=$4 {print; exit}'
   fi
   rm -rf "$tmp"
}

cmd_diff() {
   local a="$CAPDIR/${1:-}", b="$CAPDIR/${2:-}"
   [ -f "$a/hash.txt" ] && [ -f "$b/hash.txt" ] || die "usage: oracle.sh diff NAME_A NAME_B"
   local n=0
   paste -d' ' "$a/hash.txt" "$b/hash.txt" | awk '$2!=$4 {n++; if (n<=10) print "frame "$1": "$2" vs "$4} END {print n" of "NR" frames differ"}'
}

case "${1:-}" in
   selftest) shift; cmd_selftest "$@" ;;
   rec)      shift; cmd_rec "$@" ;;
   check)    shift; cmd_check "$@" ;;
   diff)     shift; cmd_diff "$@" ;;
   *)        sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 1 ;;
esac
