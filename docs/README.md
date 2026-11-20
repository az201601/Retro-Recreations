# Reference documentation

Reverse-engineering notes for the Gradius port.  Everything here is derived
from the pinned ROM and the pinned emulator; each file says how to regenerate
it, so nothing has to be taken on trust.

| file | what it answers |
|---|---|
| `rammap.md` | which RAM addresses the code touches, and which are arrays/records (`tools/rammap.py`) |
| `objects-and-oam.md` | 32-slot SoA object layout (`$0100-$04FF`), player fields, and `$0200` OAM staging |
| `audio.md` | what the sound driver did frame by frame: notes, envelopes, tempo, SFX windows (`tools/apumap.py`) |
| `sound-driver.md` | how the sound engine is built — registers, tick, envelopes (hand-written from the trace) |
| `disassembly/` | generated 6502 listings + `instructions.json` (git-ignored, ~1 MB) |

Regenerating:

```sh
# disassembly (needs the traced seed list; see docs/rammap.md header)
./tools/nesdis.py --rom "Gradius (USA).nes" --out docs/disassembly $(cat seeds.txt)
./tools/rammap.py --dis docs/disassembly --out docs/rammap.md

# audio
NES_APULOG=/tmp/apu.log ./emulator/out/nesrun --core emulator/out/cores/nestopia_libretro.so \
   --rom "Gradius (USA).nes" --var-file oracle/out/attract/vars.txt --frames 1200 \
   --input oracle/inputs/boot_to_game.txt --quiet
./tools/apumap.py /tmp/apu.log --out docs/audio.md
```

`seeds.txt` is not tracked (it is regenerated from the ROM in seconds — the
generator is described in `docs/rammap.md`); the exclusion of `$FE20` matters,
it is music data and will send the tracer into an endless walk.
