#!/usr/bin/env python3
"""Extract the post-START title menu, retaining only its 1-player choice.

The game is replayed from power-on. At NES frame 1000, START is tapped; the
menu image is captured at frame 1006. Since the 1P menu artwork is static in the
captured range, one full-screen image is enough. The lower 2-player label is
removed from its black menu area. The same run provides the menu BGM capture.
"""
from __future__ import annotations

import argparse
import array
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
EMU = ROOT / "tools" / "emu"
ROM = ROOT / "Chip 'n Dale - Rescue Rangers 2 (USA).nes"
OUT = ROOT / "tools" / "out" / "title_menu"
IMAGE_OUT = ROOT / "extracted" / "title_menu" / "title_1player.png"
AUDIO_OUT = ROOT / "extracted" / "audio" / "music_menu.wav"
START_FRAME = 1000
END_FRAME = 3200
MENU_FIRST_AUDIO_FRAME = 1000
MENU_LAST_AUDIO_FRAME = 3140  # exclusive: 2140 source frames (~35.6 s)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    args = ap.parse_args()
    del args
    if not (EMU / "retroshot").exists() or not (EMU / "libretro-fceumm" / "fceumm_libretro.so").exists():
        ap.error("emulator not built; follow tools/README.md")
    if not ROM.exists():
        ap.error(f"ROM not found: {ROM}")

    OUT.mkdir(parents=True, exist_ok=True)
    IMAGE_OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIO_OUT.parent.mkdir(parents=True, exist_ok=True)
    timeline = OUT / "timeline.txt"
    timeline.write_text(
        f"{START_FRAME} tap START 6\n"
        "1006 shot menu_1p\n"
        f"{END_FRAME} quit\n",
        encoding="ascii",
    )
    subprocess.run(
        [
            str(EMU / "retroshot"),
            "-c", "libretro-fceumm/fceumm_libretro.so",
            "-r", str(ROM),
            "-t", str(timeline),
            "-o", str(OUT),
            "-m", str(END_FRAME + 1),
        ],
        cwd=EMU,
        check=True,
    )

    shot = Image.open(OUT / "menu_1p.ppm").convert("RGB")
    if shot.size != (256, 240):
        raise ValueError(f"unexpected emulator frame size: {shot.size}")
    # Frame 1006 has the 1P row at y=192..201 and the 2P row at y=208..217.
    # The rectangle stays wholly in the uniform NES backdrop below the ledge.
    black = shot.getpixel((0, 220))
    ImageDraw.Draw(shot).rectangle((96, 204, 175, 220), fill=black)
    shot.save(IMAGE_OUT, optimize=True)

    wav_in = OUT / "audio.wav"
    with wave.open(str(wav_in), "rb") as src:
        if (src.getnchannels(), src.getframerate(), src.getsampwidth()) != (2, 48000, 2):
            raise ValueError("expected frontend PCM: stereo, 48 kHz, 16-bit WAV")
        total_frames = src.getnframes()
        stereo_bytes = src.readframes(total_frames)
    stereo = array.array("h")
    stereo.frombytes(stereo_bytes)
    if stereo.itemsize != 2:
        raise RuntimeError("this script requires 16-bit native short samples")
    # The raw frontend WAV uses little-endian PCM; convert if run on big-endian.
    import sys
    if sys.byteorder != "little":
        stereo.byteswap()
    if len(stereo) % 2:
        raise ValueError("stereo sample data is not channel-aligned")

    # Convert emulator-frame positions to the frontend's exact total sample
    # count, avoiding a fractional-rate assumption (the core reports ~60.1 Hz).
    first = round(MENU_FIRST_AUDIO_FRAME * total_frames / END_FRAME)
    last = round(MENU_LAST_AUDIO_FRAME * total_frames / END_FRAME)
    first *= 2
    last *= 2
    mono = array.array("h", ((stereo[i] + stereo[i + 1]) // 2 for i in range(first, last, 2)))
    if sys.byteorder != "little":
        mono.byteswap()
    with wave.open(str(AUDIO_OUT), "wb") as dst:
        dst.setnchannels(1)
        dst.setsampwidth(2)
        dst.setframerate(48000)
        dst.writeframes(mono.tobytes())

    with wave.open(str(AUDIO_OUT), "rb") as check:
        seconds = check.getnframes() / check.getframerate()
    print(f"Wrote {IMAGE_OUT.relative_to(ROOT)} (256x240, 1P only)")
    print(f"Wrote {AUDIO_OUT.relative_to(ROOT)} ({seconds:.3f}s, mono 48 kHz / 16-bit)")


if __name__ == "__main__":
    main()
