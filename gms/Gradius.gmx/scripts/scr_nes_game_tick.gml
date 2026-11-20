/// scr_nes_game_tick()
// Main game mode dispatch ($80BE -> $80D1 jump table).
// Executes during Step after input latch and APU tick.

var i;

global.ram_frame_ctr = (global.ram_frame_ctr + 1) & $FF;

if (global.ram_mode == 0) {
    // Mode 0: Boot + Title Screen slide-in ($80E2)
    // Frames 1..3 keep PPU rendering off; Frame 4+ slides title left by 2 px/frame.
    if (global.nes_frame < 4) {
        global.ram_ppu_active = 0;
        global.ram_scroll_x = 254;
        global.obj_state[0] = 0;
        global.obj_spr[0] = 0;
    } else {
        global.ram_ppu_active = 1;
        if ((global.pad_pressed & $3C) != 0) {
            // sub_821A: Start/Select (plus Up/Down convenience) snaps scroll to 0 and enters menu
            global.ram_scroll_x = 0;
            global.ram_mode = 1;
        } else {
            if (global.ram_scroll_x > 0) {
                global.ram_scroll_x -= 2;
                if (global.ram_scroll_x <= 0) {
                    global.ram_scroll_x = 0;
                    global.ram_mode = 1;
                }
            }
        }
    }
    if (global.ram_mode == 1) {
        global.obj_state[0] = 1;
        global.obj_spr[0] = 1;
        global.obj_x[0] = 80;
        global.obj_y[0] = 134 + global.ram_player_sel * 16;
    }
} else if (global.ram_mode == 1) {
    // Mode 1: Title menu active ($8116 / $821A)
    global.ram_ppu_active = 1;
    global.ram_scroll_x = 0;
    global.obj_state[0] = 1;
    global.obj_spr[0] = 1;
    global.obj_x[0] = 80;
    global.obj_y[0] = 134 + global.ram_player_sel * 16;

    if ((global.pad_pressed & $20) != 0) {
        // Select: toggle 1P / 2P (authentic NES $8239)
        global.ram_player_sel = 1 - global.ram_player_sel;
        global.obj_y[0] = 134 + global.ram_player_sel * 16;
    } else if ((global.pad_pressed & $08) != 0) {
        // Up: select 1 PLAYER
        global.ram_player_sel = 0;
        global.obj_y[0] = 134;
    } else if ((global.pad_pressed & $04) != 0) {
        // Down: select 2 PLAYERS
        global.ram_player_sel = 1;
        global.obj_y[0] = 150;
    } else if ((global.pad_pressed & $10) != 0) {
        // Start: begin game flash ($8140: $50 = 80 frames)
        global.ram_num_players = global.ram_player_sel + 1;
        global.ram_mode = 3;
        global.ram_timer = 80;
        global.apu_sfx_queue = 0;
    }
} else if (global.ram_mode == 3) {
    // Mode 3: Title Start confirmation blink ($8137 / $814B..$815E)
    if (global.ram_timer > 0) {
        global.ram_timer -= 1;
    }
    if (global.ram_timer <= 0) {
        global.ram_mode = 4;
        global.ram_timer = 4;
    }
} else if (global.ram_mode == 4) {
    // Mode 4: Stage 1 initialization ($8165 -> sub_9B3E)
    global.ram_mode = 5;
    global.ram_substate = 0;
    global.ram_paused = 0;
    global.konami_step = 0;
    global.ram_stage = 0;
    global.ram_stage_flags = 0;
    global.ram_hud_visible = 0;
    global.ram_scroll_x = 0;
    global.ram_scroll_y = 12;
    global.ram_cam_x = 0;
    global.ram_timer = 28; // F262..F290 pre-roll before HUD & active scrolling

    for (i = 0; i < 32; i += 1) {
        global.obj_state[i] = 0;
        global.obj_spr[i] = 0;
        global.obj_type[i] = 0;
        global.obj_x[i] = 0;
        global.obj_y[i] = 0;
        global.obj_xsub[i] = 0;
        global.obj_ysub[i] = 0;
        global.obj_cd[i] = 0;
    }

    // Spawn player at Stage 1 coordinates ($50=80, $60=96)
    global.obj_state[0] = 1;
    global.obj_spr[0] = 1;
    global.obj_x[0] = 80;
    global.obj_y[0] = 96;
    global.obj_anim_i[0] = 0;
    global.obj_anim_t[0] = 0;

    for (i = 0; i < 24; i += 1) {
        global.opt_trail_x[i] = 80;
        global.opt_trail_y[i] = 96;
    }

    if (room != rm_stage1) {
        room_goto(rm_stage1);
    }
} else if (global.ram_mode == 5) {
    // Mode 5: Active Stage Gameplay ($9650)
    global.ram_ppu_active = 1;

    // Pause toggle ($9AE2)
    if ((global.ram_stage_flags & $80) != 0 && (global.pad_pressed & $10) != 0) {
        global.ram_paused = 1 - global.ram_paused;
        global.konami_step = 0;
    }

    if (global.ram_paused == 0) {
        if ((global.ram_stage_flags & $80) == 0) {
            if (global.ram_timer > 0) {
                global.ram_timer -= 1;
            }
            if (global.ram_timer <= 0) {
                global.ram_stage_flags = $80;
                global.ram_hud_visible = 1;
            }
        } else {
            // Stage 1 horizontal camera scroll: 0.5 px/frame ($003E/$003F)
            global.ram_cam_x += 0.5;
            if (global.ram_cam_x >= 512) {
                global.ram_cam_x -= 512;
            }
            global.ram_scroll_x = floor(global.ram_cam_x);
            global.ram_scroll_y = 12;

            // Update Player, Options, and Weapons (sub_9FFC)
            scr_player_update();
        }
    } else {
        // Paused: listen for Konami code (sub_9765 / $9789)
        scr_player_update();
    }
}
