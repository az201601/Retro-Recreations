/* retroshot - minimal headless libretro frontend for asset capture.
 * Usage: retroshot -c core.so -r rom.nes -t timeline.txt -o outdir [-m maxframes]
 * Timeline lines:  <frame> <cmd> [args]
 *   press|release <BTN>   BTN in A B SELECT START UP DOWN LEFT RIGHT
 *   tap <BTN> <nframes>
 *   shot <name>           writes outdir/<name>.ppm at that frame
 *   quit
 * Runs frame-by-frame; commands apply after the frame with that index completes
 * (inputs take effect on the following frame).
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdarg.h>
#include "libretro.h"

static void core_log(enum retro_log_level level, const char *fmt, ...) {
    (void)level;
    va_list ap; va_start(ap, fmt);
    fprintf(stderr, "[core] ");
    vfprintf(stderr, fmt, ap);
    va_end(ap);
}
/* retro_* entry points are linked directly from fceumm_libretro.so */

/* ---- video ---- */
static enum retro_pixel_format pixfmt = RETRO_PIXEL_FORMAT_0RGB1555;
static unsigned fw = 0, fh = 0;
static size_t fpitch = 0;
static uint8_t raw[256 * 4 * 240 * 2];
static bool have_frame = false;

static void video_cb(const void *data, unsigned width, unsigned height, size_t pitch) {
    if (data == NULL) return; /* dupe */
    fw = width; fh = height; fpitch = pitch;
    size_t n = pitch * height;
    if (n > sizeof(raw)) n = sizeof(raw);
    memcpy(raw, data, n);
    have_frame = true;
}

static void write_ppm(const char *path) {
    if (!have_frame) { fprintf(stderr, "no frame to save\n"); return; }
    FILE *f = fopen(path, "wb");
    if (!f) { perror(path); return; }
    fprintf(f, "P6\n%u %u\n255\n", fw, fh);
    for (unsigned y = 0; y < fh; y++) {
        const uint8_t *row = raw + y * fpitch;
        for (unsigned x = 0; x < fw; x++) {
            uint8_t rgb[3];
            if (pixfmt == RETRO_PIXEL_FORMAT_XRGB8888) {
                uint32_t p; memcpy(&p, row + x * 4, 4);
                rgb[0] = (p >> 16) & 0xFF; rgb[1] = (p >> 8) & 0xFF; rgb[2] = p & 0xFF;
            } else if (pixfmt == RETRO_PIXEL_FORMAT_RGB565) {
                uint16_t p; memcpy(&p, row + x * 2, 2);
                unsigned r = (p >> 11) & 0x1F, g = (p >> 5) & 0x3F, b = p & 0x1F;
                rgb[0] = (r << 3) | (r >> 2); rgb[1] = (g << 2) | (g >> 4); rgb[2] = (b << 3) | (b >> 2);
            } else { /* 0RGB1555 */
                uint16_t p; memcpy(&p, row + x * 2, 2);
                unsigned r = (p >> 10) & 0x1F, g = (p >> 5) & 0x1F, b = p & 0x1F;
                rgb[0] = (r << 3) | (r >> 2); rgb[1] = (g << 3) | (g >> 2); rgb[2] = (b << 3) | (b >> 2);
            }
            fwrite(rgb, 1, 3, f);
        }
    }
    fclose(f);
    fprintf(stderr, "shot %s (%ux%u fmt=%d)\n", path, fw, fh, (int)pixfmt);
}

/* ---- audio ---- */
static int16_t *abuf = NULL;
static size_t alen = 0, acap = 0; /* in int16 samples */
static size_t audio_cb(const int16_t *data, size_t frames) {
    size_t n = frames * 2;
    if (alen + n > acap) {
        acap = (alen + n) * 2 + 8192;
        abuf = realloc(abuf, acap * sizeof(int16_t));
    }
    memcpy(abuf + alen, data, n * sizeof(int16_t));
    alen += n;
    return frames;
}
static void audio_smp_cb(int16_t l, int16_t r) {
    if (alen + 2 > acap) {
        acap = (alen + 2) * 2 + 8192;
        abuf = realloc(abuf, acap * sizeof(int16_t));
    }
    abuf[alen++] = l; abuf[alen++] = r;
}
static double sample_rate = 44100.0;

static void write_wav(const char *path) {
    FILE *f = fopen(path, "wb");
    if (!f) { perror(path); return; }
    uint32_t sr = (uint32_t)sample_rate;
    uint32_t data_len = (uint32_t)(alen * 2);
    uint32_t byte_rate = sr * 2 * 2;
    uint8_t hdr[44] = {
        'R','I','F','F', 0,0,0,0, 'W','A','V','E',
        'f','m','t',' ', 16,0,0,0, 1,0, 2,0,
        0,0,0,0, 0,0,0,0, 4,0, 16,0,
        'd','a','t','a', 0,0,0,0
    };
    memcpy(hdr + 24, &sr, 4);
    memcpy(hdr + 28, &byte_rate, 4);
    uint32_t riff = 36 + data_len;
    memcpy(hdr + 4, &riff, 4);
    memcpy(hdr + 40, &data_len, 4);
    fwrite(hdr, 1, 44, f);
    fwrite(abuf, 1, data_len, f);
    fclose(f);
    fprintf(stderr, "wav %s (%u samples @ %u Hz)\n", path, data_len / 4, sr);
}

/* ---- input ---- */
static uint16_t buttons = 0; /* bit per RETRO_DEVICE_ID_JOYPAD_* */

static void input_poll_cb(void) {}
static int16_t input_state_cb(unsigned port, unsigned device, unsigned index, unsigned id) {
    (void)index;
    if (port == 0 && device == RETRO_DEVICE_JOYPAD && id < 16)
        return (buttons >> id) & 1;
    return 0;
}

/* ---- environment ---- */
static bool env_cb(unsigned cmd, void *data) {
    switch (cmd) {
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT: {
        enum retro_pixel_format *f = data;
        if (*f == RETRO_PIXEL_FORMAT_0RGB1555 || *f == RETRO_PIXEL_FORMAT_XRGB8888 || *f == RETRO_PIXEL_FORMAT_RGB565) {
            pixfmt = *f; return true;
        }
        return false;
    }
    case RETRO_ENVIRONMENT_GET_CAN_DUPE: *(bool *)data = true; return true;
    case RETRO_ENVIRONMENT_SET_GEOMETRY:
    case RETRO_ENVIRONMENT_SET_SYSTEM_AV_INFO:
    case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:
    case RETRO_ENVIRONMENT_SET_VARIABLES:
    case RETRO_ENVIRONMENT_SET_CORE_OPTIONS:
    case RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2:
        return true;
    case RETRO_ENVIRONMENT_GET_VARIABLE:
    case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:
        ((struct retro_variable *)data)->value = NULL;
        return false;
    case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:
    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
        *(const char **)data = "/tmp";
        return true;
    case RETRO_ENVIRONMENT_GET_LOG_INTERFACE:
        ((struct retro_log_callback *)data)->log = core_log;
        return true;
    default:
        return false;
    }
}

/* ---- timeline ---- */
enum ev_type { EV_PRESS, EV_RELEASE, EV_SHOT, EV_QUIT, EV_RESET, EV_RAM, EV_RAMPRE };
struct event { int frame; enum ev_type type; char name[64]; };
static struct event events[512];
static int nevents = 0;
static int max_frame = 60000;
static const char *outdir = "out";

static int btn_from_name(const char *n) {
    if (!strcmp(n, "A")) return RETRO_DEVICE_ID_JOYPAD_A;
    if (!strcmp(n, "B")) return RETRO_DEVICE_ID_JOYPAD_B;
    if (!strcmp(n, "SELECT")) return RETRO_DEVICE_ID_JOYPAD_SELECT;
    if (!strcmp(n, "START")) return RETRO_DEVICE_ID_JOYPAD_START;
    if (!strcmp(n, "UP")) return RETRO_DEVICE_ID_JOYPAD_UP;
    if (!strcmp(n, "DOWN")) return RETRO_DEVICE_ID_JOYPAD_DOWN;
    if (!strcmp(n, "LEFT")) return RETRO_DEVICE_ID_JOYPAD_LEFT;
    if (!strcmp(n, "RIGHT")) return RETRO_DEVICE_ID_JOYPAD_RIGHT;
    return -1;
}

static void load_timeline(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) { perror(path); exit(1); }
    char line[256];
    while (fgets(line, sizeof line, f)) {
        if (line[0] == '#' || line[0] == '\n' || line[0] == '\r') continue;
        char a[64], b[64], c[64]; int frame;
        int n = sscanf(line, "%d %63s %63s %63s", &frame, a, b, c);
        if (n < 2) continue;
        if (!strcmp(a, "press") || !strcmp(a, "release")) {
            struct event *e = &events[nevents++];
            e->frame = frame; e->type = a[0]=='p' ? EV_PRESS : EV_RELEASE;
            snprintf(e->name, sizeof e->name, "%s", b);
        } else if (!strcmp(a, "tap")) {
            struct event *e = &events[nevents++];
            e->frame = frame; e->type = EV_PRESS;
            snprintf(e->name, sizeof e->name, "%s", b);
            int hold = (n >= 4) ? atoi(c) : 5;
            e = &events[nevents++];
            e->frame = frame + hold; e->type = EV_RELEASE;
            snprintf(e->name, sizeof e->name, "%s", b);
        } else if (!strcmp(a, "shot")) {
            struct event *e = &events[nevents++];
            e->frame = frame; e->type = EV_SHOT;
            snprintf(e->name, sizeof e->name, "%s", b);
        } else if (!strcmp(a, "ram")) {
            struct event *e = &events[nevents++];
            e->frame = frame; e->type = EV_RAM;
            snprintf(e->name, sizeof e->name, "%s", b);
        } else if (!strcmp(a, "rampre")) {
            struct event *e = &events[nevents++];
            e->frame = frame; e->type = EV_RAMPRE;
            snprintf(e->name, sizeof e->name, "%s", b);
        } else if (!strcmp(a, "quit")) {
            struct event *e = &events[nevents++];
            e->frame = frame; e->type = EV_QUIT; e->name[0] = 0;
        } else if (!strcmp(a, "reset")) {
            struct event *e = &events[nevents++];
            e->frame = frame; e->type = EV_RESET; e->name[0] = 0;
        } else {
            fprintf(stderr, "unknown cmd: %s\n", a);
        }
    }
    fclose(f);
    /* sort by frame (stable enough via simple insertion; n small) */
    for (int i = 1; i < nevents; i++) {
        struct event tmp = events[i];
        int j = i;
        while (j > 0 && events[j-1].frame > tmp.frame) { events[j] = events[j-1]; j--; }
        events[j] = tmp;
    }
}

static bool quit_flag = false;

static void dump_ram(const char *name) {
    uint8_t *ram = retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM);
    if (!ram) { fprintf(stderr, "no system ram\n"); return; }
    char p[512];
    snprintf(p, sizeof p, "%s/%s.bin", outdir, name);
    FILE *f = fopen(p, "wb");
    if (!f) { perror(p); return; }
    fwrite(ram, 1, 2048, f);
    fclose(f);
}

/* EV_RAMPRE: snapshot $0200 page BEFORE the frame runs (the OAM image the
 * game prepared during the previous vblank = what this frame renders). */
static void process_pre(int frame) {
    for (int i = 0; i < nevents; i++) {
        struct event *e = &events[i];
        if (e->frame != frame || e->type != EV_RAMPRE) continue;
        dump_ram(e->name);
    }
}

static void process_events(int frame) {
    for (int i = 0; i < nevents; i++) {
        struct event *e = &events[i];
        if (e->frame != frame || e->type == EV_RAMPRE) continue;
        switch (e->type) {
        case EV_RAM:
            dump_ram(e->name);
            break;
        case EV_PRESS: {
            int b = btn_from_name(e->name);
            if (b >= 0) buttons |= (uint16_t)(1 << b);
            break;
        }
        case EV_RELEASE: {
            int b = btn_from_name(e->name);
            if (b >= 0) buttons &= (uint16_t)~(1 << b);
            break;
        }
        case EV_SHOT: {
            char p[512];
            snprintf(p, sizeof p, "%s/%s.ppm", outdir, e->name);
            write_ppm(p);
            break;
        }
        case EV_RESET: retro_reset(); break;
        case EV_QUIT: quit_flag = true; break;
        }
    }
}

int main(int argc, char **argv) {
    const char *core_path = NULL, *rom_path = NULL, *tl_path = NULL;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "-c") && i + 1 < argc) core_path = argv[++i];
        else if (!strcmp(argv[i], "-r") && i + 1 < argc) rom_path = argv[++i];
        else if (!strcmp(argv[i], "-t") && i + 1 < argc) tl_path = argv[++i];
        else if (!strcmp(argv[i], "-o") && i + 1 < argc) outdir = argv[++i];
        else if (!strcmp(argv[i], "-m") && i + 1 < argc) max_frame = atoi(argv[++i]);
        else { fprintf(stderr, "unknown arg %s\n", argv[i]); return 1; }
    }
    if (!core_path || !rom_path || !tl_path) {
        fprintf(stderr, "usage: retroshot -c core.so -r rom.nes -t timeline.txt [-o outdir] [-m maxframes]\n");
        return 1;
    }
    load_timeline(tl_path);

    if (retro_api_version() != RETRO_API_VERSION) fprintf(stderr, "warn: api version mismatch\n");
    fprintf(stderr, "core arg: %s (linked statically at build time)\n", core_path);

    retro_set_environment(env_cb);
    retro_set_video_refresh(video_cb);
    retro_set_audio_sample(audio_smp_cb);
    retro_set_audio_sample_batch(audio_cb);
    retro_set_input_poll(input_poll_cb);
    retro_set_input_state(input_state_cb);
    retro_init();

    struct retro_system_info sinfo = {0};
    retro_get_system_info(&sinfo);
    fprintf(stderr, "core: %s | need_fullpath=%d\n", sinfo.library_name, sinfo.need_fullpath);

    FILE *rf = fopen(rom_path, "rb");
    if (!rf) { perror(rom_path); return 1; }
    fseek(rf, 0, SEEK_END); long rlen = ftell(rf); fseek(rf, 0, SEEK_SET);
    uint8_t *rom = malloc(rlen);
    if (fread(rom, 1, rlen, rf) != (size_t)rlen) { fprintf(stderr, "rom read fail\n"); return 1; }
    fclose(rf);

    struct retro_game_info game = {0};
    game.path = rom_path;
    game.data = rom;
    game.size = (size_t)rlen;
    if (!retro_load_game(&game)) { fprintf(stderr, "retro_load_game failed\n"); return 1; }

    struct retro_system_av_info av = {0};
    retro_get_system_av_info(&av);
    fw = av.geometry.base_width; fh = av.geometry.base_height;
    sample_rate = av.timing.sample_rate;
    fprintf(stderr, "av: %ux%u fps=%.3f sr=%.0f\n", av.geometry.base_width, av.geometry.base_height,
            av.timing.fps, av.timing.sample_rate);

    int framecount = 0;
    process_pre(0);
    process_events(0);
    while (!quit_flag && framecount < max_frame) {
        process_pre(framecount + 1);
        retro_run();
        framecount++;
        process_events(framecount);
    }
    fprintf(stderr, "ran %d frames\n", framecount);

    char wavpath[512];
    snprintf(wavpath, sizeof wavpath, "%s/audio.wav", outdir);
    write_wav(wavpath);

    retro_unload_game();
    retro_deinit();
    free(rom);
    free(abuf);
    return 0;
}
