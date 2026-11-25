#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <dlfcn.h>
#include <stdarg.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <errno.h>

#include "libretro.h"

static void *core;
static struct retro_system_av_info av;
static uint32_t *frame_buf;
static unsigned frame_w, frame_h, frame_pitch_pixels;
static int pixel_format = RETRO_PIXEL_FORMAT_XRGB8888;
static int16_t input_state[16];
static unsigned current_frame = 0;

typedef struct { unsigned frame; int btn; int down; size_t order; } InputEvent;
static InputEvent *events;
static size_t nevents, capevents;

/* Preserve input-file order for simultaneous presses/releases while allowing
 * a checkpoint script to append new (earlier) events after an existing run. */
static int compare_events(const void *a, const void *b) {
    const InputEvent *left = a, *right = b;
    if (left->frame < right->frame) return -1;
    if (left->frame > right->frame) return 1;
    if (left->order < right->order) return -1;
    if (left->order > right->order) return 1;
    return 0;
}

static void (*fn_retro_init)(void);
static void (*fn_retro_deinit)(void);
static void (*fn_retro_set_environment)(retro_environment_t);
static void (*fn_retro_set_video_refresh)(retro_video_refresh_t);
static void (*fn_retro_set_audio_sample)(retro_audio_sample_t);
static void (*fn_retro_set_audio_sample_batch)(retro_audio_sample_batch_t);
static void (*fn_retro_set_input_poll)(retro_input_poll_t);
static void (*fn_retro_set_input_state)(retro_input_state_t);
static bool (*fn_retro_load_game)(const struct retro_game_info*);
static void (*fn_retro_unload_game)(void);
static void (*fn_retro_run)(void);
static void (*fn_retro_get_system_av_info)(struct retro_system_av_info*);
static void *(*fn_retro_get_memory_data)(unsigned);
static size_t (*fn_retro_get_memory_size)(unsigned);
static void (*fn_retro_cheat_reset)(void);
static void (*fn_retro_cheat_set)(unsigned,bool,const char*);
static size_t (*fn_retro_serialize_size)(void);
static bool (*fn_retro_serialize)(void*,size_t);
static bool (*fn_retro_unserialize)(const void*,size_t);

static void die(const char *fmt, ...) {
    va_list ap; va_start(ap, fmt); vfprintf(stderr, fmt, ap); va_end(ap); fputc('\n', stderr); exit(1);
}
static void ensure_dir(const char *p) { mkdir(p, 0755); }

static bool env_cb(unsigned cmd, void *data) {
    switch (cmd) {
        case RETRO_ENVIRONMENT_GET_LOG_INTERFACE: return false;
        case RETRO_ENVIRONMENT_GET_CAN_DUPE: { bool *b=data; *b=true; return true; }
        case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT: {
            int fmt = *(int*)data;
            if (fmt == RETRO_PIXEL_FORMAT_XRGB8888) { pixel_format = fmt; return true; }
            if (fmt == RETRO_PIXEL_FORMAT_RGB565) { pixel_format = fmt; return true; }
            if (fmt == RETRO_PIXEL_FORMAT_0RGB1555) { pixel_format = fmt; return true; }
            return false;
        }
        case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
        case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY: {
            const char **dir = (const char**)data; *dir = "/tmp"; return true;
        }
        case RETRO_ENVIRONMENT_SET_MEMORY_MAPS: return false;
        case RETRO_ENVIRONMENT_GET_VARIABLE: return false;
        case RETRO_ENVIRONMENT_SET_VARIABLES: return true;
        case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE: { bool *b=data; *b=false; return true; }
        default: return false;
    }
}

static void video_cb(const void *data, unsigned width, unsigned height, size_t pitch) {
    frame_w = width; frame_h = height;
    if (!data) return;
    if (pixel_format == RETRO_PIXEL_FORMAT_XRGB8888) {
        frame_pitch_pixels = pitch / 4;
        size_t sz = width * height * 4;
        frame_buf = realloc(frame_buf, sz);
        const uint32_t *src = (const uint32_t*)data;
        for (unsigned y=0;y<height;y++)
            memcpy(frame_buf + y*width, src + y*frame_pitch_pixels, width*4);
    } else if (pixel_format == RETRO_PIXEL_FORMAT_RGB565) {
        frame_pitch_pixels = pitch / 2;
        size_t sz = width * height * 4;
        frame_buf = realloc(frame_buf, sz);
        const uint16_t *src = (const uint16_t*)data;
        for (unsigned y=0;y<height;y++) {
            for (unsigned x=0;x<width;x++) {
                uint16_t p = src[y*frame_pitch_pixels + x];
                uint32_t r = (p >> 11) & 0x1F; r = (r<<3)|(r>>2);
                uint32_t g = (p >> 5) & 0x3F;  g = (g<<2)|(g>>4);
                uint32_t b = p & 0x1F;         b = (b<<3)|(b>>2);
                frame_buf[y*width+x] = 0xFF000000 | (r<<16) | (g<<8) | b;
            }
        }
    } else { /* 0RGB1555 */
        frame_pitch_pixels = pitch / 2;
        size_t sz = width * height * 4;
        frame_buf = realloc(frame_buf, sz);
        const uint16_t *src = (const uint16_t*)data;
        for (unsigned y=0;y<height;y++) {
            for (unsigned x=0;x<width;x++) {
                uint16_t p = src[y*frame_pitch_pixels + x];
                uint32_t r = (p >> 10) & 0x1F; r = (r<<3)|(r>>2);
                uint32_t g = (p >> 5) & 0x1F;  g = (g<<3)|(g>>2);
                uint32_t b = p & 0x1F;         b = (b<<3)|(b>>2);
                frame_buf[y*width+x] = 0xFF000000 | (r<<16) | (g<<8) | b;
            }
        }
    }
}
static void audio_cb(int16_t l, int16_t r) { (void)l; (void)r; }
static FILE *wav_fp = NULL;
static uint32_t wav_samples = 0;
static uint32_t wav_rate = 44100;
static void wav_write_header(FILE *f, uint32_t rate, uint32_t samples) {
    uint32_t data_bytes = samples * 4;
    uint32_t riff = 36 + data_bytes;
    uint16_t ch=2, bps=16; uint32_t br=rate*4; uint16_t ba=4;
    fseek(f,0,SEEK_SET);
    fwrite("RIFF",1,4,f); fwrite(&riff,4,1,f); fwrite("WAVE",1,4,f);
    fwrite("fmt ",1,4,f); uint32_t fmt=16; fwrite(&fmt,4,1,f);
    uint16_t af=1; fwrite(&af,2,1,f); fwrite(&ch,2,1,f); fwrite(&rate,4,1,f);
    fwrite(&br,4,1,f); fwrite(&ba,2,1,f); fwrite(&bps,2,1,f);
    fwrite("data",1,4,f); fwrite(&data_bytes,4,1,f);
}
static void wav_open(const char *path, uint32_t rate) {
    wav_fp = fopen(path, "wb"); if (!wav_fp) { perror(path); return; }
    wav_rate = rate; wav_samples = 0; wav_write_header(wav_fp, rate, 0);
}
static void wav_push(const int16_t *data, size_t frames) {
    if (!wav_fp) return;
    fwrite(data, sizeof(int16_t), frames*2, wav_fp);
    wav_samples += (uint32_t)frames;
}
static void wav_close(void) {
    if (!wav_fp) return;
    wav_write_header(wav_fp, wav_rate, wav_samples);
    fclose(wav_fp); wav_fp=NULL;
    printf("WAV %u samples\n", wav_samples);
}
static size_t audio_batch_cb(const int16_t *data, size_t frames) { wav_push(data, frames); return frames; }
static void input_poll_cb(void) {}
static int16_t input_state_cb(unsigned port, unsigned device, unsigned index, unsigned id) {
    (void)index;
    if (port != 0 || device != RETRO_DEVICE_JOYPAD) return 0;
    if (id < 16) return input_state[id];
    return 0;
}

static int btn_from_name(const char *s) {
    if (!strcmp(s,"A")) return RETRO_DEVICE_ID_JOYPAD_A;
    if (!strcmp(s,"B")) return RETRO_DEVICE_ID_JOYPAD_B;
    if (!strcmp(s,"SELECT")) return RETRO_DEVICE_ID_JOYPAD_SELECT;
    if (!strcmp(s,"START")) return RETRO_DEVICE_ID_JOYPAD_START;
    if (!strcmp(s,"UP")) return RETRO_DEVICE_ID_JOYPAD_UP;
    if (!strcmp(s,"DOWN")) return RETRO_DEVICE_ID_JOYPAD_DOWN;
    if (!strcmp(s,"LEFT")) return RETRO_DEVICE_ID_JOYPAD_LEFT;
    if (!strcmp(s,"RIGHT")) return RETRO_DEVICE_ID_JOYPAD_RIGHT;
    return -1;
}

static void load_inputs(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) die("cannot open inputs %s", path);
    char line[256];
    while (fgets(line, sizeof(line), f)) {
        if (line[0]=='#' || line[0]=='\n' || line[0]=='\r') continue;
        unsigned frame; char action[16], btn[16];
        if (sscanf(line, "%u,%15[^,],%15s", &frame, action, btn) != 3) continue;
        int b = btn_from_name(btn);
        if (b < 0) continue;
        if (nevents == capevents) { capevents = capevents?capevents*2:128; events = realloc(events, capevents*sizeof(*events)); }
        events[nevents] = (InputEvent){frame, b, !strcmp(action,"down"), nevents};
        nevents++;
    }
    fclose(f);
    qsort(events, nevents, sizeof(*events), compare_events);
}

static int shot_wanted(unsigned f, unsigned *shots, size_t nshots) {
    for (size_t i=0;i<nshots;i++) if (shots[i]==f) return 1;
    return 0;
}

static void save_ppm(const char *path, const uint32_t *buf, unsigned w, unsigned h) {
    FILE *f = fopen(path, "wb");
    if (!f) { perror(path); return; }
    fprintf(f, "P6\n%u %u\n255\n", w, h);
    for (unsigned i=0;i<w*h;i++) {
        uint32_t p = buf[i];
        uint8_t rgb[3] = { (p>>16)&0xFF, (p>>8)&0xFF, p&0xFF };
        fwrite(rgb,1,3,f);
    }
    fclose(f);
    printf("SHOT %u %s\n", current_frame, path);
}

static void save_ram(const char *path) {
    void *data = fn_retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM);
    size_t sz = fn_retro_get_memory_size(RETRO_MEMORY_SYSTEM_RAM);
    if (!data || !sz) return;
    FILE *f = fopen(path, "wb");
    if (!f) return;
    fwrite(data,1,sz,f);
    fclose(f);
    printf("RAM %u %s %zu\n", current_frame, path, sz);
}

/* Private extension of our pinned fceumm build, NOT standard libretro VRAM.
 * See patches/fceumm_capture_layers.patch for layout and mapper handling. */
#define CAPTURE_PPU_MEMORY 0xFCE1
#define CAPTURE_PPU_SIZE 0x31E0
#define CAPTURE_OAM_OFFSET 0x3020
static const unsigned char *get_capture_ppu(void) {
    if (fn_retro_get_memory_size(CAPTURE_PPU_MEMORY) != CAPTURE_PPU_SIZE)
        die("core lacks pinned PPU capture patch");
    const unsigned char *data = fn_retro_get_memory_data(CAPTURE_PPU_MEMORY);
    if (!data) die("PPU capture unavailable");
    return data;
}
static void save_ppu(const char *path) {
    const unsigned char *data = get_capture_ppu();
    FILE *f = fopen(path, "wb");
    if (!f) die("cannot open PPU capture %s", path);
    if (fwrite(data, 1, CAPTURE_PPU_SIZE, f) != CAPTURE_PPU_SIZE || fclose(f))
        die("cannot write PPU capture %s", path);
    printf("PPU %u %s %u\n", current_frame, path, CAPTURE_PPU_SIZE);
}

static void *load_sym(const char *name) {
    void *s = dlsym(core, name);
    if (!s) die("missing symbol %s", name);
    return s;
}

int main(int argc, char **argv) {
    const char *core_path=NULL,*rom_path=NULL,*out_dir="/tmp/nes_frames";
    const char *inputs_path=NULL,*ram_dir=NULL,*ppu_dir=NULL,*wav_path=NULL;
    const char *ram_trace_path=NULL,*oam_trace_path=NULL,*audio_index_path=NULL;
    const char *load_state_path=NULL,*save_state_path=NULL;
    unsigned save_state_frame=0;
    unsigned start_frame=0, ram_trace_start=0, oam_trace_start=0;
    const char *cheats[64]; size_t ncheats=0;
    unsigned total=1200;
    unsigned shots[4096]; size_t nshots=0;
    unsigned shot_every=0, shot_start=0;
    unsigned ppu_every=0, ppu_start=0;
    for (int i=1;i<argc;i++) {
        if (!strcmp(argv[i],"--core") && i+1<argc) core_path=argv[++i];
        else if (!strcmp(argv[i],"--rom") && i+1<argc) rom_path=argv[++i];
        else if (!strcmp(argv[i],"--out") && i+1<argc) out_dir=argv[++i];
        else if (!strcmp(argv[i],"--frames") && i+1<argc) total=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--inputs") && i+1<argc) inputs_path=argv[++i];
        else if (!strcmp(argv[i],"--ram-dir") && i+1<argc) ram_dir=argv[++i];
        else if (!strcmp(argv[i],"--ppu-dir") && i+1<argc) ppu_dir=argv[++i];
        else if (!strcmp(argv[i],"--ram-trace") && i+1<argc) ram_trace_path=argv[++i];
        else if (!strcmp(argv[i],"--ram-trace-start") && i+1<argc) ram_trace_start=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--oam-trace") && i+1<argc) oam_trace_path=argv[++i];
        else if (!strcmp(argv[i],"--oam-trace-start") && i+1<argc) oam_trace_start=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--wav") && i+1<argc) wav_path=argv[++i];
        else if (!strcmp(argv[i],"--audio-index") && i+1<argc) audio_index_path=argv[++i];
        else if (!strcmp(argv[i],"--shot-every") && i+1<argc) shot_every=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--shot-start") && i+1<argc) shot_start=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--ppu-every") && i+1<argc) ppu_every=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--ppu-start") && i+1<argc) ppu_start=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--cheat") && i+1<argc && ncheats<64) cheats[ncheats++]=argv[++i];
        else if (!strcmp(argv[i],"--load-state") && i+1<argc) load_state_path=argv[++i];
        else if (!strcmp(argv[i],"--save-state") && i+1<argc) save_state_path=argv[++i];
        else if (!strcmp(argv[i],"--save-state-frame") && i+1<argc) save_state_frame=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--start-frame") && i+1<argc) start_frame=atoi(argv[++i]);
        else if (!strcmp(argv[i],"--shots") && i+1<argc) {
            char *s=strdup(argv[++i]), *tok=strtok(s,",");
            while(tok && nshots<4096){ shots[nshots++]=atoi(tok); tok=strtok(NULL,","); }
            free(s);
        }
    }
    if (!core_path || !rom_path) die("usage: %s --core fceumm.so --rom game.nes [--frames N] [--shots 1,2] [--inputs i.csv] [--out dir] [--ram-dir dir]", argv[0]);
    if (ppu_every && !ppu_dir) die("--ppu-every requires --ppu-dir");
    if (audio_index_path && !wav_path) die("--audio-index requires --wav");
    ensure_dir(out_dir);
    if (ram_dir) ensure_dir(ram_dir);
    if (ppu_dir) ensure_dir(ppu_dir);
    if (inputs_path) load_inputs(inputs_path);

    core = dlopen(core_path, RTLD_NOW);
    if (!core) die("dlopen: %s", dlerror());
    fn_retro_init = load_sym("retro_init");
    fn_retro_deinit = load_sym("retro_deinit");
    fn_retro_set_environment = load_sym("retro_set_environment");
    fn_retro_set_video_refresh = load_sym("retro_set_video_refresh");
    fn_retro_set_audio_sample = load_sym("retro_set_audio_sample");
    fn_retro_set_audio_sample_batch = load_sym("retro_set_audio_sample_batch");
    fn_retro_set_input_poll = load_sym("retro_set_input_poll");
    fn_retro_set_input_state = load_sym("retro_set_input_state");
    fn_retro_load_game = load_sym("retro_load_game");
    fn_retro_unload_game = load_sym("retro_unload_game");
    fn_retro_run = load_sym("retro_run");
    fn_retro_get_system_av_info = load_sym("retro_get_system_av_info");
    fn_retro_get_memory_data = load_sym("retro_get_memory_data");
    fn_retro_get_memory_size = load_sym("retro_get_memory_size");
    fn_retro_cheat_reset = dlsym(core, "retro_cheat_reset");
    fn_retro_cheat_set = dlsym(core, "retro_cheat_set");
    fn_retro_serialize_size = dlsym(core, "retro_serialize_size");
    fn_retro_serialize = dlsym(core, "retro_serialize");
    fn_retro_unserialize = dlsym(core, "retro_unserialize");

    fn_retro_set_environment(env_cb);
    fn_retro_set_video_refresh(video_cb);
    fn_retro_set_audio_sample(audio_cb);
    fn_retro_set_audio_sample_batch(audio_batch_cb);
    fn_retro_set_input_poll(input_poll_cb);
    fn_retro_set_input_state(input_state_cb);
    fn_retro_init();

    FILE *rf = fopen(rom_path, "rb");
    if (!rf) die("cannot open rom");
    fseek(rf,0,SEEK_END); long rsz=ftell(rf); fseek(rf,0,SEEK_SET);
    void *rom=malloc(rsz); fread(rom,1,rsz,rf); fclose(rf);
    struct retro_game_info gi = { rom_path, rom, (size_t)rsz, NULL };
    if (!fn_retro_load_game(&gi)) die("retro_load_game failed");
    if (fn_retro_cheat_reset) fn_retro_cheat_reset();
    for (size_t ci=0; ci<ncheats; ci++) {
        if (fn_retro_cheat_set) { fn_retro_cheat_set((unsigned)ci, true, cheats[ci]); printf("CHEAT %s\n", cheats[ci]); }
        else printf("CHEAT unsupported\n");
    }
    fn_retro_get_system_av_info(&av);
    if (wav_path) wav_open(wav_path, (uint32_t)av.timing.sample_rate);
    FILE *audio_index = NULL;
    if (audio_index_path) {
        audio_index = fopen(audio_index_path, "wb");
        if (!audio_index) die("cannot open audio index %s", audio_index_path);
        /* AFI1, first absolute emulator frame, WAV sample rate, then one
         * little-endian uint64 cumulative stereo-sample count after each
         * retro_run(). Boundary 0 is implicit before the first frame. */
        uint32_t header[2] = {start_frame + 1, wav_rate};
        if (fwrite("AFI1", 1, 4, audio_index) != 4 ||
            fwrite(header, sizeof(header), 1, audio_index) != 1)
            die("cannot write audio index header");
    }
    if (load_state_path && fn_retro_unserialize) {
        FILE *sf = fopen(load_state_path, "rb");
        if (!sf) die("cannot open state %s", load_state_path);
        fseek(sf,0,SEEK_END); long ssz=ftell(sf); fseek(sf,0,SEEK_SET);
        void *sbuf=malloc(ssz); fread(sbuf,1,ssz,sf); fclose(sf);
        if (!fn_retro_unserialize(sbuf,(size_t)ssz)) die("unserialize failed %s", load_state_path);
        free(sbuf);
        printf("LOAD_STATE %s\n", load_state_path);
    }

    FILE *ram_trace = NULL;
    size_t ram_trace_size = 0;
    if (ram_trace_path) {
        ram_trace_size = fn_retro_get_memory_size(RETRO_MEMORY_SYSTEM_RAM);
        if (!ram_trace_size || ram_trace_size > UINT32_MAX)
            die("invalid system RAM size for trace");
        ram_trace = fopen(ram_trace_path, "wb");
        if (!ram_trace) die("cannot open RAM trace %s", ram_trace_path);
        /* RRT1, first frame (inclusive), RAM bytes per frame; little-endian. */
        if (ram_trace_start <= start_frame) ram_trace_start = start_frame + 1;
        uint32_t header[2] = {ram_trace_start, (uint32_t)ram_trace_size};
        fwrite("RRT1", 1, 4, ram_trace);
        fwrite(header, sizeof(header), 1, ram_trace);
    }

    FILE *oam_trace = NULL;
    if (oam_trace_path) {
        oam_trace = fopen(oam_trace_path, "wb");
        if (!oam_trace) die("cannot open OAM trace %s", oam_trace_path);
        if (oam_trace_start <= start_frame) oam_trace_start = start_frame + 1;
        uint32_t header[2] = {oam_trace_start, 0x100};
        fwrite("OAT1", 1, 4, oam_trace);
        fwrite(header, sizeof(header), 1, oam_trace);
    }

    size_t ie = 0;
    while (ie < nevents && events[ie].frame <= start_frame) {
        input_state[events[ie].btn] = events[ie].down ? 1 : 0;
        ie++;
    }
    for (unsigned f=start_frame+1; f<=total; f++) {
        current_frame = f;
        while (ie < nevents && events[ie].frame == f) {
            input_state[events[ie].btn] = events[ie].down ? 1 : 0;
            ie++;
        }
        fn_retro_run();
        if (audio_index) {
            uint64_t samples_after_frame = wav_samples;
            if (fwrite(&samples_after_frame, sizeof(samples_after_frame), 1, audio_index) != 1)
                die("audio index write failed at frame %u", f);
        }
        if (ram_trace && f >= ram_trace_start) {
            const void *ram = fn_retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM);
            if (!ram || fwrite(ram, 1, ram_trace_size, ram_trace) != ram_trace_size)
                die("RAM trace write failed at frame %u", f);
        }
        if (oam_trace && f >= oam_trace_start) {
            const unsigned char *ppu = get_capture_ppu();
            if (fwrite(ppu + CAPTURE_OAM_OFFSET, 1, 0x100, oam_trace) != 0x100)
                die("OAM trace write failed at frame %u", f);
        }
        int take = (nshots && shot_wanted(f, shots, nshots));
        if (!take && shot_every && f >= shot_start && ((f-shot_start)%shot_every)==0) take=1;
        if (take && frame_buf) {
            char p[512]; snprintf(p,sizeof(p),"%s/frame_%05u.ppm",out_dir,f);
            save_ppm(p, frame_buf, frame_w, frame_h);
        }
        int ppu_take = ppu_every && f >= ppu_start && (f-ppu_start)%ppu_every == 0;
        if (ppu_dir && (take || ppu_take)) {
            char pp[512]; snprintf(pp,sizeof(pp),"%s/ppu_%05u.bin",ppu_dir,f);
            save_ppu(pp);
        }
        if (ram_dir && (take || ppu_take)) {
            char rp[512]; snprintf(rp,sizeof(rp),"%s/ram_%05u.bin",ram_dir,f);
            save_ram(rp);
        }
        if (save_state_path && fn_retro_serialize && save_state_frame && f == save_state_frame) {
            size_t ssz = fn_retro_serialize_size();
            void *sbuf = malloc(ssz);
            if (fn_retro_serialize(sbuf, ssz)) {
                FILE *sf = fopen(save_state_path, "wb");
                if (sf) { fwrite(sbuf,1,ssz,sf); fclose(sf); printf("SAVE_STATE %u %s\n", f, save_state_path); }
            }
            free(sbuf);
        }
    }
    if (save_state_path && fn_retro_serialize && !save_state_frame) {
        size_t ssz = fn_retro_serialize_size();
        void *sbuf = malloc(ssz);
        if (fn_retro_serialize(sbuf, ssz)) {
            FILE *sf = fopen(save_state_path, "wb");
            if (sf) { fwrite(sbuf,1,ssz,sf); fclose(sf); printf("SAVE_STATE %u %s\n", total, save_state_path); }
        }
        free(sbuf);
    }
    if (ram_trace) {
        if (fclose(ram_trace)) die("RAM trace close failed");
        printf("RAM_TRACE %u..%u %u bytes/frame %s\n",
               ram_trace_start, total, (unsigned)ram_trace_size, ram_trace_path);
    }
    if (oam_trace) {
        if (fclose(oam_trace)) die("OAM trace close failed");
        printf("OAM_TRACE %u..%u 256 bytes/frame %s\n",
               oam_trace_start, total, oam_trace_path);
    }
    if (audio_index) {
        if (fclose(audio_index)) die("audio index close failed");
        printf("AUDIO_INDEX %u..%u %u stereo samples %s\n",
               start_frame + 1, total, wav_samples, audio_index_path);
    }
    fn_retro_unload_game();
    fn_retro_deinit();
    wav_close();
    free(rom);
    printf("DONE %u\n", total);
    return 0;
}
