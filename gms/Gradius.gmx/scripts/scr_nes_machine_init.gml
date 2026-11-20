/// scr_nes_machine_init()
// Initializes Gradius NES hardware state, PPU staging buffers, 32-slot SoA
// object tables ($0100-$04FF), player record ($0017-$004C), and clock.

var i;

// NTSC PPU timing reference (oracle/README.md)
global.nes_fps = 60.098814;
global.nes_frame_ms = 1000.0 / 60.098814;
global.nes_frame = 0;
global.nes_elapsed_ms = 0.0;
global.debug_overlay = false;

// Surface for pixel-exact 256x240 PPU output
global.ppu_surface = -1;

// Input latch ($0005/$0007, $009C)
global.pad_raw = 0;
global.pad_prev = 0;
global.pad_held = 0;     // $0007 (A=$80 B=$40 Sel=$20 St=$10 U=8 D=4 L=2 R=1)
global.pad_pressed = 0;  // $0005 (edge-triggered)

// Core game state ($0000-$003F)
global.ram_mode = 0;          // $0000: 0=title scroll-in, 1=title menu, 3=start flash, 4=stage init, 5=active play
global.ram_substate = 0;      // $0001
global.ram_frame_ctr = 0;     // $0002
global.ram_player_sel = 0;    // $000F: 0=1P, 1=2P
global.ram_paused = 0;        // $0015
global.ram_difficulty = 0;    // $0017
global.ram_stage = 0;         // $0019 (0=Stage 1)
global.ram_stage_flags = 0;   // $001B ($80=active play)
global.ram_hud_visible = 0;   // $001F (0=off, >0=Sprite-0 HUD split enabled)
global.ram_oam_rot = 4;       // $002F (rotating OAM slot offset 1..63, steps +17 slots = +$44 bytes)
global.ram_scroll_x = 254;    // $0012 staged horizontal scroll
global.ram_scroll_y = 0;      // $0013 staged vertical scroll
global.ram_cam_x = 0;         // $003E/$003F camera scroll fixed point (0.5 px/frame in Stage 1)
global.ram_timer = 0;         // $004C generic state countdown
global.ram_ppu_active = 0;    // $0011 rendering enabled (blank frames 0..3 like NES)

// Player zero-page record ($0020-$0046)
global.p_lives = 3;           // $0020
global.p_score = 0;
global.p_hiscore = 50000;
global.p_speed = 0;           // $0040 (0..14)
global.p_missile = 0;         // $0041 (0/1)
global.p_power = 0;           // $0042 (0..6: 1=SPD,2=MSL,3=DBL,4=LSR,5=OPT,6=SHD)
global.p_weapon = 0;          // $0044 (0=Normal, 1=Laser, 2=Double)
global.p_options = 0;         // $0045 (0..2)
global.p_shield = 0;          // $0046 (0..5)
global.konami_step = 0;       // $9789 pause Konami code state (0..10)

// Sound queue / APU tick state
global.apu_sfx_queue = -1;
global.apu_sfx_timer = 0;

// 24-entry Option trail ring buffer ($07A0-$07B7, $07C0-$07D7)
for (i = 0; i < 24; i += 1) {
    global.opt_trail_x[i] = 80;
    global.opt_trail_y[i] = 96;
}

// 32-slot Structure-of-Arrays Object RAM ($0100-$04FF)
// 0=Player, 1..2=Options, 3..5=ShotA, 6..8=ShotB, 9..11=Missiles, 12..21=Enemies, 22..31=EnemyProj
for (i = 0; i < 32; i += 1) {
    global.obj_state[i] = 0;   // $0100,X
    global.obj_spr[i] = 0;     // $0120,X metasprite ID
    global.obj_anim_t[i] = 0;  // $0140,X anim timer
    global.obj_anim_i[i] = 0;  // $0160,X anim frame / trail head / weapon type
    global.obj_attr[i] = 0;    // $0180,X OAM attribute override
    global.obj_type[i] = 0;    // $0300,X AI behavior / type
    global.obj_y[i] = 0;       // $0320,X integer Y
    global.obj_ysub[i] = 0;    // $0340,X fractional Y (0..255)
    global.obj_x[i] = 0;       // $0360,X integer X
    global.obj_xsub[i] = 0;    // $0380,X fractional X (0..255)
    global.obj_cd[i] = 0;      // $03A0,X cooldown / drop group
    global.obj_vy[i] = 0;      // $03BC/$03EC signed 8.8 Y velocity (float px/frame)
    global.obj_vx[i] = 0;      // $042C/$044C signed 8.8 X velocity (float px/frame)
    global.obj_hp[i] = 0;      // $046C,X HP / timer
}

// OAM shadow ($0200-$02FF staged at End-of-Frame) and VBlank-latched PPU OAM (64 slots)
for (i = 0; i < 64; i += 1) {
    global.oam_sh_y[i] = 244;      // $F4 = offscreen
    global.oam_sh_sid[i] = 0;
    global.oam_sh_attr[i] = 0;
    global.oam_sh_x[i] = 244;
    global.oam_sh_frame[i] = 0;

    global.ppu_oam_y[i] = 244;
    global.ppu_oam_sid[i] = 0;
    global.ppu_oam_attr[i] = 0;
    global.ppu_oam_x[i] = 244;
    global.ppu_oam_frame[i] = 0;
}

// Staged -> VBlank-latched PPU display registers
global.next_mode = 0;
global.next_ppu_active = 0;
global.next_scroll_x = 254;
global.next_scroll_y = 0;
global.next_hud_visible = 0;
global.next_hud_power = 0;
global.next_hud_lives = 3;
global.next_hud_score = 0;
global.next_hud_hiscore = 50000;

global.ppu_mode = 0;
global.ppu_active = 0;
global.ppu_scroll_x = 254;
global.ppu_scroll_y = 0;
global.ppu_hud_visible = 0;
global.ppu_hud_power = 0;
global.ppu_hud_lives = 3;
global.ppu_hud_score = 0;
global.ppu_hud_hiscore = 50000;
