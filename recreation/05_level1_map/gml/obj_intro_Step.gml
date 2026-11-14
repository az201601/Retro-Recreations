/// obj_intro : Step
frame += 1;
var n = frame;

// ---- 0) controller ------------------------------------------------------------
var pad = 0;
if (keyboard_check(vk_enter)) pad |= 1;     // START
if (keyboard_check(vk_shift)) pad |= 2;     // SELECT
if (keyboard_check(ord("X"))) pad |= 4;     // A
if (keyboard_check(vk_up))    pad |= 8;     // UP
if (keyboard_check(vk_down))  pad |= 16;    // DOWN
if (keyboard_check(ord("Z"))) pad |= 32;    // B
if (keyboard_check(vk_left))  pad |= 64;    // LEFT
if (keyboard_check(vk_right)) pad |= 128;   // RIGHT
if ((pad & 24) == 24) pad -= 24;            // UP + DOWN together cancel out (impossible on a real d-pad)
var pressed = pad & (pad_prev ^ 255);        // buttons that went down on this frame
pad_prev = pad;
var start_pressed = ((pressed & 1) != 0);

// ---- 1) sound ---------------------------------------------------------------------
// the menu sound effects use the 2nd square channel of the NES; the music on that channel comes back afterwards
if (n == sq2_unmute) audio_sound_gain(theme_sq2, 1, 0);

// a sound requested on the previous frame starts now
if (snd_queue != -1)
{
    if (snd_queue == snd_title_theme)
    {
        // the title music replaces whatever intro sound is still playing
        audio_stop_sound(snd_intro_jingle);
        audio_stop_sound(snd_intro_roll);
        theme_main = audio_play_sound(snd_title_theme, 10, true);       // both are 2880 frames long and loop forever
        theme_sq2  = audio_play_sound(snd_title_theme_sq2, 10, true);
    }
    else if (snd_queue == snd_menu_select || snd_queue == snd_menu_move)
    {
        audio_stop_sound(snd_menu_select);      // only one effect at a time (one NES channel)
        audio_stop_sound(snd_menu_move);
        audio_play_sound(snd_queue, 20, false);
        audio_sound_gain(theme_sq2, 0, 0);      // the effect takes the channel away from the music ...
        if (snd_queue == snd_menu_select) sq2_unmute = n + 12;   // ... for 12 frames
        else                              sq2_unmute = n + 10;   // ... for 10 frames
    }
    else
    {
        audio_play_sound(snd_queue, 10, false);
    }
    snd_queue = -1;
}
if (n == 0) audio_play_sound(snd_intro_pops, 10, false);   // two APU "thumps" on NES frames 169 and 189 (optional)

// ---- 2) scripted spotlight sequence (stops for good once START skips it) ---
if (skip_frame < 0 && n < fade_start)
{
    switch (n)
    {
        case 14:    // NES frame 170: brick wall mask is on screen
            bg_mode = 1;
            break;
        case 32:    // NES frame 188: spotlight is created above the screen, moving down 2 px/frame
            spot_on = true;
            spot_x  = 160 * 256;
            spot_y  = -95 * 256;
            spot_vx = 0;
            spot_vy = 512;
            break;
        case 160:   // NES frame 316: up-left, 1.375 px/frame on both axes
            spot_vx = -352;
            spot_vy = -352;
            break;
        case 256:   // NES frame 412: right, 2 px/frame
            spot_vx = 512;
            spot_vy = 0;
            break;
        case 320:   // NES frame 476: down-left, 1.375 px/frame
            spot_vx = -352;
            spot_vy = 352;
            break;
        case 368:   // NES frame 524: left, 2 px/frame (leaves the screen)
            spot_vx = -512;
            spot_vy = 0;
            break;
        case 496:   // NES frame 652: wall now has the Chip & Dale silhouettes, intro jingle is requested
            bg_mode   = 2;
            snd_queue = snd_intro_jingle;
            break;
        case 497:   // NES frame 653: spotlight is moved off-screen left, comes back in at 2 px/frame
            spot_x  = -164 * 256;
            spot_y  = 73 * 256;
            spot_vx = 512;
            spot_vy = 0;
            break;
        case 630:   // NES frame 786: overshoots, snaps back left at 4 px/frame
            spot_vx = -1024;
            break;
        case 646:   // NES frame 802: stops on the silhouettes, drum roll is requested
            spot_vx   = 0;
            snd_queue = snd_intro_roll;
            break;
    }

    if (spot_on)
    {
        spot_x += spot_vx;
        spot_y += spot_vy;
    }

    // START skips the intro, but only while the spotlight is travelling (NES frames 188..801).
    // The picture freezes and the fade-out begins 5 frames later.
    if (start_pressed && n >= 32 && n <= 645)
    {
        skip_frame = n;
        fade_start = n + 5;
    }
}

// ---- 3) fade out the spotlight, fade in the title screen -------------------
var f = n - fade_start;
if (f >= 0)
{
    switch (f)
    {
        case 0:  spot_fade = 1;                break;
        case 4:  spot_fade = 2;                break;
        case 8:  spot_fade = 3;                break;
        case 12: spot_on = false;              break;   // all black
        case 17: bg_mode = 0;                  break;
        case 20: snd_queue = snd_title_theme;  break;   // audible from f == 21
        case 25: title_fade = 0;               break;
        case 29: title_fade = 1;               break;
        case 33: title_fade = 2;               break;
        case 37: title_fade = 3;               break;   // title screen fully visible
    }
}

// ---- 4) menus ---------------------------------------------------------------------
// 4a) a button pressed on the previous frame takes effect on this frame
if (act_move)
{
    act_move    = false;
    menu_cursor = 1 - menu_cursor;
    snd_queue   = snd_menu_move;
}
if (act_confirm)
{
    act_confirm = false;
    snd_queue   = snd_menu_select;      // replaces the move sound if both happen on the same frame
    menu_t      = n;
    if (menu_state == 0)
    {
        menu_state  = 1;                // "Press START button" turns into 1player / 2players (takes 3 frames)
        menu_cursor = 0;
    }
    else if (menu_state == 1 && menu_cursor == 0)
    {
        menu_state = 2;                 // 1player: choose Chip or Dale
    }
    else
    {
        if (menu_state == 1) { global.players = 2; global.p1_char = 0; }
        else                 { global.players = 1; global.p1_char = menu_cursor; }
        menu_from  = menu_state;
        menu_state = 3;                 // the screen fades out; buttons are ignored from here on
    }
}

// 4b) read the buttons
if (menu_state == 0)
{
    // the title screen accepts START from f == 38 on (A, B, SELECT and the d-pad do nothing)
    if (f >= 38 && start_pressed) act_confirm = true;
}
else if ((menu_state == 1 && n >= menu_t + 2) || (menu_state == 2 && n >= menu_t + 1))
{
    if ((pressed & 26) != 0) act_move    = true;    // SELECT, UP or DOWN: the cursor goes to the other line
    if ((pressed & 5)  != 0) act_confirm = true;    // START or A
}

// 4c) after the choice: fade steps on menu_t + 4 / + 8 / + 12 (see Draw), black from menu_t + 16
if (menu_state == 3 && n == menu_t + 16) menu_state = 4;
if (menu_state == 4 && n == menu_t + 23)
{
    // the title music is cut off here by the sound of the next screen
    audio_stop_sound(snd_title_theme);
    audio_stop_sound(snd_title_theme_sq2);
    // the night scene (section 5) appears on frame menu_t + 41
}

// ---- 5) night scene: fence, skyline, blimp, searchlights ------------------------------
if (menu_state == 4 && !ns_done)
{
    var t = n - (menu_t + 41);      // scene clock; negative while the screen is still black

    // 5a) blimp: half a pixel per frame
    if ((t >= 44 && t <= 331) || t >= 524) ns_blimp_x += 128;    // flies in and stops; flies on once it is lit
    if (t >= 396 && t <= 427) ns_blimp_y += 128;                 // sinks 16 pixels ...
    if (t >= 492 && t <= 523) ns_blimp_y -= 128;                 // ... and rises again

    // 5b) leaving the scene: START (accepted from t == 13) or the end of the script on t == 1003.
    //     Each of the two starts the fade-out clock 34 frames later (a second one restarts it);
    //     the first one decides when the scene ends.
    if (start_pressed && t >= 13 && !ns_skipped && (ns_exit_t < 0 || t < ns_exit_t + 55))
    {
        ns_skipped    = true;
        ns_fade_at1   = t + 34;
        ns_alarm_skip = t + 2;      // START swallows an alarm restart that is due right now
        if (ns_exit_t < 0) ns_exit_t = t;
    }
    if (t == 1003)
    {
        ns_fade_at2 = t + 34;
        if (ns_exit_t < 0) ns_exit_t = t;
    }

    // 5c) one fade-out step every 4 frames
    if (ns_fade_t0 >= 0 && t > ns_fade_t0 && ((t - ns_fade_t0) mod 4) == 0)
    {
        ns_lv_bg    = min(ns_lv_bg + 1, 4);
        ns_lv_blimp = min(ns_lv_blimp + 1, 4);
        if (ns_beam_mode == 2) ns_lv_beam = min(ns_lv_beam + 1, 4);
    }
    // the alarm gets quieter from the moment the scene starts to end
    if (ns_exit_t >= 0 && t > ns_exit_t && ((t - ns_exit_t) mod 4) == 0 && ns_vol > 1)
    {
        ns_vol -= 1;
        if (ns_alarm != -1) audio_sound_gain(ns_alarm, ns_gain[ns_vol], 0);
    }

    // 5d) the lights come on - in the original even when the picture is already fading or black
    if (t == 525)
    {
        ns_blimp_lit = 1;
        ns_lv_blimp  = 0;
        ns_beam_mode = 1;
    }
    if (ns_beam_mode == 1 && t > 526 && ((t - 526) mod 64) == 0) ns_beam = 1 - ns_beam;

    // 5e) the fade-out clock starts; the searchlights stop swapping
    if (t == ns_fade_at1 || t == ns_fade_at2)
    {
        ns_fade_t0 = t;
        if (ns_beam_mode == 1)
        {
            if (t > 525) ns_beam_mode = 2;
            else         ns_beam_mode = 0;
        }
    }

    // 5f) end of the scene
    if (ns_exit_t >= 0 && t == ns_exit_t + 57)
    {
        ns_done = true;
        global.skip_cutscene = ns_skipped;
        nw_t0 = n + 12;     // the newscaster cutscene (section 6) appears 12 frames from now
        if (ns_skipped) lv_d = n;   // START was pressed: the game goes straight to the first level (section 7)
    }
    else if (t >= 526 && ((t - 526) mod 49) == 0 && t != ns_alarm_skip)
    {
        // 5g) the alarm is 49 frames long and is started again every 49 frames
        audio_stop_sound(snd_prison_alarm);
        ns_alarm = audio_play_sound(snd_prison_alarm, 10, false);
        audio_sound_gain(ns_alarm, ns_gain[ns_vol], 0);
    }
}

// ---- 6) newscaster cutscene ----------------------------------------------------------------
if (ns_done && !nw_done && !global.skip_cutscene)
{
    var nt = n - nw_t0;             // cutscene clock; -12 on the frame the night scene ends
    var i, c, a, sg, free;

    // 6a) leaving the cutscene: START (accepted from nt == 13) or the end of the script. Same as in the night scene:
    //     each of the two starts the fade-out clock 34 frames later, the first one decides when the cutscene ends.
    if (start_pressed && nt >= 13 && !nw_skipped && (nw_exit_t < 0 || nt < nw_exit_t + 55))
    {
        nw_skipped   = true;
        nw_fade_at1  = nt + 34;
        nw_type_skip = nt + 1;      // START swallows the typing sound of a character typed on the next frame
        if (nw_exit_t < 0) nw_exit_t = nt;
    }
    if (nw_fade_t0 >= 0 && nt > nw_fade_t0 && ((nt - nw_fade_t0) mod 4) == 0) nw_lv = min(nw_lv + 1, 4);
    // the sound gets quieter from the moment the cutscene starts to end
    if (nw_exit_t >= 0 && nt > nw_exit_t && ((nt - nw_exit_t) mod 4) == 0 && nw_quiet < 11) nw_quiet += 1;
    if (nt == nw_fade_at1 || nt == nw_fade_at2) nw_fade_t0 = nt;

    if (nw_exit_t >= 0 && nt == nw_exit_t + 57)
    {
        nw_done = true;
        audio_stop_sound(snd_news_music_a);
        audio_stop_sound(snd_news_music_b);
        lv_d = n;           // the first level (section 7) starts
    }
    else
    {
        // 6b) text box
        nw_mouth_shown = nw_mouth;
        if (nw_mode == 0 && nw_page < nw_pages)
        {
            if (nt == nw_wait_t0 + nw_pg_pre[nw_page])
            {
                nw_mode = 1;  nw_ti = 0;  nw_next_tick = nt;  nw_fast = false;  nw_ncol = 0;
                nw_speaker = nw_pg_speaker[nw_page];
            }
        }
        if (nw_mode == 0 && nw_page == nw_pages && nt == nw_wait_t0 + 8)
        {
            nw_fade_at2 = nt + 34;  // end of the script
            if (nw_exit_t < 0) nw_exit_t = nt;
        }
        if (nw_mode == 1)
        {
            if (nt == nw_next_tick)
            {
                i = nw_pg_first[nw_page] + nw_ti;
                nw_ti += 1;
                // kind of step: 0 = a character, 1 = a space, 2 = go to the next line (takes 1 frame, no sound)
                if (nw_tk_kind[i] == 0)
                {
                    c = nw_tk_row[i] * 32 + nw_tk_col[i];
                    nw_text[c] = nw_tk_top[i];
                    if (nw_tk_bot[i] > 0) nw_text[c + 32] = nw_tk_bot[i];   // lower half of a tall character
                }
                if (nw_tk_kind[i] == 2)
                {
                    nw_ncol = 0;
                    nw_next_tick = nt + 1;
                }
                else
                {
                    nw_ncol += 1;
                    if (nw_fast) nw_next_tick = nt + 1;
                    else
                    {
                        nw_next_tick = nt + 5;
                        if (nt != nw_type_skip) nw_type_at = nt + 1;
                    }
                }
                nw_mouth = (nw_ncol >> 1) & 1;
                if (nw_ti == nw_pg_count[nw_page]) { nw_mode = 2;  nw_end = nw_next_tick; }
            }
            if (nw_b_held) nw_fast = true;      // B (held on the previous frame) types the rest of the page at once
        }
        else if (nw_mode == 2)
        {
            // the page is cleared 120 frames after it was complete, or at once by pressing B
            if (nt == nw_end + 120 || (nt > nw_end && nw_b_pressed))
            {
                nw_clear_t = nt;
                nw_mouth   = 0;
                nw_page   += 1;
                nw_wait_t0 = nt;
                nw_gstart[nw_page] = nt;
                nw_mode    = 0;
            }
        }
        nw_b_held    = ((pad & 32) != 0);
        nw_b_pressed = ((pressed & 32) != 0);
        for (i = 3; i <= 8; i += 1)             // the 6 rows of the text box go blank one after the other
        {
            if (nt == nw_clear_t + nw_clear_at[i])
            {
                for (c = 0; c < 32; c += 1) nw_text[i * 32 + c] = 0;
            }
        }

        // 6c) sound. The typing sound uses the 2nd square channel of the NES: the music's part on that channel
        //     (snd_news_music_b) goes silent and only comes back with its next note.
        if (nt == nw_music_t0)
        {
            audio_stop_sound(snd_prison_alarm);
            nw_music_a = audio_play_sound(snd_news_music_a, 10, true);   // both are 1920 frames long and loop
            nw_music_b = audio_play_sound(snd_news_music_b, 10, true);
        }
        if (nt == nw_type_at)
        {
            c = nw_type_snd[nw_pg_voice[min(nw_page, nw_pages - 1)]];
            audio_stop_sound(c);
            a = audio_play_sound(c, 20, false);
            audio_sound_gain(a, (11 - nw_quiet) / 11, 0);
            nw_gate = 0;  nw_pend = 0;  nw_busy_until = nt + 3;
        }
        if (nt >= nw_music_t0)
        {
            if (nw_note[(nt - nw_music_t0) mod nw_music_len] == 1) nw_pend = 1;
        }
        if (nt > nw_busy_until)
        {
            if (nw_pend == 1) nw_gate = 1;
            nw_pend = 0;
        }
        if (nw_music_a != -1)
        {
            audio_sound_gain(nw_music_a, (11 - nw_quiet) / 11, 0);
            audio_sound_gain(nw_music_b, nw_gate * (11 - nw_quiet) / 11, 0);
        }

        // 6d) actors. Each movement is a recorded track (picture, x, y per frame) that starts a fixed number of
        //     frames after a page was cleared; an actor stays on the last frame of his track until the next one.
        for (sg = 0; sg < nw_segs; sg += 1)
        {
            if (nw_gstart[nw_sg_page[sg]] >= 0)
            {
                if (nt == nw_gstart[nw_sg_page[sg]] + nw_sg_off[sg])
                {
                    nw_seg[nw_sg_actor[sg]]    = sg;
                    nw_seg_t0[nw_sg_actor[sg]] = nt;
                }
            }
        }
        // Zipper hovers on his own 252-frame clock; once the script lets him go he leaves at the start of a wing beat
        if (nw_seg[3] >= 0 && nw_ball_left < 0 && nw_gstart[nw_ball_rel_page] >= 0)
        {
            if (nt >= nw_gstart[nw_ball_rel_page] + nw_ball_rel_off)
            {
                i = nt - nw_seg_t0[3] - nw_ball_hover;
                if (i > 0)
                {
                    c = i mod 252;
                    if ((c mod 6) == 0 && c > 0 && c < 240) { nw_ball_y = nw_ay[3];  nw_ball_left = nt; }
                }
            }
        }
        for (a = 0; a < 6; a += 1)
        {
            nw_ac[a] = 0;  nw_ax[a] = 0;  nw_ay[a] = 0;
            if (nw_seg[a] >= 0)
            {
                i = nt - nw_seg_t0[a];
                if (a == 3 && i >= nw_ball_hover)
                {
                    if (nw_ball_left >= 0)
                    {
                        c = nw_ball_first + min(nt - nw_ball_left, nw_ball_count - 1);     // flying off
                        nw_ac[a] = nw_tr_cel[c];  nw_ax[a] = nw_tr_x[c];  nw_ay[a] = nw_tr_y[c] - 128 + nw_ball_y;
                    }
                    else
                    {
                        c = (i - nw_ball_hover) mod 252;                                   // hovering
                        if (c >= 240) nw_ac[a] = nw_ball_cel2 + ((c mod 6) div 3);
                        else          nw_ac[a] = nw_ball_cel + ((c mod 6) div 3);
                        nw_ax[a] = nw_ball_x;
                        nw_ay[a] = nw_ball_hy[c mod 12];
                    }
                }
                else
                {
                    c = nw_sg_first[nw_seg[a]] + min(i, nw_sg_count[nw_seg[a]] - 1);
                    nw_ac[a] = nw_tr_cel[c];  nw_ax[a] = nw_tr_x[c];  nw_ay[a] = nw_tr_y[c];
                }
            }
        }
        // object slots: an actor who appears takes the lowest free slot from 3 up (Chip always has slot 2)
        for (a = 1; a < 6; a += 1)
        {
            if (nw_ac[a] == 0) nw_slot[a] = -1;
            else if (nw_slot[a] < 0)
            {
                free = 3;
                for (i = 0; i < 6; i += 1) { if (nw_slot[i] == free) { free += 1;  i = -1; } }
                nw_slot[a] = free;
            }
        }
        // the star shows one frame earlier when its slot comes after Dale's
        if (nw_seg[5] >= 0)
        {
            if (nt - nw_seg_t0[5] == nw_star_first - 1)
            {
                free = 3;
                for (i = 0; i < 6; i += 1) { if (nw_slot[i] == free) { free += 1;  i = -1; } }
                if (free > nw_slot[4])
                {
                    nw_seg_t0[5] -= 1;
                    nw_slot[5] = free;
                    c = nw_sg_first[nw_seg[5]] + min(nt - nw_seg_t0[5], nw_sg_count[nw_seg[5]] - 1);
                    nw_ac[5] = nw_tr_cel[c];  nw_ax[5] = nw_tr_x[c];  nw_ay[5] = nw_tr_y[c];
                }
            }
        }
        // the speaker's mouth
        if (nw_speaker >= 0 && nw_mouth_shown == 1)
        {
            if (nw_open[nw_ac[nw_speaker]] > 0) nw_ac[nw_speaker] = nw_open[nw_ac[nw_speaker]];
        }
    }
}

// ---- 7) level 1, section 1: the dining room ---------------------------------------------------
//         So far: music, background, camera and the way out. No player, enemies, crates or hearts yet.
if (lv_d >= 0 && !lv_done)
{
    var lt = n - (lv_d + 7);        // level clock; -7 on the frame the previous screen ended

    // 7a) the level music starts one frame after the previous screen ended
    if (lt == -6)
    {
        audio_stop_sound(snd_prison_alarm);     // still playing at its lowest volume when START skipped the night scene
        lv_music_a = audio_play_sound(snd_lv1_music_a, 10, true);    // both are 1920 frames long and loop
        lv_music_b = audio_play_sound(snd_lv1_music_b, 10, true);
    }

    // 7b) TEMPORARY, until the player exists (next step): LEFT / RIGHT move the camera 2 pixels per frame.
    //     In the original the camera follows the player, and the section ends when the player walks off the
    //     right edge of the last screen. Here: press RIGHT once more when the camera is at its right end.
    if (lt >= 17 && lv_exit_t < 0)
    {
        if ((pressed & 128) != 0 && lv_cam_x == 1792) lv_exit_t = lt;
        else if ((pad & 128) != 0) lv_cam_x = min(lv_cam_x + 2, 1792);
        else if ((pad & 64) != 0)  lv_cam_x = max(lv_cam_x - 2, 0);
    }

    // 7c) leaving the section: the picture fades out (see Draw) and is black from lv_exit_t + 17
    if (lv_exit_t >= 0 && lt == lv_exit_t + 22)
    {
        lv_done = true;
        // TODO (later step): the next section (the kitchen) appears on level frame lv_exit_t + 31.
        //                    No new music is started there, the level music should keep playing.
    }
}
