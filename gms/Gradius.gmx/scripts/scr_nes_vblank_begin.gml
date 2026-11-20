/// scr_nes_vblank_begin()
// Explicit VBlank-Begin phase (Begin Step -> NES NMI $806A..$809C).
// Latches staged OAM shadow ($0200-$02FF) into hardware PPU OAM via OAM DMA
// ($4014) and commits staged scroll/HUD/mode registers before frame rendering.

var i;

// 1. OAM DMA ($0200-$02FF -> PPUOAM): 1-frame pipeline from previous End-of-Frame
for (i = 0; i < 64; i += 1) {
    global.ppu_oam_y[i] = global.oam_sh_y[i];
    global.ppu_oam_sid[i] = global.oam_sh_sid[i];
    global.ppu_oam_attr[i] = global.oam_sh_attr[i];
    global.ppu_oam_x[i] = global.oam_sh_x[i];
    global.ppu_oam_frame[i] = global.oam_sh_frame[i];
}

// 2. Latch PPU scroll/control/HUD state ($8281 / $8A51)
global.ppu_mode = global.next_mode;
global.ppu_active = global.next_ppu_active;
global.ppu_scroll_x = global.next_scroll_x;
global.ppu_scroll_y = global.next_scroll_y;
global.ppu_hud_visible = global.next_hud_visible;
global.ppu_hud_power = global.next_hud_power;
global.ppu_hud_lives = global.next_hud_lives;
global.ppu_hud_score = global.next_hud_score;
global.ppu_hud_hiscore = global.next_hud_hiscore;
global.ppu_title_blink = global.next_title_blink;
global.ppu_player_sel = global.next_player_sel;

// 3. Advance NES frame counter and NTSC reference clock
global.nes_frame += 1;
global.nes_elapsed_ms = global.nes_frame * global.nes_frame_ms;
