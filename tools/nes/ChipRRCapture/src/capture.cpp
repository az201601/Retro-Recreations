// ChipRRCapture - headless capture harness for Chip 'n Dale: Rescue Rangers 2 (USA)
//
// Built on the nes-py emulator core (MIT, see LICENSE_nes-py.txt).
// Boots the ROM, runs a scripted controller input, and records a per-frame
// trace (palette, live CHR banking, OAM, CPU RAM) that the Python extractor
// turns into pixel-exact sprite sheets / tilesets / level maps.
//
// usage: capture ROM frames outdir "f:b,f:b,..." [traceFrom traceTo] [ppmEvery]
//   buttons: A=1 B=2 SELECT=4 START=8 UP=16 DOWN=32 LEFT=64 RIGHT=128
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <set>
#include <fstream>
#include <algorithm>
#include "emulator.hpp"
#include "mappers/mapper_SxROM.hpp"

using namespace NES;

static void dumpPPM(const char* path, NES_Pixel* buf, int w, int h) {
    std::ofstream f(path, std::ios::binary);
    f << "P6\n" << w << " " << h << "\n255\n";
    for (int i = 0; i < w * h; ++i) {
        NES_Pixel p = buf[i];
        unsigned char rgb[3] = {(unsigned char)((p >> 16) & 0xff),
                                (unsigned char)((p >> 8) & 0xff),
                                (unsigned char)(p & 0xff)};
        f.write((char*)rgb, 3);
    }
}

struct Rec {  // fixed 2344-byte per-frame record
    int32_t frame;
    uint8_t chr_lo, chr_hi, prg_lo, prg_hi, chr_mode, prg_mode;
    uint8_t spr_page, bg_page, long_sprites;
    uint8_t pad[3];
    uint8_t palette[32];
    uint8_t oam[256];
    uint8_t ram[2048];
    uint8_t vram[2048];
};

int main(int argc, char** argv) {
    std::string rom = argc > 1 ? argv[1] : "Chip 'n Dale - Rescue Rangers 2 (USA).nes";
    int frames = argc > 2 ? atoi(argv[2]) : 600;
    std::string outdir = argc > 3 ? argv[3] : "out/cap";
    std::string scriptArg = argc > 4 ? argv[4] : "200:8";
    int traceFrom = argc > 5 ? atoi(argv[5]) : 0;
    int traceTo = argc > 6 ? atoi(argv[6]) : 1000000;
    int ppmEvery = argc > 7 ? atoi(argv[7]) : 60;

    // script: "frame:buttons,frame:buttons,..." held for a single frame unless
    // written as start-end:buttons (held inclusive)
    struct Ev { int a, b; int btn; };
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
    auto buttonsAt = [&](int f) -> NES_Byte {
        int b = 0;
        for (auto& e : script) if (f >= e.a && f <= e.b) b |= e.btn;
        return (NES_Byte)b;
    };

    Emulator emu(rom);
    char path[512];
    snprintf(path, sizeof path, "%s/trace.bin", outdir.c_str());
    std::ofstream trace(path, std::ios::binary);
    if (!trace) { fprintf(stderr, "cannot open %s\n", path); return 2; }

    std::set<int> chrWindows;
    // optional: hide sprites for the whole run to capture clean backgrounds
    const char* envhide = getenv("HIDE_SPRITES");
    if (envhide && *envhide == '1') emu.raw_set_hide_sprites(true);

    for (int f = 0; f < frames; ++f) {
        NES_Byte* pad = emu.get_controller(0);
        *pad = buttonsAt(f);
        // mirror onto port 2 as well: makes the harness robust to which port
        // the game polls for player 1
        *emu.get_controller(1) = buttonsAt(f);
        emu.step();

        MapperSxROM* s = dynamic_cast<MapperSxROM*>(emu.raw_mapper());
        if (!s) { fprintf(stderr, "not SxROM\n"); return 3; }
        chrWindows.insert(s->chr_bank_lo());
        chrWindows.insert(s->chr_bank_hi());

        if (f >= traceFrom && f <= traceTo) {
            Rec r;
            memset(&r, 0, sizeof r);
            r.frame = f;
            r.chr_lo = (uint8_t)s->chr_bank_lo();
            r.chr_hi = (uint8_t)s->chr_bank_hi();
            r.prg_lo = (uint8_t)s->prg_bank_lo();
            r.prg_hi = (uint8_t)s->prg_bank_hi();
            r.chr_mode = (uint8_t)s->chr_mode();
            r.prg_mode = (uint8_t)s->prg_mode();
            r.spr_page = (uint8_t)emu.raw_ppu().raw_sprite_page();
            r.bg_page = (uint8_t)emu.raw_ppu().raw_background_page();
            r.long_sprites = emu.raw_ppu().raw_long_sprites() ? 1 : 0;
            NES_Address va = emu.raw_ppu().raw_vram_addr();
            r.pad[0] = (uint8_t)(va & 0xff);
            r.pad[1] = (uint8_t)(va >> 8);
            r.pad[2] = emu.raw_ppu().raw_fine_x();
            // pad[3..] unused
            memcpy(r.palette, emu.raw_picture_bus().raw_palette(), 32);
            memcpy(r.oam, emu.raw_ppu().raw_OAM(), 256);
            memcpy(r.ram, emu.raw_ram(), 2048);
            memcpy(r.vram, emu.raw_picture_bus().raw_ram(), 2048);
            trace.write((const char*)&r, sizeof r);
        }
        if (ppmEvery > 0 && f % ppmEvery == 0) {
            snprintf(path, sizeof path, "%s/frames/f%05d.ppm", outdir.c_str(), f);
            dumpPPM(path, emu.get_screen_buffer(), Emulator::WIDTH, Emulator::HEIGHT);
        }
    }
    snprintf(path, sizeof path, "%s/frames/final.ppm", outdir.c_str());
    dumpPPM(path, emu.get_screen_buffer(), Emulator::WIDTH, Emulator::HEIGHT);

    // report pattern-table windows used by the game during this run
    std::ofstream meta((outdir + "/trace.json").c_str());
    meta << "{\"rom\":\"" << rom << "\",\"frames\":" << frames
         << ",\"record_size\":" << sizeof(Rec) << ",\"chr_windows\":[";
    bool first = true;
    for (int b : chrWindows) { meta << (first ? "" : ",") << b; first = false; }
    meta << "]}\n";
    fprintf(stderr, "chr windows:");
    for (int b : chrWindows) fprintf(stderr, " %d", b);
    fprintf(stderr, "\n");
    return 0;
}
