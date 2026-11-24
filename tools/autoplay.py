#!/usr/bin/env python3
"""Drive the headless emulator interactively.

``retroshot -i`` speaks a tiny line protocol; this class wraps it so Python can
play the game, poll RAM, and snapshot rooms.  It also collects the per-frame
frame counter so callers can keep their own timelines honest.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


class Retroshot:
    def __init__(self, rom: str | Path, outdir: str | Path, emu_dir: str | Path | None = None,
                 core: str = "libretro-fceumm/fceumm_libretro.so"):
        self.outdir = Path(outdir).resolve()
        self.outdir.mkdir(parents=True, exist_ok=True)
        rom = Path(rom).resolve()
        emu_dir = Path(emu_dir or Path(__file__).resolve().parent / "emu").resolve()
        self.proc = subprocess.Popen(
            [str(emu_dir / "retroshot"), "-c", core, "-r", str(rom), "-i", "-o", str(self.outdir)],
            cwd=str(emu_dir), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1,
        )
        self.frame = self._expect()

    def _expect(self) -> int:
        line = self.proc.stdout.readline()
        if not line:
            raise RuntimeError("emulator exited unexpectedly")
        parts = line.split()
        if parts[0] == "ERR":
            raise RuntimeError(f"emulator rejected command: {' '.join(parts[1:])}")
        if parts[0] != "OK":
            raise RuntimeError(f"unexpected emulator response: {line!r}")
        return int(parts[1])

    def cmd(self, text: str) -> int:
        assert self.proc.stdin is not None
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()
        self.frame = self._expect()
        return self.frame

    # convenience wrappers -------------------------------------------------
    def run(self, frames: int) -> int:
        return self.cmd(f"run {frames}")

    def press(self, button: str) -> int:
        return self.cmd(f"press {button}")

    def release(self, button: str) -> int:
        return self.cmd(f"release {button}")

    def tap(self, button: str, hold: int = 6) -> int:
        return self.cmd(f"tap {button} {hold}")

    def load(self, state: str | Path) -> int:
        """Restore a savestate.

        Paths are resolved here because the emulator process runs with its own
        working directory; passing a relative path used to fail silently and
        leave the previous state running.
        """
        path = Path(state)
        if not path.is_absolute():
            path = path.resolve()
        if self.frame == 0:
            # The core has not produced a frame yet; unserialize is a no-op
            # before that, so prime it and then restore.
            self.cmd("run 1")
        return self.cmd(f"load {path}")

    def save(self, name: str | Path) -> int:
        path = Path(name)
        if not path.is_absolute():
            path = self.outdir / path.name
        return self.cmd(f"state {path.with_suffix('')}")

    def screenshot(self, name: str | Path) -> int:
        path = Path(name)
        if not path.is_absolute():
            path = self.outdir / path.name
        return self.cmd(f"shot {path.with_suffix('')}")

    def ram(self, name: str) -> bytes:
        self.cmd(f"ram {name}")
        return (self.outdir / f"{name}.bin").read_bytes()

    def state(self, name: str) -> Path:
        self.cmd(f"state {name}")
        return self.outdir / f"{name}.fcs"

    def shot(self, name: str) -> Path:
        self.cmd(f"shot {name}")
        return self.outdir / f"{name}.ppm"

    def run_until(self, frame: int) -> int:
        """Advance to an absolute frame, in one call (emulator is fast)."""
        if frame > self.frame:
            self.run(frame - self.frame)
        return self.frame

    def close(self) -> None:
        if self.proc.poll() is None:
            try:
                if self.proc.stdin:
                    self.proc.stdin.write("quit\n")
                    self.proc.stdin.flush()
            except BrokenPipeError:
                pass
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
