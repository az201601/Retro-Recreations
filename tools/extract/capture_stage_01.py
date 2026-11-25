#!/usr/bin/env python3
"""Reproducible, ROM-driven Restaurant/Water Rabbit capture (fceumm only).

The checkpoint chain and input files are committed; large raw traces are
regenerable and belong in tools/out/ (gitignored). See docs/STAGE_01_RESTAURANT.md.
The gameplay route uses a lives safeguard (00A7:03); the six-hit boss test
additionally uses 0067:01 (infinite health) so the actual boss can run to death
without intervening player-death resets. Neither cheat sets boss health or
skips a room. PNG assets are extracted separately from these captures.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
ROM = ROOT / "Chip 'n Dale - Rescue Rangers 2 (USA).nes"
CORE = ROOT / "tools/out/emu/fceumm_libretro.so"
EMU = ROOT / "tools/out/emu/fceumm_headless"
STATES = ROOT / "tools/emu/checkpoints/stage_01_restaurant"
INPUTS = ROOT / "tools/emu/inputs"
DEFAULT_OUT = ROOT / "tools/out/emu/stage_01_verified"
# Published TAS ROM checksum (the disassembly's reassembled ROM is different).
EXPECTED_ROM_MD5 = "e78eb3226a9e09113be319fee1a84f4d"


def capture(out: Path, name: str, start: int, end: int, inputs: str,
            *, ppu_every: int, shots_every: int, infinite_hp: bool = False,
            verify_state: str | None = None) -> None:
    path = out / name
    path.mkdir(parents=True, exist_ok=True)
    cmd = [str(EMU), "--core", str(CORE), "--rom", str(ROM),
           "--load-state", str(STATES / f"frame_{start}.state"),
           "--start-frame", str(start), "--frames", str(end),
           "--inputs", str(INPUTS / inputs), "--cheat", "00A7:03",
           "--out", str(path), "--ram-dir", str(path), "--ppu-dir", str(path),
           "--ppu-every", str(ppu_every), "--ppu-start", str(start + 1),
           "--shot-every", str(shots_every), "--shot-start", str(start + 1),
           "--ram-trace", str(path / "ram_trace.dat"),
           "--oam-trace", str(path / "oam_trace.dat"),
           "--wav", str(path / "playthrough.wav"),
           "--audio-index", str(path / "audio_frame_index.dat"),
           "--save-state", str(path / f"frame_{end}.state")]
    if infinite_hp:
        cmd.extend(["--cheat", "0067:01"])
    with (path / "capture.log").open("w") as log:
        subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    print(f"{name}: frames {start + 1}..{end}; ", end="", flush=True)
    if verify_state:
        result = (path / f"frame_{end}.state").read_bytes()
        expected = (STATES / verify_state).read_bytes()
        if result != expected:
            raise ValueError(f"{name} differs from verified save state {verify_state}")
        print("verified state byte-for-byte", flush=True)
    else:
        print("saved endpoint", flush=True)


def capture_idle_music(out: Path) -> None:
    """Keep Chip stationary in the Seating room for a clean music reference."""
    path = out / "music_idle"
    path.mkdir(parents=True, exist_ok=True)
    cmd = [str(EMU), "--core", str(CORE), "--rom", str(ROM),
           "--load-state", str(STATES / "frame_11200.state"),
           "--start-frame", "11200", "--frames", "13300",
           "--cheat", "00A7:03", "--cheat", "0067:01",
           "--out", str(path), "--ram-dir", str(path),
           "--shots", "11201,11900,12500,13000,13300",
           "--wav", str(path / "idle.wav"),
           "--audio-index", str(path / "audio_frame_index.dat")]
    with (path / "capture.log").open("w") as log:
        subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    for frame in (11201, 11900, 12500, 13000, 13300):
        ram = (path / f"ram_{frame}.bin").read_bytes()
        if (ram[0x73], ram[0x40], ram[0xC0], ram[0xC2]) != (0, 4, 58, 192):
            raise ValueError(f"idle music capture not stationary at frame {frame}")
    print("music_idle: 11201..13300, seating player stationary; WAV+sample index", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--part", choices=["all", "prelude", "route", "boss", "music"], default="all")
    args = ap.parse_args()
    if not CORE.is_file() or not EMU.is_file():
        raise SystemExit("Build pinned core first: ./tools/emu/build_fceumm.sh")
    if hashlib.md5(ROM.read_bytes()).hexdigest() != EXPECTED_ROM_MD5:
        raise SystemExit("ROM checksum mismatch; refusing to replay incompatible saves")
    args.out.mkdir(parents=True, exist_ok=True)
    if args.part in ("all", "prelude"):
        # Earlier manually played opening. Independent of the verified 11800
        # checkpoint: its gameplay can differ even when on the same screen.
        capture(args.out, "seating_opening", 11200, 11800,
                "stage_01_restaurant_playthrough_wip.txt",
                ppu_every=4, shots_every=32)
    if args.part in ("all", "route"):
        capture(args.out, "route_to_boss", 11800, 20350,
                "stage_01_restaurant_route_to_boss.txt",
                ppu_every=8, shots_every=64,
                verify_state="frame_20350.state")
    if args.part in ("all", "boss"):
        capture(args.out, "water_rabbit", 20350, 30100,
                "stage_01_restaurant_boss_safe.txt",
                ppu_every=2, shots_every=40, infinite_hp=True)
    if args.part in ("all", "music"):
        capture_idle_music(args.out)


if __name__ == "__main__":
    main()
