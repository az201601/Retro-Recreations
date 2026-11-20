# Reference captures

Captures here are produced by `../emulator/oracle.sh` and are *derived*: the
inputs (this directory), the pinned ROM (`../Gradius (USA).nes`, sha1
`17d740e1e79350e1f0a6565908767e8585606a98`) and the pinned emulator core
(`../emulator/build.sh`) fully determine the output. So `out/` is git-ignored
and regenerated on demand.

```
inputs/          controller scripts, one per scenario (committed)
palette/         the pinned 64-entry NES palette (committed - it is the target)
out/<name>/      f%06d.png, audio.wav, hash.txt, ram.txt, meta.txt, vars.txt
```

## Reproduce everything

```
./emulator/build.sh
./emulator/oracle.sh rec attract --frames 1200 --input oracle/inputs/boot_to_game.txt \
    --png-from 300 --png-every 30 --watch CPU:0:64 --wav
./emulator/oracle.sh check attract --frames 1200 --input oracle/inputs/boot_to_game.txt \
    --png-from 300 --png-every 30 --watch CPU:0:64
```

`check` re-runs the capture and reports the first frame whose hash differs -
that is the frame budget for "did my change break anything".

## Input scripts

One rule per line: `FRAME[-TO]  BUTTONS`, buttons `U D L R A B S T`
(select/start), `-` for nothing. Later rules OR together, so

```
0-179   -
180-183 T
184-400 -
```

is "wait 3 seconds, tap Start, then idle". Frame 0 is power-on, and the clock
is the NES's 60.0988 Hz, not the host's 60.000.
