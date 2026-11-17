#!/usr/bin/env bash
# Recreate every emulator trace that tools/build_assets.py reads.
# Total run time is about 2 minutes; output lands in out/ (git ignored).
set -e
cd "$(dirname "$0")/.."
ROM="Chip 'n Dale - Rescue Rangers 2 (USA).nes"
CAP=./tools/nes/capture
# boot -> 1P select -> cut scene; frame 5600 onwards is the first stage
PRE="200:8,260:8,400:32,420:32,440:8,520:1,700:8"

run() {           # run <name> <frames> <script> <traceFrom> [ppmEvery]
  mkdir -p "out/$1/frames"
  $CAP "$ROM" "$2" "out/$1" "$3" "$4" "$(($2 - 1))" "${5:-0}" >/dev/null 2>&1
  echo "  out/$1"
}

echo "captures:"

# --- boot / title / cut scenes / menu art ---------------------------------
run boot    1700  "200:8" 0
run menu    1400  "200:8,260:8,400:32,420:32,440:8,600:1,700:128,760:8,820:8" 400
run intro   6000  "$PRE" 300

# --- the first stage: run, jump, throw ------------------------------------
S="$PRE,5400-10999:128"
for f in $(seq 5600 120 10900); do S="$S,$f:129"; done          # A = jump
for f in $(seq 5660 90 10900);  do S="$S,$f:130"; done          # B = grab / throw
run game   11000  "$S" 5400

# --- hero reference runs --------------------------------------------------
# hold RIGHT only: the walk cycle (5600..5633) and the idle loop
run pi_holdR 9000 "$PRE,5600-8999:128" 5500

# jump: RIGHT + A held, so the whole arc is visible (crouch 5734, tuck 5744)
run mv_g     7200 "$PRE,5700-7199:129" 5700

# hop in place while running: gives the landing squash (5718)
S="$PRE,5700-7199:128"
for f in $(seq 5710 24 7190); do S="$S,$f:129"; done
run mv_a     7200 "$S" 5700

# crate throw: RIGHT + B taps (5700 = wind-up, 5609 = release)
S="$PRE,5600-7599:128"
for f in $(seq 5660 24 7590); do S="$S,$f:130"; done
run pb       7600 "$S" 5500

# --- level art ------------------------------------------------------------
run level    9000 "$PRE,5600-8999:128" 5400 6

echo "done. now run: python tools/find_poses.py <trace>  and  .venv/bin/python tools/build_assets.py"
