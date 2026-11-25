#!/usr/bin/env python3
"""Cut reproducible Stage 1 audio excerpts at exact emulated-frame boundaries.

The pinned headless fceumm harness writes AFI1 cumulative stereo sample counts,
so a varying 798/799 samples-per-NTSC-frame schedule cannot shift the cuts.
Music-only is from a *stationary, safe* player run. Boss/clear clips are honest
mixed gameplay references, not isolated SFX or proven seamless music loops.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import wave

from export_stage_01_rom import CAPTURE, DEFAULT_OUT

CLIPS = (
    ("bgm_restaurant_stationary_excerpt", "music_idle", "idle.wav", 11800, 13200,
     "Stationary Seating music reference; no player movement/attack SFX observed. "
     "Not loop-point verified or proven free of off-screen SFX.", "music_excerpt"),
    ("boss_water_rabbit_gameplay_mix", "water_rabbit", "playthrough.wav", 20900, 22000,
     "Water Rabbit combat music WITH in-game water/box sounds; not isolated music.",
     "mixed_reference"),
    ("stage_clear_gameplay_mix", "water_rabbit", "playthrough.wav", 29730, 30099,
     "Cheat-assisted boss defeat/clear cue WITH gameplay and score sounds.",
     "mixed_reference"),
)


def read_index(path: Path) -> tuple[int, int, list[int]]:
    data = path.read_bytes()
    if len(data) < 20 or data[:4] != b"AFI1" or (len(data) - 12) % 8:
        raise ValueError(f"invalid AFI1 index: {path}")
    first, rate = struct.unpack_from("<II", data, 4)
    samples = [0] + [v[0] for v in struct.iter_unpack("<Q", data[12:])]
    if not all(a <= b for a, b in zip(samples, samples[1:])):
        raise ValueError("audio index sample counts must increase monotonically")
    return first, rate, samples


def export(raw: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    items = []
    for basename, part, wav_name, frame_start, frame_end, description, kind in CLIPS:
        source = raw / part
        first, rate, boundaries = read_index(source / "audio_frame_index.dat")
        if not first <= frame_start <= frame_end < first + len(boundaries) - 1:
            raise ValueError(f"{basename} frames outside AFI1 coverage")
        start = boundaries[frame_start - first]
        end = boundaries[frame_end - first + 1]
        with wave.open(str(source / wav_name), "rb") as wav:
            if (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) != (rate, 2, 2):
                raise ValueError("unexpected WAV format; expected 48kHz 16-bit stereo")
            if wav.getnframes() != boundaries[-1]:
                raise ValueError("AFI1 final sample count does not match source WAV")
            wav.setpos(start)
            payload = wav.readframes(end - start)
        fn = basename + ".wav"
        with wave.open(str(out / fn), "wb") as dest:
            dest.setnchannels(2)
            dest.setsampwidth(2)
            dest.setframerate(rate)
            dest.writeframes(payload)
        items.append({"file": fn, "type": kind, "description": description,
                      "source_capture": part, "frames_inclusive": [frame_start, frame_end],
                      "samples_in_source": [start, end], "rate_hz": rate,
                      "duration_seconds": round((end - start) / rate, 5),
                      "loop_verified": False,
                      "sha256": hashlib.sha256((out / fn).read_bytes()).hexdigest()})
        print(fn, f"{(end - start) / rate:.2f} sec", kind)
    manifest = {"source": "USA ROM / pinned fceumm AFI1 + WAV captures",
                "caution": "Only the stationary Seating excerpt approaches an isolated BGM. "
                           "Boss and clear clips are mixed sound references, not clean SFX or loops.",
                "clips": items}
    (out / "stage_01_audio.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", type=Path, default=CAPTURE)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT / "audio")
    args = ap.parse_args()
    export(args.raw, args.out)


if __name__ == "__main__":
    main()
