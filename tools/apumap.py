#!/usr/bin/env python3
"""
apumap.py - turn a captured APU register stream into a readable score.

The Nestopia core in emulator/out is built with an APU write logger
(emulator/patches/nestopia-apulog.py).  Set NES_APULOG=<file> and every write
to $4000-$4017 is appended as

    <frame> <cpu-cycle-in-frame> <addr> <data>

This tool reads that log and reports what the sound driver actually did, per
channel: note onsets (with period, Hz and nearest note name), the software
volume envelopes, length-counter and linear-counter values, tempos.  The point
is a specification the GameMaker port can be checked against - the register
stream is the ground truth, not the ROM's music data.

Usage:
    NES_APULOG=apu.log ./emulator/out/nesrun --core emulator/out/cores/nestopia_libretro.so \
        --rom "Gradius (USA).nes" --frames 1200 --input oracle/inputs/boot_to_game.txt --quiet
    ./tools/apumap.py apu.log --out docs/audio.md
    ./tools/apumap.py apu.log --events          # compact machine-readable stream
"""
import argparse
import collections
import sys

CLOCK = 1789772.7          # NTSC CPU clock, Hz
CHANNELS = {
    "pulse1":   (0x4000, 0x4001, 0x4002, 0x4003),
    "pulse2":   (0x4004, 0x4005, 0x4006, 0x4007),
    "triangle": (None,   0x4008, 0x400A, 0x400B),
    "noise":    (None,   0x400C, 0x400E, 0x400F),
}
REG_NAME = {}
for _ch, _regs in CHANNELS.items():
    for _r in _regs:
        if _r is not None:
            REG_NAME[_r] = _ch
REG_NAME[0x4011] = "dmc"
REG_NAME[0x4012] = "dmc"
REG_NAME[0x4013] = "dmc"
REG_NAME[0x4015] = "status"
REG_NAME[0x4017] = "framecounter"

NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def note_name(freq):
    """Nearest equal-tempered note plus the deviation in cents."""
    if freq <= 0:
        return "-", 0
    import math
    midi = 69 + 12 * math.log2(freq / 440.0)
    near = round(midi)
    cents = int(round((midi - near) * 100))
    return "%s%d" % (NOTES[near % 12], near // 12 - 1), cents


def pulse_hz(period):
    return CLOCK / (16.0 * (period + 1))


def triangle_hz(period):
    return CLOCK / (32.0 * (period + 1))


def load(path):
    """[(frame, cycle, addr, data)] in the order the CPU wrote them."""
    out = []
    with open(path) as f:
        for n, line in enumerate(f, 1):
            p = line.split()
            if len(p) != 4:
                continue
            try:
                out.append((int(p[0]), int(p[1]), int(p[2], 16), int(p[3], 16)))
            except ValueError:
                raise SystemExit("apumap: bad line %d: %r" % (n, line.rstrip()))
    return out


class Channel:
    """State carried between writes, so a note onset is visible."""

    def __init__(self, name, regs):
        self.name = name
        self.vol_reg, self.sweep_reg, self.lo_reg, self.hi_reg = regs
        self.lo = 0
        self.hi = 0
        self.period = None            # last period the CPU asked for
        self.pending = {}             # frame -> (cycle, period), coalesced
        self.notes = []               # (frame, cycle, period, hz, name, cents, vol)
        self.volumes = []             # (frame, value) for every volume write
        self.lengths = []             # (frame, value) $4003/$4007/$400B/$400F
        self.sweeps = []
        self.restarts = 0
        self.rests = 0                # period 0 = channel silenced

    def write(self, frame, cycle, addr, data):
        if addr == self.vol_reg:
            self.volumes.append((frame, data))
        elif addr == self.sweep_reg:
            self.sweeps.append((frame, data))
        elif addr == self.lo_reg:
            self.lo = data
            self._retune(frame, cycle)
        elif addr == self.hi_reg:
            self.hi = data
            self.lengths.append((frame, data))
            self._retune(frame, cycle)

    def _retune(self, frame, cycle):
        """Record the period the channel is left at when this frame ends.

        The driver usually writes the high byte (which triggers a phase reset)
        and then the low byte a few cycles later, so the intermediate pair is
        not a note.  Coalescing per frame keeps the real onsets - the music
        does run arpeggios faster than one frame per step, and those show up
        as onsets on consecutive frames.
        """
        period = ((self.hi & 0x07) << 8) | self.lo
        self.pending[frame] = (cycle, period)

    def settle(self):
        """Turn the coalesced per-frame periods into note onsets."""
        for frame in sorted(self.pending):
            cycle, period = self.pending[frame]
            if period == self.period:
                continue
            self.period = period
            if period == 0:
                # period 0 is the driver's "silence this channel" command, not
                # a note (a real NES pulse channel at period 0 is inaudible).
                self.rests += 1
                continue
            if self.name.startswith("pulse"):
                hz = pulse_hz(period)
            elif self.name == "triangle":
                hz = triangle_hz(period)
            else:
                hz = 0.0
            nm, cents = note_name(hz) if hz else ("-", 0)
            self.notes.append((frame, cycle, period, hz, nm, cents))
            self.restarts += 1
        self.pending = {}


def envelopes(volumes, width=4):
    """Collapse per-frame volume writes into the distinct ramp shapes used.

    The driver writes the volume nibble every frame, so a 'run' is a series of
    consecutive frames whose volume falls by one.  Reporting the runs tells us
    the envelope table to reproduce.
    """
    runs = []
    cur = None
    prev = None
    for frame, v in volumes:
        vol = v & 0x0F
        if cur and frame == cur["frame_end"] + 1 and vol == cur["end"] - 1:
            cur["frame_end"] = frame
            cur["end"] = vol
        elif cur and frame == cur["frame_end"] and vol == cur["end"] - 1:
            cur["end"] = vol            # two writes in one frame (retrigger)
        else:
            if cur:
                runs.append(cur)
            cur = {"frame_start": frame, "frame_end": frame, "start": vol, "end": vol}
        if v & 0xC0:
            cur.setdefault("duty", v >> 6)
        prev = v
    if cur:
        runs.append(cur)
    return runs


def summarise(events, out, total_frames):
    w = out.write
    writes = collections.Counter(a for _, _, a, _ in events)
    per_channel = collections.Counter(REG_NAME.get(a, "?") for _, _, a, _ in events)
    frames = sorted({f for f, _, _, _ in events})
    first, last = (frames[0], frames[-1]) if frames else (0, 0)
    per_frame = collections.Counter(f for f, _, _, _ in events)

    w("# APU register stream\n\n")
    w("Derived from a `NES_APULOG` capture by `tools/apumap.py`; regenerate with\n"
      "the command in that file's docstring.  This is the sound driver's\n"
      "*observable behaviour*, which is what the recreation has to match.\n\n")
    w("| | |\n|---|---|\n")
    w("| frames in capture | %d |\n" % total_frames)
    w("| frames with APU writes | %d |\n" % len(frames))
    w("| first / last frame with writes | %d / %d |\n" % (first, last))
    w("| total register writes | %d |\n" % len(events))
    w("| busiest frame | %d writes at frame %d |\n"
      % (per_frame.most_common(1)[0][1] if per_frame else 0,
         per_frame.most_common(1)[0][0] if per_frame else -1))
    w("\nWrites per register:\n\n| register | writes | channel |\n|---|---|---|\n")
    for addr, n in sorted(writes.items()):
        w("| `$%04X` | %d | %s |\n" % (addr, n, REG_NAME.get(addr, "?")))
    w("\nWrites per channel: ")
    w(", ".join("%s %d" % (k, v) for k, v in sorted(per_channel.items())))
    w("\n")

    # --- channel detail -----------------------------------------------------
    chans = {}
    for name, regs in CHANNELS.items():
        c = Channel(name, regs)
        chans[name] = c
        for frame, cycle, addr, data in events:
            if addr in regs:
                c.write(frame, cycle, addr, data)
        c.settle()

    w("\n## Per-channel behaviour\n")
    for name in ("pulse1", "pulse2", "triangle", "noise"):
        c = chans[name]
        w("\n### %s\n\n" % name)
        if not c.notes and not c.volumes:
            w("unused\n")
            continue
        w("- note onsets: **%d**, first at frame %d\n"
          % (len(c.notes), c.notes[0][0] if c.notes else -1))
        if c.notes and name != "noise":
            gaps = collections.Counter(
                b[0] - a[0] for a, b in zip(c.notes, c.notes[1:]))
            common = ", ".join("%d frames x%d" % (g, n)
                               for g, n in gaps.most_common(5))
            w("- onset spacing: %s\n" % (common or "single note"))
            lo = min(c.notes, key=lambda n: n[3])
            hi = max(c.notes, key=lambda n: n[3])
            tone = [n for n in c.notes]
            w("- range: %s (%.0f Hz) .. %s (%.0f Hz)\n"
              % (lo[4], lo[3], hi[4], hi[3]))
            cents = [n[5] for n in tone]
            w("- tuning vs equal temperament: %+d .. %+d cents (mean %+.1f)\n"
              % (min(cents), max(cents), sum(cents) / len(cents)))
            if c.rests:
                w("- rest commands (period 0): %d\n" % c.rests)
        if c.lengths:
            vals = collections.Counter(v & 0xF8 for _, v in c.lengths)
            w("- `$%04X` (length count + period high): %s\n"
              % (c.hi_reg, ", ".join("`%02X`x%d" % (k, n)
                                     for k, n in vals.most_common(6))))
        if c.sweeps:
            vals = collections.Counter(v for _, v in c.sweeps)
            role = {"pulse1": "sweep", "pulse2": "sweep",
                    "triangle": "linear counter", "noise": "volume"}[name]
            enabled = any(v & 0x80 for v in vals)
            w("- `$%04X` (%s): %s%s\n"
              % (c.sweep_reg, role,
                 ", ".join("`%02X`x%d" % (k, n) for k, n in vals.most_common(4)),
                 "" if name != "noise" or enabled
                 else " - noise volume is set per effect"))
        if c.volumes:
            envs = envelopes(c.volumes)
            shapes = collections.Counter(
                (e["start"], e["end"], e["frame_end"] - e["frame_start"] + 1)
                for e in envs if e["start"] != e["end"])
            w("- volume writes: %d, one per frame while a note sounds\n"
              % len(c.volumes))
            if shapes:
                w("- envelope ramps (volume start->end over n frames): %s\n"
                  % ", ".join("%d->%d over %d x%d" % (a, b, d, n)
                              for (a, b, d), n in shapes.most_common(6)))
            else:
                w("- volume never ramps (single value per note)\n")
            duties = collections.Counter(v >> 6 for _, v in c.volumes)
            w("- duty cycles: %s"
              % ", ".join("%d x%d" % (k, n) for k, n in sorted(duties.items())))
            w("   (0=12.5%%, 1=25%%, 2=50%%, 3=75%%)\n")
            const = sum(1 for _, v in c.volumes if v & 0x10)
            w("- constant-volume bit set on %d/%d writes%s\n"
              % (const, len(c.volumes),
                 " - hardware envelopes unused, volume is software-driven"
                 if const == len(c.volumes) else ""))

    # --- tempo -------------------------------------------------------------
    w("\n## Tempo\n\n")
    for name in ("pulse1", "pulse2", "triangle"):
        c = chans[name]
        if len(c.notes) < 4:
            continue
        gaps = sorted(b[0] - a[0] for a, b in zip(c.notes, c.notes[1:])
                      if b[0] - a[0] > 0)
        if not gaps:
            continue
        med = gaps[len(gaps) // 2]
        w("- %s: onset gaps %s frames, median %d (%.1f steps/s at 60.0988 fps)\n"
          % (name,
             "/".join(str(g) for g in sorted(set(gaps))[:8]),
             med, 60.0988 / med))

    # --- sound effects -----------------------------------------------------
    # Music writes 3-5 registers per frame at a fixed point in the frame.  An
    # effect dumps registers all over the frame and sweeps pitch every frame,
    # so density plus pitch motion separates the two without guessing.
    # A note onset on three channels also spikes to 7-9 writes for a single
    # frame; only a sustained burst is an effect.
    dense = [f for f, n in per_frame.items() if n >= 6]
    windows = []
    for f in sorted(dense):
        if windows and f - windows[-1][1] <= 4:
            windows[-1][1] = f
        else:
            windows.append([f, f])
    windows = [[a, b] for a, b in windows if b - a >= 3]
    w("\n## Sound-effect windows\n\n")
    if windows:
        w("Runs of 4+ frames where the driver writes 6+ registers *and* moves\n"
          "the pitch every frame.  Music writes its registers once per frame at\n"
          "a fixed point; an effect sweeps the period on consecutive frames.\n"
          "Isolated single-frame spikes are just chord/note onsets and are not\n"
          "listed.\n\n")
        w("| frames | length | peak writes/frame |\n|---|---|---|\n")
        for a, b in windows:
            w("| %d-%d | %d frames | %d |\n"
              % (a, b, b - a + 1, max(per_frame[x] for x in range(a, b + 1))))
    else:
        w("none - the capture contains only music and silence\n")

    # --- event table -------------------------------------------------------
    w("\n## Note events\n\n")
    w("| channel | frame | cycle | period | Hz | note | cents |\n|---|---|---|---|---|---|---|\n")
    rows = []
    for name in ("pulse1", "pulse2", "triangle"):
        for frame, cycle, period, hz, nm, cents in chans[name].notes:
            rows.append((frame, name, cycle, period, hz, nm, cents))
    rows.sort()
    for frame, name, cycle, period, hz, nm, cents in rows:
        w("| %s | %d | %d | `$%03X` | %.1f | %s | %+d |\n"
          % (name, frame, cycle, period, hz, nm, cents))
    return rows


def events_dump(events):
    """Compact, diffable stream: frame cycle addr data, one line per write."""
    for frame, cycle, addr, data in events:
        sys.stdout.write("%d %d %04X %02X\n" % (frame, cycle, addr, data))


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log")
    ap.add_argument("--out", help="write markdown report here")
    ap.add_argument("--events", action="store_true",
                    help="print the raw stream to stdout instead of a report")
    ap.add_argument("--csv", help="write note events as CSV")
    args = ap.parse_args(argv[1:])

    events = load(args.log)
    if not events:
        raise SystemExit("apumap: no writes in %s" % args.log)
    if args.events:
        events_dump(events)
        return 0

    total = max(f for f, _, _, _ in events) + 1
    if args.out:
        with open(args.out, "w") as f:
            rows = summarise(events, f, total)
    else:
        rows = summarise(events, sys.stdout, total)

    if args.csv:
        with open(args.csv, "w") as f:
            f.write("frame,channel,cycle,period,hz,note,cents\n")
            for frame, name, cycle, period, hz, nm, cents in rows:
                f.write("%d,%s,%d,%d,%.2f,%s,%d\n"
                        % (frame, name, cycle, period, hz, nm, cents))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
