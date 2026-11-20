/// scr_nes_apu_tick()
// Sound driver tick skeleton ($ED02 / $EC1E).
// Runs once per NES frame after input latch. Currently dispatches queued SFX
// assets (docs/audio.md & docs/sound-driver.md).

if (global.apu_sfx_queue >= 0) {
    if (global.apu_sfx_queue == 0) {
        audio_play_sound(sfx_title_start, 10, false);
        global.apu_sfx_timer = 19; // frames ~0.31s matching sfx_title_start.wav
    }
    global.apu_sfx_queue = -1;
}

if (global.apu_sfx_timer > 0) {
    global.apu_sfx_timer -= 1;
}
