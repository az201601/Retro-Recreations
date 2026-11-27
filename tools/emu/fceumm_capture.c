#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <dlfcn.h>
#include <sys/stat.h>
#include "libretro.h"

static unsigned frame_no, target_frames = 1200, width, height, capture_interval = 30;
static FILE *wav;
static uint64_t samples_written;
static char outdir[512] = "tools/out/spotlight";
static bool env_cb(unsigned cmd, void *data) {
  switch (cmd) {
    case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT: return *(enum retro_pixel_format*)data == RETRO_PIXEL_FORMAT_XRGB8888;
    case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
    case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY: *(const char**)data = "."; return true;
    case RETRO_ENVIRONMENT_GET_CAN_DUPE: *(bool*)data = true; return true;
    case RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME: return true;
    default: return false;
  }
}
static void input_poll(void) {}
static int16_t input_state(unsigned p, unsigned d, unsigned i, unsigned id) { (void)p;(void)d;(void)i;(void)id; return 0; }
static void video_cb(const void *pixels, unsigned w, unsigned h, size_t pitch) {
  width=w; height=h;
  if (!pixels || frame_no % capture_interval != 0) return;
  char path[600]; snprintf(path,sizeof(path),"%s/frame_%05u.ppm",outdir,frame_no);
  FILE *f=fopen(path,"wb"); if(!f) return;
  fprintf(f,"P6\n%u %u\n255\n",w,h);
  const unsigned char *src=(const unsigned char*)pixels;
  for(unsigned y=0;y<h;y++) for(unsigned x=0;x<w;x++) {
    const unsigned char *p=src+y*pitch+x*4;
    unsigned char rgb[3]={p[2],p[1],p[0]}; fwrite(rgb,1,3,f);
  }
  fclose(f);
}
static size_t audio_batch(const int16_t *data, size_t frames) { if(wav && data) { fwrite(data,sizeof(int16_t)*2,frames,wav); samples_written += frames; } return frames; }
static void audio_one(int16_t l,int16_t r) { int16_t s[2]={l,r}; if(wav){fwrite(s,sizeof(s),1,wav);samples_written++;} }
int main(int argc,char **argv) {
  if(argc>1) target_frames=(unsigned)strtoul(argv[1],0,10);
  if(argc>2) snprintf(outdir,sizeof(outdir),"%s",argv[2]);
  if(argc>3) capture_interval=(unsigned)strtoul(argv[3],0,10);
  if(!capture_interval) capture_interval=1;
  mkdir("tools/out",0777); mkdir(outdir,0777);
  void *lib=dlopen("tools/emu/libretro-fceumm/fceumm_libretro.so",RTLD_NOW|RTLD_LOCAL);
  if(!lib){fprintf(stderr,"dlopen: %s\n",dlerror());return 2;}
  __typeof__(&retro_set_environment) retro_set_environment=dlsym(lib,"retro_set_environment");
  __typeof__(&retro_set_video_refresh) retro_set_video_refresh=dlsym(lib,"retro_set_video_refresh");
  __typeof__(&retro_set_audio_sample) retro_set_audio_sample=dlsym(lib,"retro_set_audio_sample");
  __typeof__(&retro_set_audio_sample_batch) retro_set_audio_sample_batch=dlsym(lib,"retro_set_audio_sample_batch");
  __typeof__(&retro_set_input_poll) retro_set_input_poll=dlsym(lib,"retro_set_input_poll");
  __typeof__(&retro_set_input_state) retro_set_input_state=dlsym(lib,"retro_set_input_state");
  __typeof__(&retro_init) retro_init=dlsym(lib,"retro_init");
  __typeof__(&retro_load_game) retro_load_game=dlsym(lib,"retro_load_game");
  __typeof__(&retro_run) retro_run=dlsym(lib,"retro_run");
  __typeof__(&retro_unload_game) retro_unload_game=dlsym(lib,"retro_unload_game");
  __typeof__(&retro_deinit) retro_deinit=dlsym(lib,"retro_deinit");
  if(!retro_set_environment||!retro_set_video_refresh||!retro_set_audio_sample||!retro_set_audio_sample_batch||!retro_set_input_poll||!retro_set_input_state||!retro_init||!retro_load_game||!retro_run||!retro_unload_game||!retro_deinit){fprintf(stderr,"missing libretro symbol\n");return 2;}
  retro_set_environment(env_cb); retro_set_video_refresh(video_cb); retro_set_audio_sample(audio_one); retro_set_audio_sample_batch(audio_batch);
  retro_set_input_poll(input_poll); retro_set_input_state(input_state); retro_init();
  const char *rom="Chip 'n Dale - Rescue Rangers 2 (USA).nes";
  struct retro_game_info game={0}; game.path=rom;
  if(!retro_load_game(&game)){fprintf(stderr,"ROM load failed\n");return 3;}
  char wavpath[600]; snprintf(wavpath,sizeof(wavpath),"%s/audio.wav",outdir); wav=fopen(wavpath,"wb+");
  if(!wav){perror(wavpath);return 4;} unsigned char blank[44]={0}; fwrite(blank,1,44,wav);
  for(frame_no=0;frame_no<target_frames;frame_no++) retro_run();
  fclose(wav); wav=NULL; fflush(stdout);
  /* Patch PCM WAV header after the captured stream. */
  FILE *wf=fopen(wavpath,"r+b"); if(wf){uint32_t data_bytes=(uint32_t)(samples_written*4), riff=36+data_bytes, rate=48000, byte_rate=rate*4; uint16_t one=1,bits=16,ch=2,align=4;
    fwrite("RIFF",1,4,wf); fwrite(&riff,4,1,wf); fwrite("WAVEfmt ",1,8,wf); uint32_t fmt=16; fwrite(&fmt,4,1,wf); fwrite(&one,2,1,wf); fwrite(&ch,2,1,wf); fwrite(&rate,4,1,wf); fwrite(&byte_rate,4,1,wf); fwrite(&align,2,1,wf); fwrite(&bits,2,1,wf); fwrite("data",1,4,wf); fwrite(&data_bytes,4,1,wf); fclose(wf);}
  retro_unload_game();retro_deinit();dlclose(lib);
  printf("FCEUmm capture: %u frames, video %ux%u, %llu audio sample frames, output %s\n",target_frames,width,height,(unsigned long long)samples_written,outdir);
  return 0;
}
