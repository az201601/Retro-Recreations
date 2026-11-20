/*
 * libretro_host.c - minimal, deterministic, headless libretro frontend.
 *
 * Purpose: drive a libretro NES core (Nestopia, FCEUX-mm, ...) from the
 * command line so that a reference ("oracle") capture of a real ROM can be
 * produced: per-frame PNG screenshots, a WAV of the APU output, frame
 * hashes, and per-frame RAM watches.  Everything is driven by an explicit
 * frame counter, so runs are exactly reproducible - no wall clock, no
 * vsync, no audio device.
 *
 * Build: see build.sh (needs libdl only).
 *
 * Usage: nesrun --core CORE.so --rom ROM.nes [options]
 *
 *   --frames N              run N frames (default 600)
 *
 *   --dir DIR               output directory for PNGs
 *   --png LIST              frames to dump as PNG: "0,120,200-260,1000"
 *                           (implies --dir DIR, default ./frames)
 *   --png-every K           dump every K-th frame (starting at --png-from)
 *   --png-from N            first frame for --png-every (default 0)
 *   --scale S               nearest-neighbour upscale for PNGs (default 1)
 *   --crop X,Y,W,H          crop PNGs to that rect of the frame
 *
 *   --wav FILE              write all APU output as 16-bit stereo WAV
 *   --hash FILE             write "frame <fnv64hash>" for every frame
 *
 *   --var KEY=VALUE         set a core option (repeatable)
 *   --var-file FILE         read "KEY=VALUE" lines (core options)
 *
 *   --input FILE            frame -> buttons script; lines:
 *                             "FRAME BUTTONS"        hold for 1 frame
 *                             "FROM-TO BUTTONS"      hold for a range
 *                             "#" comment
 *                           BUTTONS from U D L R A B S T (S=select,T=start),
 *                           "-" or "" = nothing.  Vectors: UDLRABST string.
 *
 *   --watch NAME:OFF:LEN    hex-dump LEN bytes at OFF of memory region NAME
 *                           every frame, one line per frame: "F <hex bytes>"
 *   --watch-out FILE        where watches go (default stdout)
 *   --mem-list              print available memory region names and exit
 *
 *   --save-state FRAME:FILE save a serialized state at FRAME
 *   --load-state FILE       load a serialized state right after load_game
 *
 *   --sysdir DIR            "system directory" handed to the core
 *   --probe                 print core/system info and exit
 *   --quiet                 no progress on stderr
 *
 * Frame numbering starts at 0 for the first retro_run() call.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdarg.h>
#include <dlfcn.h>
#include <sys/stat.h>

#include "libretro.h"

/* ------------------------------------------------------------------ */
/* Core entry points                                                   */
/* ------------------------------------------------------------------ */

static void (*p_retro_init)(void);
static void (*p_retro_deinit)(void);
static unsigned (*p_retro_api_version)(void);
static void (*p_retro_get_system_info)(struct retro_system_info *);
static void (*p_retro_get_system_av_info)(struct retro_system_av_info *);
static void (*p_retro_set_environment)(retro_environment_t);
static void (*p_retro_set_video_refresh)(retro_video_refresh_t);
static void (*p_retro_set_audio_sample)(retro_audio_sample_t);
static void (*p_retro_set_audio_sample_batch)(retro_audio_sample_batch_t);
static void (*p_retro_set_input_poll)(retro_input_poll_t);
static void (*p_retro_set_input_state)(retro_input_state_t);
static void (*p_retro_set_controller_port_device)(unsigned, unsigned);
static void (*p_retro_reset)(void);
static void (*p_retro_run)(void);
static size_t (*p_retro_serialize_size)(void);
static bool (*p_retro_serialize)(void *, size_t);
static bool (*p_retro_unserialize)(const void *, size_t);
static bool (*p_retro_load_game)(const struct retro_game_info *);
static void (*p_retro_unload_game)(void);

/* ------------------------------------------------------------------ */
/* Options                                                             */
/* ------------------------------------------------------------------ */

#define MAX_VARS 128
static struct { char key[128]; char val[256]; } vars[MAX_VARS];
static int var_count = 0;

static const char *var_lookup(const char *key)
{
   for (int i = 0; i < var_count; i++)
      if (!strcmp(vars[i].key, key))
         return vars[i].val;
   return NULL;
}

static void var_set(const char *kv)
{
   const char *eq = strchr(kv, '=');
   if (!eq || var_count >= MAX_VARS) {
      fprintf(stderr, "nesrun: bad --var '%s' (want KEY=VALUE)\n", kv);
      exit(2);
   }
   size_t n = (size_t)(eq - kv);
   if (n >= sizeof(vars[0].key)) n = sizeof(vars[0].key) - 1;
   memcpy(vars[var_count].key, kv, n);
   vars[var_count].key[n] = 0;
   snprintf(vars[var_count].val, sizeof(vars[0].val), "%s", eq + 1);
   var_count++;
}

/* ------------------------------------------------------------------ */
/* Logging                                                             */
/* ------------------------------------------------------------------ */

static bool quiet = false;

static void core_log(enum retro_log_level level, const char *fmt, ...)
{
   if (quiet || level == RETRO_LOG_DEBUG) return;
   va_list ap;
   va_start(ap, fmt);
   fprintf(stderr, "[core] ");
   vfprintf(stderr, fmt, ap);
   va_end(ap);
}

/* ------------------------------------------------------------------ */
/* Memory maps (for --watch / --mem-list)                              */
/* ------------------------------------------------------------------ */

static struct retro_memory_map memmap;
static bool have_memmap = false;

/* ------------------------------------------------------------------ */
/* Video                                                               */
/* ------------------------------------------------------------------ */

static const uint32_t *frame_px  = NULL;
static unsigned frame_w = 0, frame_h = 0;
static size_t   frame_pitch_px = 0;
static bool     frame_dupe = false;

/* ------------------------------------------------------------------ */
/* Audio: streamed WAV writer                                          */
/* ------------------------------------------------------------------ */

static FILE   *wav_fp = NULL;
static uint32_t wav_frames = 0;

static void wav_open(const char *path)
{
   wav_fp = fopen(path, "wb");
   if (!wav_fp) { perror(path); exit(2); }
   unsigned char hdr[44] = {0};
   memcpy(hdr, "RIFF", 4);
   memcpy(hdr + 8, "WAVEfmt ", 8);
   hdr[16] = 16;                     /* fmt chunk size */
   hdr[20] = 1;                      /* PCM */
   hdr[22] = 2;                      /* channels */
   uint32_t rate = 48000, byterate = 48000 * 4;
   uint16_t align = 4, bits = 16;
   memcpy(hdr + 24, &rate, 4);
   memcpy(hdr + 28, &byterate, 4);
   memcpy(hdr + 32, &align, 2);
   memcpy(hdr + 34, &bits, 2);
   memcpy(hdr + 36, "data", 4);
   fwrite(hdr, 1, 44, wav_fp);
}

static void wav_close(void)
{
   if (!wav_fp) return;
   uint32_t datasz = wav_frames * 4;
   uint32_t riffsz = datasz + 36;
   fseek(wav_fp, 4, SEEK_SET);   fwrite(&riffsz, 4, 1, wav_fp);
   fseek(wav_fp, 40, SEEK_SET);  fwrite(&datasz, 4, 1, wav_fp);
   fclose(wav_fp);
   wav_fp = NULL;
}

static size_t audio_batch(const int16_t *data, size_t frames)
{
   if (wav_fp && frames) {
      fwrite(data, sizeof(int16_t) * 2, frames, wav_fp);
      wav_frames += (uint32_t)frames;
   }
   return frames;
}

static void audio_sample(int16_t l, int16_t r)
{
   int16_t pair[2] = { l, r };
   audio_batch(pair, 1);
}

/* ------------------------------------------------------------------ */
/* PNG writer (stored-deflate; no external zlib needed)                */
/* ------------------------------------------------------------------ */

static uint32_t crc_table[256];
static void crc_init(void)
{
   for (uint32_t n = 0; n < 256; n++) {
      uint32_t c = n;
      for (int k = 0; k < 8; k++)
         c = (c & 1) ? 0xEDB88320u ^ (c >> 1) : (c >> 1);
      crc_table[n] = c;
   }
}

static uint32_t crc_upd(uint32_t crc, const void *buf, size_t len)
{
   const unsigned char *p = buf;
   for (size_t i = 0; i < len; i++)
      crc = crc_table[(crc ^ p[i]) & 0xff] ^ (crc >> 8);
   return crc;
}

static uint32_t adler32(const void *buf, size_t len)
{
   const unsigned char *p = buf;
   uint32_t a = 1, b = 0;
   while (len) {
      size_t n = len > 5552 ? 5552 : len;
      len -= n;
      while (n--) { a += *p++; b += a; }
      a %= 65521; b %= 65521;
   }
   return (b << 16) | a;
}

static void be32(unsigned char *p, uint32_t v)
{
   p[0] = (unsigned char)(v >> 24); p[1] = (unsigned char)(v >> 16);
   p[2] = (unsigned char)(v >> 8);  p[3] = (unsigned char)v;
}

static void png_chunk(FILE *f, const char *tag, const void *data, uint32_t len)
{
   unsigned char hdr[8];
   be32(hdr, len);
   memcpy(hdr + 4, tag, 4);
   fwrite(hdr, 1, 8, f);
   if (len) fwrite(data, 1, len, f);
   uint32_t crc = crc_upd(0xffffffffu, tag, 4);
   crc = crc_upd(crc, data, len) ^ 0xffffffffu;
   unsigned char c[4];
   be32(c, crc);
   fwrite(c, 1, 4, f);
}

/* Write an 8-bit RGB PNG from raw RGB rows (row-major, tightly packed). */
static int write_png(const char *path, const unsigned char *rgb, int w, int h)
{
   FILE *f = fopen(path, "wb");
   if (!f) { perror(path); return 0; }

   static const unsigned char sig[8] = { 0x89, 'P', 'N', 'G', 0x0d, 0x0a, 0x1a, 0x0a };
   fwrite(sig, 1, 8, f);

   unsigned char ihdr[13];
   be32(ihdr, (uint32_t)w);
   be32(ihdr + 4, (uint32_t)h);
   ihdr[8] = 8;   /* bit depth */
   ihdr[9] = 2;   /* colour type: truecolour */
   ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
   png_chunk(f, "IHDR", ihdr, 13);

   /* Raw scanlines with filter byte 0, wrapped in a zlib stream that uses
    * stored (uncompressed) deflate blocks. */
   size_t rowbytes = (size_t)w * 3 + 1;
   size_t rawlen   = rowbytes * (size_t)h;
   unsigned char *raw = malloc(rawlen);
   if (!raw) { fclose(f); return 0; }
   for (int y = 0; y < h; y++) {
      raw[y * rowbytes] = 0;
      memcpy(raw + y * rowbytes + 1, rgb + (size_t)y * w * 3, (size_t)w * 3);
   }

   uint32_t rawlen32 = (uint32_t)rawlen;
   size_t zlen = 2 + 5 * ((rawlen + 65534) / 65535) + rawlen + 4;
   unsigned char *z = malloc(zlen);
   if (!z) { free(raw); fclose(f); return 0; }
   size_t zp = 0;
   z[zp++] = 0x78; z[zp++] = 0x01;               /* zlib header, no dict */
   size_t off = 0;
   while (off < rawlen) {
      size_t n = rawlen - off; if (n > 65535) n = 65535;
      bool last = (off + n == rawlen);
      z[zp++] = last ? 1 : 0;                    /* BFINAL, BTYPE=00 */
      z[zp++] = (unsigned char)(n & 0xff);
      z[zp++] = (unsigned char)(n >> 8);
      z[zp++] = (unsigned char)(~n & 0xff);
      z[zp++] = (unsigned char)((~n >> 8) & 0xff);
      memcpy(z + zp, raw + off, n);
      zp += n; off += n;
   }
   be32(z + zp, adler32(raw, rawlen)); zp += 4;
   (void)rawlen32;
   png_chunk(f, "IDAT", z, (uint32_t)zp);
   png_chunk(f, "IEND", NULL, 0);

   free(z); free(raw); fclose(f);
   return 1;
}

/* ------------------------------------------------------------------ */
/* Frame dumping                                                       */
/* ------------------------------------------------------------------ */

/* mkdir -p, so callers never have to pre-create the output directory. */
static void ensure_dir(const char *path)
{
   char tmp[512];
   snprintf(tmp, sizeof(tmp), "%s", path);
   for (char *q = tmp + 1; *q; q++) {
      if (*q != '/') continue;
      *q = 0;
      mkdir(tmp, 0777);
      *q = '/';
   }
   mkdir(tmp, 0777);
}

static char  out_dir[512] = "frames";
static int   png_scale = 1;
static int   crop_x = 0, crop_y = 0, crop_w = 0, crop_h = 0;
static char  png_ranges[8192] = "";   /* "0,120,200-260" */
static int   png_every = 0, png_from = 0;
static FILE *hash_fp = NULL;
static int   dumped = 0;

static bool in_png_ranges(long frame)
{
   const char *p = png_ranges;
   while (*p) {
      char *end;
      long a = strtol(p, &end, 10);
      if (end == p) { p++; continue; }
      long b = a;
      if (*end == '-') { p = end + 1; b = strtol(p, &end, 10); }
      else p = end;
      if (frame >= a && frame <= b) return true;
      while (*end == ',' || *end == ' ') end++;
      p = end;
   }
   return false;
}

static void dump_frame(long frame)
{
   if (!frame_px || frame_dupe) return;
   int w = (int)frame_w, h = (int)frame_h;
   int cx = crop_w ? crop_x : 0, cy = crop_h ? crop_y : 0;
   int cw = crop_w ? crop_w : w, ch = crop_h ? crop_h : h;
   if (cx + cw > w) cw = w - cx;
   if (cy + ch > h) ch = h - cy;
   if (cw <= 0 || ch <= 0) return;

   int ow = cw * png_scale, oh = ch * png_scale;
   unsigned char *rgb = malloc((size_t)ow * oh * 3);
   if (!rgb) return;
   for (int y = 0; y < ch; y++) {
      const uint32_t *src = frame_px + (size_t)(y + cy) * frame_pitch_px + cx;
      for (int x = 0; x < cw; x++) {
         uint32_t px = src[x];
         unsigned char r = (unsigned char)((px >> 16) & 0xff);
         unsigned char g = (unsigned char)((px >> 8) & 0xff);
         unsigned char b = (unsigned char)(px & 0xff);
         for (int sy = 0; sy < png_scale; sy++) {
            unsigned char *dst = rgb + ((size_t)(y * png_scale + sy) * ow + (size_t)x * png_scale) * 3;
            for (int sx = 0; sx < png_scale; sx++) {
               dst[sx * 3 + 0] = r; dst[sx * 3 + 1] = g; dst[sx * 3 + 2] = b;
            }
         }
      }
   }
   char path[600];
   snprintf(path, sizeof(path), "%s/f%06ld.png", out_dir, frame);
   write_png(path, rgb, ow, oh);
   free(rgb);
   dumped++;
}

static void hash_frame(long frame)
{
   if (!hash_fp || !frame_px || frame_dupe) return;
   uint64_t h = 1469598103934665603ull;
   for (unsigned y = 0; y < frame_h; y++) {
      const uint32_t *row = frame_px + (size_t)y * frame_pitch_px;
      for (unsigned x = 0; x < frame_w; x++) {
         h ^= row[x] & 0x00ffffffu;
         h *= 1099511628211ull;
      }
   }
   fprintf(hash_fp, "%ld %016llx\n", frame, (unsigned long long)h);
}

/* ------------------------------------------------------------------ */
/* Input script                                                        */
/* ------------------------------------------------------------------ */

#define MAX_INPUTS 4096
static struct { long from, to; unsigned mask; } inputs[MAX_INPUTS];
static int input_count = 0;

static unsigned parse_buttons(const char *s)
{
   unsigned m = 0;
   for (; *s; s++) {
      switch (*s) {
         case 'U': m |= 1u << RETRO_DEVICE_ID_JOYPAD_UP;     break;
         case 'D': m |= 1u << RETRO_DEVICE_ID_JOYPAD_DOWN;   break;
         case 'L': m |= 1u << RETRO_DEVICE_ID_JOYPAD_LEFT;   break;
         case 'R': m |= 1u << RETRO_DEVICE_ID_JOYPAD_RIGHT;  break;
         case 'A': m |= 1u << RETRO_DEVICE_ID_JOYPAD_A;      break;
         case 'B': m |= 1u << RETRO_DEVICE_ID_JOYPAD_B;      break;
         case 'S': m |= 1u << RETRO_DEVICE_ID_JOYPAD_SELECT; break;
         case 'T': m |= 1u << RETRO_DEVICE_ID_JOYPAD_START;  break;
         case '-': case ' ': case '.': break;
         default:
            fprintf(stderr, "nesrun: unknown button '%c'\n", *s);
            exit(2);
      }
   }
   return m;
}

static void load_inputs(const char *path)
{
   FILE *f = fopen(path, "r");
   if (!f) { perror(path); exit(2); }
   char line[512];
   while (fgets(line, sizeof(line), f)) {
      char *p = line;
      while (*p == ' ' || *p == '\t') p++;
      if (*p == '#' || *p == '\n' || *p == 0) continue;
      long a = strtol(p, &p, 10), b = a;
      if (*p == '-') { p++; b = strtol(p, &p, 10); }
      while (*p == ' ' || *p == '\t' || *p == ':') p++;
      char *nl = strpbrk(p, "\r\n");
      if (nl) *nl = 0;
      if (input_count >= MAX_INPUTS) break;
      inputs[input_count].from = a;
      inputs[input_count].to   = b;
      inputs[input_count].mask = parse_buttons(p);
      input_count++;
   }
   fclose(f);
}

static unsigned input_for_frame(long frame)
{
   unsigned m = 0;
   for (int i = 0; i < input_count; i++)
      if (frame >= inputs[i].from && frame <= inputs[i].to)
         m |= inputs[i].mask;
   return m;
}

/* ------------------------------------------------------------------ */
/* Watches                                                             */
/* ------------------------------------------------------------------ */

#define MAX_WATCH 16
static struct { char region[64]; unsigned off, len; } watch[MAX_WATCH];
static int watch_count = 0;
static FILE *watch_fp = NULL;

static void add_watch(const char *spec)
{
   /* NAME:OFF:LEN, OFF accepts 0x..  NAME "CPU" = a 6502 address. */
   char name[64] = {0};
   const char *p = spec;
   size_t i = 0;
   while (*p && *p != ':' && i < sizeof(name) - 1) name[i++] = *p++;
   name[i] = 0;
   if (*p != ':') { fprintf(stderr, "nesrun: bad --watch '%s'\n", spec); exit(2); }
   p++;
   char *end;
   unsigned long off = strtoul(p, &end, 0);
   p = (*end == ':') ? end + 1 : end;
   unsigned long len = strtoul(p, NULL, 0);
   if (watch_count >= MAX_WATCH) return;
   snprintf(watch[watch_count].region, sizeof(watch[0].region), "%s", name);
   watch[watch_count].off = (unsigned)off;
   watch[watch_count].len = (unsigned)len;
   watch_count++;
}

/* One byte at a 6502 address, honouring whatever descriptors the core
 * published (Nestopia publishes RAM 4x, FCEUmm as eight 1k chunks). */
static const unsigned char *mem_byte_cpu(unsigned addr)
{
   for (unsigned i = 0; i < memmap.num_descriptors; i++) {
      const struct retro_memory_descriptor *d = &memmap.descriptors[i];
      const char *dn = d->addrspace ? d->addrspace : "";
      size_t dlen = d->len & 0x00ffffffu;
      if (*dn) continue;
      if (addr >= d->start && (size_t)addr < d->start + dlen)
         return (const unsigned char *)d->ptr + d->offset + (addr - d->start);
   }
   return NULL;
}

/* One byte `off` bytes into a named address space ("PPUCHR", "PPUPAL",
 * "NTARAM", ...).  With no name match, "CPU" style lookup is assumed. */
static const unsigned char *mem_byte_region(const char *space, unsigned off)
{
   if (!strcmp(space, "CPU"))
      return mem_byte_cpu(off);
   for (unsigned i = 0; i < memmap.num_descriptors; i++) {
      const struct retro_memory_descriptor *d = &memmap.descriptors[i];
      const char *dn = d->addrspace ? d->addrspace : "";
      size_t dlen = d->len & 0x00ffffffu;
      if (strcmp(dn, space)) continue;
      if (off < dlen)
         return (const unsigned char *)d->ptr + d->offset + off;
   }
   return NULL;
}

/* ------------------------------------------------------------------ */
/* Environment callback                                                */
/* ------------------------------------------------------------------ */

static struct retro_game_geometry geom = { 256, 240, 256, 240, 0.0f };
static char sysdir[512] = ".";
static char savedir[512] = ".";

static bool environ_cb(unsigned cmd, void *data)
{
   switch (cmd) {
      case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT: {
         enum retro_pixel_format *fmt = data;
         return *fmt == RETRO_PIXEL_FORMAT_XRGB8888 || *fmt == RETRO_PIXEL_FORMAT_0RGB1555;
      }
      case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
         *(const char **)data = sysdir;
         return true;
      case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY:
         *(const char **)data = savedir;
         return true;
      case RETRO_ENVIRONMENT_GET_VARIABLE: {
         struct retro_variable *v = data;
         const char *val = var_lookup(v->key);
         v->value = val;              /* NULL => core keeps its own default */
         return val != NULL;
      }
      case RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:
         *(bool *)data = false;
         return true;
      case RETRO_ENVIRONMENT_GET_LOG_INTERFACE: {
         struct retro_log_callback *cb = data;
         cb->log = core_log;
         return true;
      }
      case RETRO_ENVIRONMENT_GET_INPUT_BITMASKS:
         return true;
      case RETRO_ENVIRONMENT_GET_MESSAGE_INTERFACE_VERSION:
         *(unsigned *)data = 1;
         return true;
      case RETRO_ENVIRONMENT_GET_CAN_DUPE:
         *(bool *)data = true;
         return true;
      case RETRO_ENVIRONMENT_SET_MEMORY_MAPS: {
         /* num_descriptors is a plain count; the CONST flag lives in each
          * descriptor's len field, so nothing to strip here. */
         memmap = *(struct retro_memory_map *)data;
         have_memmap = true;
         return true;
      }
      case RETRO_ENVIRONMENT_SET_GEOMETRY: {
         struct retro_game_geometry *g = data;
         geom = *g;
         return true;
      }
      case RETRO_ENVIRONMENT_SET_PERFORMANCE_LEVEL:
      case RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS:
      case RETRO_ENVIRONMENT_SET_CONTROLLER_INFO:
      case RETRO_ENVIRONMENT_SET_CORE_OPTIONS:
      case RETRO_ENVIRONMENT_SET_CORE_OPTIONS_INTL:
      case RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2:
      case RETRO_ENVIRONMENT_SET_CORE_OPTIONS_V2_INTL:
      case RETRO_ENVIRONMENT_SET_CORE_OPTIONS_UPDATE_DISPLAY_CALLBACK:
      case RETRO_ENVIRONMENT_SET_CORE_OPTIONS_DISPLAY:
      case RETRO_ENVIRONMENT_SET_MESSAGE:
      case RETRO_ENVIRONMENT_SET_MESSAGE_EXT:
      case RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME:
      case RETRO_ENVIRONMENT_SET_AUDIO_BUFFER_STATUS_CALLBACK:
      case RETRO_ENVIRONMENT_SET_MINIMUM_AUDIO_LATENCY:
      case RETRO_ENVIRONMENT_SET_SERIALIZATION_QUIRKS:
         return true;
      case RETRO_ENVIRONMENT_GET_VFS_INTERFACE:
         return false;
      case RETRO_ENVIRONMENT_GET_AUDIO_VIDEO_ENABLE: {
         int *v = data; *v = 3; return true;
      }
      default:
         return false;
   }
}

/* ------------------------------------------------------------------ */
/* Callbacks                                                           */
/* ------------------------------------------------------------------ */

static void video_cb(const void *data, unsigned w, unsigned h, size_t pitch)
{
   if (!data) { frame_dupe = true; return; }
   frame_dupe = false;
   frame_px = data;
   frame_w = w; frame_h = h;
   frame_pitch_px = pitch / sizeof(uint32_t);
}

static unsigned pad_state = 0;

static void input_poll_cb(void) { }

static int16_t input_state_cb(unsigned port, unsigned device, unsigned index,
                              unsigned id)
{
   if (port != 0 || device != RETRO_DEVICE_JOYPAD) return 0;
   if (id == RETRO_DEVICE_ID_JOYPAD_MASK) return (int16_t)pad_state;
   if (id > RETRO_DEVICE_ID_JOYPAD_R3) return 0;
   return (pad_state >> id) & 1 ? 1 : 0;
}

/* ------------------------------------------------------------------ */
/* main                                                                */
/* ------------------------------------------------------------------ */

static void *sym(void *h, const char *name, bool required)
{
   void *s = dlsym(h, name);
   if (!s && required) {
      fprintf(stderr, "nesrun: missing symbol %s\n", name);
      exit(2);
   }
   return s;
}

#define BIND(h, fn, required) p_##fn = sym(h, #fn, required)

static void list_memories(void)
{
   for (unsigned i = 0; i < memmap.num_descriptors; i++) {
      const struct retro_memory_descriptor *d = &memmap.descriptors[i];
      printf("%s\tsize=%zu\tselect=%#zx\tstart=%#zx\n",
             d->addrspace ? d->addrspace : "(none)", d->len, d->select, d->start);
   }
}

/* Read a whole file; the cores here all take data, not a path. */
static void *read_file(const char *path, size_t *size)
{
   FILE *f = fopen(path, "rb");
   if (!f) { perror(path); exit(2); }
   fseek(f, 0, SEEK_END);
   long len = ftell(f);
   fseek(f, 0, SEEK_SET);
   void *buf = malloc((size_t)len ? (size_t)len : 1);
   if (fread(buf, 1, (size_t)len, f) != (size_t)len) {
      fprintf(stderr, "nesrun: short read on %s\n", path);
      exit(2);
   }
   fclose(f);
   if (size) *size = (size_t)len;
   return buf;
}

int main(int argc, char **argv)
{
   const char *core_path = NULL, *rom_path = NULL;
   long frames = 600;
   const char *wav_path = NULL, *hash_path = NULL, *input_path = NULL;
   const char *watch_path = NULL, *load_state = NULL, *save_state = NULL;
   bool do_probe = false, do_memlist = false;

   crc_init();

   for (int i = 1; i < argc; i++) {
      const char *a = argv[i];
      #define ARG() (i + 1 < argc ? argv[++i] : (fprintf(stderr, "nesrun: %s needs a value\n", a), exit(2), (char*)0))
      if (!strcmp(a, "--core")) core_path = ARG();
      else if (!strcmp(a, "--rom")) rom_path = ARG();
      else if (!strcmp(a, "--frames")) frames = atol(ARG());
      else if (!strcmp(a, "--dir")) snprintf(out_dir, sizeof(out_dir), "%s", ARG());
      else if (!strcmp(a, "--png")) snprintf(png_ranges, sizeof(png_ranges), "%s", ARG());
      else if (!strcmp(a, "--png-every")) png_every = atoi(ARG());
      else if (!strcmp(a, "--png-from")) png_from = atoi(ARG());
      else if (!strcmp(a, "--scale")) png_scale = atoi(ARG());
      else if (!strcmp(a, "--crop")) sscanf(ARG(), "%d,%d,%d,%d", &crop_x, &crop_y, &crop_w, &crop_h);
      else if (!strcmp(a, "--wav")) wav_path = ARG();
      else if (!strcmp(a, "--hash")) hash_path = ARG();
      else if (!strcmp(a, "--var")) var_set(ARG());
      else if (!strcmp(a, "--var-file")) {
         const char *pf = ARG();
         FILE *vf = fopen(pf, "r");
         if (!vf) { perror(pf); return 2; }
         char line[512];
         while (fgets(line, sizeof(line), vf)) {
            char *p = line;
            while (*p == ' ' || *p == '\t') p++;
            if (*p == '#' || *p == '\n' || *p == 0) continue;
            char *nl = strpbrk(p, "\r\n"); if (nl) *nl = 0;
            var_set(p);
         }
         fclose(vf);
      }
      else if (!strcmp(a, "--input")) { input_path = ARG(); }
      else if (!strcmp(a, "--watch")) add_watch(ARG());
      else if (!strcmp(a, "--watch-out")) watch_path = ARG();
      else if (!strcmp(a, "--save-state")) save_state = ARG();
      else if (!strcmp(a, "--load-state")) load_state = ARG();
      else if (!strcmp(a, "--probe")) do_probe = true;
      else if (!strcmp(a, "--mem-list")) do_memlist = true;
      else if (!strcmp(a, "--sysdir")) snprintf(sysdir, sizeof(sysdir), "%s", ARG());
      else if (!strcmp(a, "--quiet")) quiet = true;
      else if (!strcmp(a, "-h") || !strcmp(a, "--help")) {
         printf("see the comment block at the top of libretro_host.c\n");
         return 0;
      }
      else { fprintf(stderr, "nesrun: unknown arg %s\n", a); return 2; }
   }

   if (!core_path) { fprintf(stderr, "nesrun: --core required\n"); return 2; }

   void *h = dlopen(core_path, RTLD_NOW | RTLD_LOCAL);
   if (!h) { fprintf(stderr, "nesrun: %s\n", dlerror()); return 2; }

   BIND(h, retro_init, true);
   BIND(h, retro_deinit, true);
   BIND(h, retro_api_version, true);
   BIND(h, retro_get_system_info, true);
   BIND(h, retro_get_system_av_info, true);
   BIND(h, retro_set_environment, true);
   BIND(h, retro_set_video_refresh, true);
   BIND(h, retro_set_audio_sample, true);
   BIND(h, retro_set_audio_sample_batch, true);
   BIND(h, retro_set_input_poll, true);
   BIND(h, retro_set_input_state, true);
   BIND(h, retro_set_controller_port_device, false);
   BIND(h, retro_reset, false);
   BIND(h, retro_run, true);
   BIND(h, retro_serialize_size, false);
   BIND(h, retro_serialize, false);
   BIND(h, retro_unserialize, false);
   BIND(h, retro_load_game, true);
   BIND(h, retro_unload_game, true);

   p_retro_set_environment(environ_cb);
   p_retro_init();

   struct retro_system_info si;
   memset(&si, 0, sizeof(si));
   p_retro_get_system_info(&si);

   if (do_probe) {
      printf("library_name:    %s\n", si.library_name ? si.library_name : "?");
      printf("library_version: %s\n", si.library_version ? si.library_version : "?");
      printf("valid_extensions:%s\n", si.valid_extensions ? si.valid_extensions : "?");
      printf("need_fullpath:   %d\n", si.need_fullpath);
      p_retro_set_video_refresh(video_cb);
      p_retro_set_audio_sample(audio_sample);
      p_retro_set_audio_sample_batch(audio_batch);
      p_retro_set_input_poll(input_poll_cb);
      p_retro_set_input_state(input_state_cb);
      if (rom_path) {
         struct retro_game_info gi;
         size_t romsize = 0;
         void *romdata = read_file(rom_path, &romsize);
         memset(&gi, 0, sizeof(gi));
         gi.path = rom_path;
         gi.data = romdata;
         gi.size = romsize;
         if (!p_retro_load_game(&gi)) { fprintf(stderr, "load_game failed\n"); return 1; }
         struct retro_system_av_info av;
         p_retro_get_system_av_info(&av);
         printf("base_w:          %u\n", av.geometry.base_width);
         printf("base_h:          %u\n", av.geometry.base_height);
         printf("max_w:           %u\n", av.geometry.max_width);
         printf("max_h:           %u\n", av.geometry.max_height);
         printf("aspect:          %f\n", av.geometry.aspect_ratio);
         printf("fps:             %.6f\n", av.timing.fps);
         printf("sample_rate:     %f\n", av.timing.sample_rate);
         printf("mem regions:     %u\n", memmap.num_descriptors);
      }
      p_retro_deinit();
      return 0;
   }

   if (!rom_path) { fprintf(stderr, "nesrun: --rom required\n"); return 2; }

   size_t romlen = 0;
   void *romdata = read_file(rom_path, &romlen);

   p_retro_set_video_refresh(video_cb);
   p_retro_set_audio_sample(audio_sample);
   p_retro_set_audio_sample_batch(audio_batch);
   p_retro_set_input_poll(input_poll_cb);
   p_retro_set_input_state(input_state_cb);
   if (p_retro_set_controller_port_device)
      p_retro_set_controller_port_device(0, RETRO_DEVICE_JOYPAD);

   struct retro_game_info gi;
   memset(&gi, 0, sizeof(gi));
   gi.path = rom_path;
   gi.data = romdata;
   gi.size = romlen;
   if (!p_retro_load_game(&gi)) {
      fprintf(stderr, "nesrun: retro_load_game failed\n");
      return 1;
   }

   struct retro_system_av_info av;
   p_retro_get_system_av_info(&av);
   if (!quiet)
      fprintf(stderr, "nesrun: %s %s | %.3f fps | %.0f Hz | %ux%u (max %ux%u)\n",
              si.library_name ? si.library_name : "core",
              si.library_version ? si.library_version : "",
              av.timing.fps, av.timing.sample_rate,
              av.geometry.base_width, av.geometry.base_height,
              av.geometry.max_width, av.geometry.max_height);

   if (do_memlist) { list_memories(); p_retro_unload_game(); p_retro_deinit(); return 0; }

   if (load_state) {
      FILE *sf = fopen(load_state, "rb");
      if (!sf) { perror(load_state); return 2; }
      fseek(sf, 0, SEEK_END);
      long sl = ftell(sf);
      fseek(sf, 0, SEEK_SET);
      void *sb = malloc((size_t)sl);
      if (fread(sb, 1, (size_t)sl, sf) != (size_t)sl) { return 2; }
      fclose(sf);
      if (!p_retro_unserialize(sb, (size_t)sl)) {
         fprintf(stderr, "nesrun: unserialize failed\n");
         return 1;
      }
      free(sb);
   }

   if (input_path) load_inputs(input_path);
   if (png_ranges[0] || png_every) ensure_dir(out_dir);
   if (wav_path) wav_open(wav_path);
   if (hash_path) { hash_fp = fopen(hash_path, "w"); if (!hash_fp) { perror(hash_path); return 2; } }
   if (watch_count) {
      /* No --watch-out?  Go to stderr: stdout stays clean for the caller. */
      watch_fp = watch_path ? fopen(watch_path, "w") : stderr;
      if (!watch_fp) { perror(watch_path); return 2; }
   }

   long save_frame = -1;
   char save_path[512] = "";
   if (save_state) {
      char *colon = strchr(save_state, ':');
      if (colon) {
         save_frame = strtol(save_state, NULL, 10);
         snprintf(save_path, sizeof(save_path), "%s", colon + 1);
      }
   }

   /* Warn once about the frame geometry the core actually produces. */
   long first_w = -1, first_h = -1;

   for (long f = 0; f < frames; f++) {
      pad_state = input_for_frame(f);
      p_retro_run();

      if (first_w < 0 && frame_px) {
         first_w = (long)frame_w; first_h = (long)frame_h;
         if (!quiet) fprintf(stderr, "nesrun: frame size %ldx%ld\n", first_w, first_h);
      }

      if (hash_fp) hash_frame(f);

      if (watch_count) {
         fprintf(watch_fp, "F %ld", f);
         for (int wi = 0; wi < watch_count; wi++) {
            bool any = false;
            for (unsigned k = 0; k < watch[wi].len; k++) {
               const unsigned char *p = mem_byte_region(watch[wi].region,
                                                        watch[wi].off + k);
               if (!p) { fprintf(watch_fp, " --"); continue; }
               fprintf(watch_fp, " %02X", *p);
               any = true;
            }
            if (!any) fprintf(watch_fp, " NA");
         }
         fputc('\n', watch_fp);
      }

      bool want = false;
      if (png_ranges[0] && in_png_ranges(f)) want = true;
      if (png_every && f >= png_from && ((f - png_from) % png_every) == 0) want = true;
      if (want) dump_frame(f);

      if (f == save_frame && p_retro_serialize && p_retro_serialize_size) {
         size_t sz = p_retro_serialize_size();
         void *sb = malloc(sz);
         if (sb && p_retro_serialize(sb, sz)) {
            FILE *sf = fopen(save_path, "wb");
            if (sf) { fwrite(sb, 1, sz, sf); fclose(sf); }
         }
         free(sb);
      }
   }

   if (watch_fp && watch_fp != stderr) fclose(watch_fp);
   if (hash_fp) fclose(hash_fp);
   wav_close();

   if (!quiet)
      fprintf(stderr, "nesrun: done %ld frames, %d png(s), %u audio frames\n",
              frames, dumped, wav_frames);

   p_retro_unload_game();
   p_retro_deinit();
   free(romdata);
   dlclose(h);
   return 0;
}
