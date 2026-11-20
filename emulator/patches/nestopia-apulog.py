#!/usr/bin/env python3
"""
nestopia-apulog.py - add an APU register-write log to the pinned Nestopia core.

Why: to reproduce Gradius's music and sound effects frame-exactly, the thing
you need is not the waveform - it is the exact stream of writes the game makes
to $4000-$4013/$4015 and the exact moment of each.  Nestopia is cycle
accurate, so it knows the CPU timestamp of every write; nothing else in the
toolchain does.

What it adds (all behind an environment variable, so normal runs are
untouched):

  NES_APULOG=/path/file.log   log every APU register write
  NES_APULOG_CPU=0            log PPU/CPU-visible writes too (future use)

Line format, one write per line:

    <frame> <cpucycle> <addr> <data>
    frame     libretro frame counter (frame 0 = first emulated frame)
    cpucycle  CPU cycles since that frame began; this is the timing
              resolution the recreation has to match
    addr      $4000-$4017 as written
    data      8-bit value

The patch is applied by emulator/build.sh with `--check`, so a second run is a
no-op and a changed upstream file fails loudly instead of producing a silently
different oracle.
"""

from __future__ import annotations

import sys

MARKER = "/* nesrun-apulog: patched */"

HOOK = r'''
/* ---- nesrun-apulog: APU register write log ------------------------------ *
 * Enabled only when NES_APULOG names a file.  One line per write:
 *   <frame> <cpucycle-in-frame> <addr> <data>
 * Frames are counted at BeginFrame(), which the libretro core calls once per
 * emulated frame, so the log lines up with the PNG/hash capture.           */
#ifndef NESRUN_APULOG_H
#define NESRUN_APULOG_H
#include <cstdio>
#include <cstdlib>
#include <cstring>
class ApuWriteLogNs
{
public:
   static ApuWriteLogNs& Instance()
   {
      static ApuWriteLogNs log;
      return log;
   }
   void Open()
   {
      const char* p = getenv( "NES_APULOG" );
      if (file || !p || !*p) return;
      file = std::fopen( p, "w" );
      frame = 0;
   }
   void Frame( unsigned long long baseCycles )
   {
      ++frame;
      frameBase = baseCycles;      /* cpu cycles are absolute; log frame-relative */
   }
   void Write( unsigned addr, unsigned data, unsigned long long cyc )
   {
      if (!file) return;
      std::fprintf( file, "%llu %llu %02X %02X\n", frame,
                    cyc >= frameBase ? cyc - frameBase : cyc,
                    addr & 0xFFFFU, data & 0xFFU );
   }
   bool Enabled() const { return file != 0; }
private:
   ApuWriteLogNs() : file(0), frame(0), frameBase(0) {}
   ~ApuWriteLogNs() { if (file) std::fclose( file ); }
   std::FILE* file;
   unsigned long long frame;
   unsigned long long frameBase;
};
#endif
'''

PATCH_POINTS = [
    # (file, original text, replacement text)
    (
        "source/core/NstApu.cpp",
        "\t\tNES_POKE_AD(Apu,4000)\n\t\t{\n",
        MARKER + HOOK + "\n\t\tNES_POKE_AD(Apu,4000)\n\t\t{\n\t\t\tApuWriteLogNs::Instance().Write( address, data, (unsigned long long)cpu.GetCycles() );\n",
    ),
    (
        "source/core/NstApu.cpp",
        "\t\tNES_POKE_AD(Apu,4001)\n\t\t{\n",
        "\t\tNES_POKE_AD(Apu,4001)\n\t\t{\n\t\t\tApuWriteLogNs::Instance().Write( address, data, (unsigned long long)cpu.GetCycles() );\n",
    ),
    (
        "source/core/NstApu.cpp",
        "\t\tNES_POKE_AD(Apu,4002)\n\t\t{\n",
        "\t\tNES_POKE_AD(Apu,4002)\n\t\t{\n\t\t\tApuWriteLogNs::Instance().Write( address, data, (unsigned long long)cpu.GetCycles() );\n",
    ),
    (
        "source/core/NstApu.cpp",
        "\t\tNES_POKE_AD(Apu,4003)\n\t\t{\n",
        "\t\tNES_POKE_AD(Apu,4003)\n\t\t{\n\t\t\tApuWriteLogNs::Instance().Write( address, data, (unsigned long long)cpu.GetCycles() );\n",
    ),
    (
        "source/core/NstApu.cpp",
        "\t\tNES_POKE_D(Apu,4008)\n\t\t{\n",
        "\t\tNES_POKE_D(Apu,4008)\n\t\t{\n\t\t\tApuWriteLogNs::Instance().Write( address, data, (unsigned long long)cpu.GetCycles() );\n",
    ),
    (
        "source/core/NstApu.cpp",
        "\t\tNES_POKE_D(Apu,400A)\n\t\t{\n",
        "\t\tNES_POKE_D(Apu,400A)\n\t\t{\n\t\t\tApuWriteLogNs::Instance().Write( address, data, (unsigned long long)cpu.GetCycles() );\n",
    ),
    (
        "source/core/NstApu.cpp",
        "\t\tNES_POKE_D(Apu,400B)\n\t\t{\n",
        "\t\tNES_POKE_D(Apu,400B)\n\t\t{\n\t\t\tApuWriteLogNs::Instance().Write( address, data, (unsigned long long)cpu.GetCycles() );\n",
    ),
    (
        "source/core/NstApu.cpp",
        "\t\tNES_POKE_D(Apu,400C)\n\t\t{\n",
        "\t\tNES_POKE_D(Apu,400C)\n\t\t{\n\t\t\tApuWriteLogNs::Instance().Write( address, data, (unsigned long long)cpu.GetCycles() );\n",
    ),
    (
        "source/core/NstApu.cpp",
        "\t\tNES_POKE_D(Apu,400E)\n\t\t{\n",
        "\t\tNES_POKE_D(Apu,400E)\n\t\t{\n\t\t\tApuWriteLogNs::Instance().Write( address, data, (unsigned long long)cpu.GetCycles() );\n",
    ),
    (
        "source/core/NstApu.cpp",
        "\t\tNES_POKE_D(Apu,400F)\n\t\t{\n",
        "\t\tNES_POKE_D(Apu,400F)\n\t\t{\n\t\t\tApuWriteLogNs::Instance().Write( address, data, (unsigned long long)cpu.GetCycles() );\n",
    ),
    (
        "source/core/NstApu.cpp",
        "\t\tNES_POKE_D(Apu,4010)\n\t\t{\n",
        "\t\tNES_POKE_D(Apu,4010)\n\t\t{\n\t\t\tApuWriteLogNs::Instance().Write( address, data, (unsigned long long)cpu.GetCycles() );\n",
    ),
    (
        "source/core/NstApu.cpp",
        "\t\tNES_POKE_AD(Apu,4011)\n\t\t{\n",
        "\t\tNES_POKE_AD(Apu,4011)\n\t\t{\n\t\t\tApuWriteLogNs::Instance().Write( address, data, (unsigned long long)cpu.GetCycles() );\n",
    ),
    (
        "source/core/NstApu.cpp",
        "\t\tNES_POKE_AD(Apu,4012)\n\t\t{\n",
        "\t\tNES_POKE_AD(Apu,4012)\n\t\t{\n\t\t\tApuWriteLogNs::Instance().Write( address, data, (unsigned long long)cpu.GetCycles() );\n",
    ),
    (
        "source/core/NstApu.cpp",
        "\t\tNES_POKE_AD(Apu,4013)\n\t\t{\n",
        "\t\tNES_POKE_AD(Apu,4013)\n\t\t{\n\t\t\tApuWriteLogNs::Instance().Write( address, data, (unsigned long long)cpu.GetCycles() );\n",
    ),
    (
        "source/core/NstApu.cpp",
        "\t\tNES_POKE_D(Apu,4015)\n\t\t{\n",
        "\t\tNES_POKE_D(Apu,4015)\n\t\t{\n\t\t\tApuWriteLogNs::Instance().Write( address, data, (unsigned long long)cpu.GetCycles() );\n",
    ),
]

FRAME_HOOK = (
    "source/core/NstApu.cpp",
    "\t\tvoid Apu::BeginFrame(Sound::Output* output)\n\t\t{\n",
    "\t\tvoid Apu::BeginFrame(Sound::Output* output)\n\t\t{\n"
    "\t\t\tApuWriteLogNs::Instance().Frame();\n",
)


import re

HOOK_LINE = ("\t\t\tApuWriteLogNs::Instance().Write( address, data, "
             "(unsigned long long)cpu.GetCycles() );\n")


def patch_apu(path: str) -> int:
    """Insert a log call at the top of every APU register write handler."""
    src = open(path, encoding="utf-8", errors="surrogateescape").read()
    if "ApuWriteLogNs::Instance().Write(" in src:
        return 0
    # NES_POKE_AD(Apu,4000) {   /  NES_POKE_D(Apu,400C) {   ...
    pattern = re.compile(r"(NES_POKE_(AD|A|D)\(Apu,(40[0-1][0-9A-F])\)\n\t\t\{\n)")

    def sub(m):
        # NES_POKE_D handlers only receive data; the macro's own address is
        # available as a compile-time constant via the handler name.
        kind, reg = m.group(2), m.group(3)
        line = HOOK_LINE
        if kind == "D":
            line = line.replace("address, data", "0x%sU, data" % reg)
        return m.group(1) + line

    new, n = pattern.subn(sub, src)
    if n == 0:
        raise SystemExit("nestopia-apulog: no APU write handlers found - "
                         "the pinned core changed; update the patch script")
    open(path, "w", encoding="utf-8", errors="surrogateescape").write(new)
    return n


def apply_frame_hook(path: str) -> str:
    src = open(path, encoding="utf-8", errors="surrogateescape").read()
    if "ApuWriteLogNs::Instance().Frame();" in src:
        return "already"
    marker = "void Apu::BeginFrame(Sound::Output* output)"
    idx = src.find(marker)
    if idx < 0:
        raise SystemExit("nestopia-apulog: BeginFrame not found")
    # insert just after the opening brace of the function body
    brace = src.find("{", idx)
    insert = ("\n\t\t\tApuWriteLogNs::Instance().Open();"
              "\n\t\t\tApuWriteLogNs::Instance().Frame( (unsigned long long)cpu.GetCycles() );")
    src = src[:brace + 1] + insert + src[brace + 1:]
    open(path, "w", encoding="utf-8", errors="surrogateescape").write(src)
    return "patched"


def main(argv):
    check_only = "--check" in argv
    rest = [a for a in argv if not a.startswith("--")]
    root = rest[0] if rest else "."
    apu = f"{root}/source/core/NstApu.cpp"
    src = open(apu, encoding="utf-8", errors="surrogateescape").read()

    if check_only:
        if MARKER not in src or "ApuWriteLogNs::Instance().Open();" not in src:
            raise SystemExit("nestopia-apulog: NOT applied")
        print(f"nestopia-apulog: present ({src.count('ApuWriteLogNs::Instance().Write')} handlers hooked)")
        return 0

    if MARKER not in src:
        # insert the log class right after the last #include at the top of the
        # file: BeginFrame() appears earlier in the file than the write
        # handlers, and both need to see the class.
        lines = src.split("\n")
        last_inc = max(i for i, l in enumerate(lines) if l.startswith("#include"))
        block = ("\n/* nesrun-apulog: patched */"
                 + HOOK.replace("/* nesrun-apulog: patched */", "")
                 ).rstrip("\n").split("\n")
        lines[last_inc + 1:last_inc + 1] = block
        src = "\n".join(lines)
        open(apu, "w", encoding="utf-8", errors="surrogateescape").write(src)

    n = patch_apu(apu)
    apply_frame_hook(apu)
    out = open(apu, encoding="utf-8", errors="surrogateescape").read()
    print(f"nestopia-apulog: patched {n} APU write handlers in {root}")
    print(f"nestopia-apulog: total hooks now {out.count('ApuWriteLogNs::Instance().Write')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
