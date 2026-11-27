# FCEUmm reference capture

The headless capture helper loads the repository ROM in FCEUmm (not JSNES), requests the libretro XRGB8888 video format, records unmodified 256x240 frame callbacks as RGB PPM, and records the APU output as stereo 48 kHz/16-bit PCM WAV.

Build the FCEUmm core from source and compile the helper:

```sh
git clone --depth 1 https://github.com/libretro/libretro-fceumm.git tools/emu/libretro-fceumm
make -C tools/emu/libretro-fceumm -f Makefile.libretro platform=unix -j2
cc -O2 -Itools/emu/libretro-fceumm/src/drivers/libretro/libretro-common/include \
  tools/emu/fceumm_capture.c -ldl -o tools/emu/fceumm_capture
tools/emu/fceumm_capture 1200 tools/out/spotlight_verified 1
```

Arguments are number of emulated frames, output directory, and capture interval in frames. The ignored reference bundle `tools/out/chipdale_spotlight_fceumm_reference.tar.gz` contains all captured frames and audio. The emulator/core source, binary, and captures are excluded from Git by `.gitignore`.

The output establishes a repeatable software-emulator reference, not proof of hardware-perfect accuracy. To claim 100% hardware accuracy, compare frame-by-frame and audio against a verified console capture with the same reset, region, and timing conditions.
