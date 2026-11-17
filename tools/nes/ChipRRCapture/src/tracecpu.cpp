// tracecpu - instruction-level trace of the game's input handling.
//
// Runs the ROM with a scripted controller and writes every executed
// instruction in the window [fromFrame, toFrame] to a binary file:
//
//   record = u32 frame | u16 pc | u8 a | u8 x   (8 bytes)
//
// usage: tracecpu ROM fromFrame toFrame out.bin "script"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <fstream>
#include "emulator.hpp"

using namespace NES;

int main(int argc, char** argv) {
    std::string rom = argc > 1 ? argv[1] : "Chip 'n Dale - Rescue Rangers 2 (USA).nes";
    int from = argc > 2 ? atoi(argv[2]) : 700;
    int to = argc > 3 ? atoi(argv[3]) : 760;
    std::string out = argc > 4 ? argv[4] : "out/trace.pc";
    std::string scriptArg = argc > 5 ? argv[5] : "";

    struct Ev { int a, b, btn; };
    std::vector<Ev> script;
    {
        std::string cur;
        for (char c : scriptArg + ",") {
            if (c == ',') {
                if (!cur.empty()) {
                    size_t k = cur.find(':');
                    std::string fr = cur.substr(0, k);
                    int btn = k == std::string::npos ? 8 : (int)strtol(cur.c_str() + k + 1, nullptr, 0);
                    size_t d = fr.find('-');
                    int a = atoi(fr.substr(0, d).c_str());
                    int b = d == std::string::npos ? a : atoi(fr.c_str() + d + 1);
                    script.push_back({a, b, btn});
                }
                cur.clear();
            } else cur += c;
        }
    }

    Emulator emu(rom);
    std::ofstream f(out, std::ios::binary);
    if (!f) { fprintf(stderr, "cannot open %s\n", out.c_str()); return 2; }

    for (int frame = 0; frame <= to; ++frame) {
        int b = 0;
        for (auto& e : script) if (frame >= e.a && frame <= e.b) b |= e.btn;
        NES_Byte pad = (NES_Byte)b;
        *emu.get_controller(0) = pad;
        *emu.get_controller(1) = pad;

        if (frame < from) { emu.step(); continue; }

        // step instruction by instruction for the whole frame
        char buf[8 * 4096];
        int n = 0;
        while (emu.raw_cycle_budget < Emulator::RAW_CYCLES_PER_FRAME) {
            NES_Address pc = emu.raw_cpu().reg_PC();
            uint32_t fr = (uint32_t)frame;
            memcpy(buf + n, &fr, 4);
            buf[n + 4] = pc & 0xff; buf[n + 5] = pc >> 8;
            buf[n + 6] = emu.raw_cpu().reg_A();
            buf[n + 7] = emu.raw_cpu().reg_X();
            n += 8;
            if (n >= 8 * 4090) { f.write(buf, n); n = 0; }
            emu.step_instruction();
        }
        if (n) f.write(buf, n);
    }
    return 0;
}
