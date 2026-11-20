# Gradius sound driver — what the ROM actually does

Written from the traced disassembly (`tools/nesdis.py`, `docs/disassembly/`)
and from a live APU write log (`NES_APULOG`, see `emulator/README.md`).  The
per-frame numbers quoted here come from the 1200-frame attract capture that
`docs/audio.md` is generated from.

## Where the code lives

| | |
|---|---|
| driver location | fixed bank 1, `$EC00-$EFFF` (never banked out) |
| init / song load | `$EC1E` |
| per-frame tick | `$ED02`, called from the NMI handler after `INC $0004` |
| music data | `$FE20` and up, in the same fixed bank |

The tick runs **once per frame**, at a fixed point in the NMI, which is why
the observable register stream is frame-locked: same frame, same cycle, every
loop of the attract sequence.

## Register access is fully indexed

Every APU write goes through a channel index in `X`:

| instruction | sites |
|---|---|
| `STA $4000,X` | `$ECC3 $EDD1 $EE1F $EE7E $EF2C $EF41` |
| `STA $4001,X` | `$EDF9` |
| `STA $4002,X` | `$ED65 $EFA2` |
| `STA $4003,X` | `$ED68 $EF9B` |

There is **no** `STA $4011` and no `STA $4012/$4013` anywhere in the ROM, so
**DPCM is unused** — sample playback is not part of the port.  `$4015` is
written once, at startup (`$81AD`, value `$1F`: all four channels on).

A 1200-frame capture of the attract sequence contains 1650 writes and not one
to `$4011-$4013` or `$4017`: the frame counter is left at its power-on default
(4-step, IRQ inhibited), so the port never has to model APU frame IRQs.

## Per-channel usage

| channel | registers written | how it is driven |
|---|---|---|
| pulse 1 | `$4000` 565, `$4002` 114, `$4003` 33, `$4001` 10 | volume rewritten **every frame** |
| pulse 2 | `$4004` 408, `$4006` 92, `$4007` 12, `$4005` 12 | volume rewritten **every frame** |
| triangle | `$4008` 160, `$400A` 116, `$400B` 116 | linear counter used as a gate |
| noise | `$400C` 9, `$400E` 1, `$400F` 1 | effects only |

Three consequences the port has to reproduce:

1. **Hardware envelopes are never used.**  `$4000`/`$4004` have the
   constant-volume bit set on 565/565 and 408/408 writes.  The driver ramps
   the volume itself, one write per frame, so a note is a *7–16 frame
   staircase*, not an exponential decay.  Envelope shapes observed:
   `15->9` (7 frames), `10->3` (8), `10->8` (3), `7->0` (8), `15->0` (16).
2. **Sweep is fixed at `$30`** on both pulses (10 and 12 writes) — the enable
   bit is never set, so no hardware pitch sweep.  Any vibrato or slide is
   software, by writing `$4002`/`$4006`.
3. **Only 12–33 writes to `$4003`/`$4007`** across 1200 frames, always `$08`
   (length index 1, period high 0).  Notes are therefore all in the low period
   octave and the *length counter plays no part in note length*; the driver
   silences a channel by writing volume 0 or a period of 0.

## Note timing

The tick is 1 frame; the music's step is a multiple of it.  In the attract
sequence the melody's onset gaps are 2/4/7/8/16/35/83/239 frames, median 8
(**7.5 steps/s**), the bass's median 4, the triangle's median 8.  The 2 and 4
frame gaps are not tempo changes: they are runs of fast arpeggio steps, which
is why the score in `docs/audio.md` has consecutive-frame onsets in places.

Tuning is within about ±20 cents of equal temperament for the pulses and
±43 cents for the triangle, i.e. the ROM ships **its own period table** and
the port must copy those numbers rather than convert note names back to
periods.

## Sound effects

Frame 1033 of the attract capture starts a 32-frame burst with up to 15 writes
per frame where the triangle period climbs by ~128 per frame (A4 → A3 → D3 →
A2 → F2 → D2 → B1) while the noise channel fires and the pulses go to period 0.
That is the shape of every effect in the game: **pitch sweeps done by software,
on the triangle for the "big" effects and the noise channel for hits**, versus
music which touches each register once per frame.

`docs/audio.md` lists all such windows automatically.
