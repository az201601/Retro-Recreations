/// obj_player : User Defined 0   (one NES frame of the player; run by obj_stage1, see its End Step)
var held = p_pad;
var pressed = p_pressed;
if (p_auto) { held = 128; pressed = 0; }        // leaving the section: walks right, nothing else
if ((held & 24) == 24) { held &= 231; pressed &= 231; }     // UP and DOWN together count as neither
p_landed = false;
p_snd = 0;

// the eyes in the crate: after 11 frames of hiding under it the player looks out, for 101 frames, then the
// eyes are shut for 16 frames, and so on. The crate follows what the player did one frame ago.
if (p_carry != noone)
{
    if (p_state == 3 && p_cnt >= 11 && p_cnt <= 111) p_carry.c_eyes = 1 + p_face;
    else p_carry.c_eyes = 0;
}

// ---- 0) bonus boxes ------------------------------------------------------------------------
if (p_state != 23) scr_pl_touch();

// ---- 1) what the player does, by the state at the start of the frame -----------------
switch (p_state)
{
    case 5:     // on the ground
    case 20:    // walking out of the section (does not fall)
        if (p_state == 5 && !scr_pl_floor()) { p_pose = 2; p_yv = 0; p_state = 1; }      // walked off an edge
        else if ((held & 16) != 0) { p_state = 3; p_cnt = 0; }                           // DOWN: crouch
        else if ((pressed & 4) != 0) { p_yv = -110; p_state = 8; p_pose = 2; }           // A: jump
        else if ((held & 192) == 0) { p_state = 5; p_pose = 0; p_cnt = 0; }              // stand
        else                                                                             // walk
        {
            p_pose = 1;
            p_walk = (p_cnt div 8) mod 4;       // a new picture every 8 frames
            p_cnt = (p_cnt + 1) mod 256;
        }
        break;

    case 3:     // crouching
        if (!scr_pl_floor()) { p_pose = 2; p_yv = 0; p_state = 1; }
        else
        {
            p_pose = 4;
            // with a crate: nothing else for the 4 frames the crate takes to come down
            var lock = (p_carry != noone && p_cnt < 4);
            if (!lock && (held & 16) == 0) { p_state = 5; p_pose = 0; p_cnt = 0; }
            else if (!lock && (pressed & 4) != 0 && !scr_pl_row(p_y, 2))
            {
                p_pose = 2; p_yv = 0; p_state = 1;      // DOWN + A on a thin platform: drop through it
            }
            else
            {
                p_cnt += 1;                             // frames spent crouching (used with a crate, see 5 and the eyes above)
                if (p_cnt == 128) p_cnt = 11;
            }
        }
        break;

    case 8:     // jumping: rising for as long as A is held
        var over = true;
        scr_pl_move_y();
        if (p_y >= p_h && p_y <= 255 && scr_pl_row(p_y - p_h, 2))
        {
            p_y = (((p_y - p_h) div 16) + 1) * 16 + p_h;        // the head hit a solid block
        }
        else
        {
            p_yv += 6;
            if (p_yv < 0) over = false;
        }
        if (over) p_yv = 0;
        if (over || (held & 4) == 0)
        {
            if (scr_pl_floor()) { p_state = 5; p_pose = 0; p_cnt = 0; }
            else { p_pose = 2; p_yv = 0; p_state = 1; }
        }
        break;

    case 1:     // falling
        var y0 = p_y;
        p_yv = min(p_yv + 6, 110);
        scr_pl_move_y();
        // lands only on the frame the feet pass the top edge of a block row
        if (p_y >= 0 && p_y <= 255 && floor(p_y / 16) != floor(y0 / 16))
        {
            if (scr_pl_row(p_y, 1))
            {
                p_y = (p_y div 16) * 16;
                p_ysub = 0;
                p_landed = true;
                p_cnt = 0; p_state = 2; p_pose = 3;
            }
        }
        break;

    case 2:     // just landed: 5 frames, cut short by LEFT / RIGHT or a new jump
        if (!scr_pl_floor()) { p_pose = 2; p_yv = 0; p_state = 1; }
        else if ((pressed & 4) != 0) { p_yv = -110; p_state = 8; p_pose = 2; }
        else
        {
            var go = true;
            if ((held & 192) == 0)
            {
                p_cnt += 1;
                if (p_cnt < 5) go = false;
            }
            if (go)
            {
                if ((held & 16) != 0) { p_state = 3; p_cnt = 0; }
                else { p_state = 5; p_pose = 0; p_cnt = 0; }
            }
        }
        break;

    case 23:    // fell out of the picture: wait, then the section starts again
        p_cnt -= 1;
        if (p_cnt == 0) p_restart = true;
        break;
}

// ---- 2) fell below the picture --------------------------------------------------------
if (p_state < 20 && p_y >= 232)
{
    p_state = 23;
    p_cnt = 60;
    stage.lv_lives -= 1;
    if (p_carry != noone)
    {
        p_run = 0;
        scr_pl_throw(8);        // a carried crate flies straight up (with the throw sound)
    }
}

// ---- 3) carrying: the run-up and the throw ----------------------------------------------
// the run-up counts the frames walked on the ground without a stop
if (p_state == 5 && p_carry != noone && p_moved != 0 && (held & 192) != 0) p_run = min(p_run + 1, 255);
else p_run = 0;
if (p_carry != noone && (pressed & 32) != 0 && p_state != 23) scr_pl_throw(held);      // B: throw

// ---- 4) left / right (and picking up a crate) -------------------------------------------
if (p_state != 23)
{
    var x0 = p_x;
    if (p_throw >= 2) p_xv = 0;                 // stands still while throwing (not on the frame of the throw itself)
    else
    {
        if (!p_auto)
        {
            p_xv = 0;
            if ((held & 128) != 0)     { p_face = 1; p_xv = 2; }
            else if ((held & 64) != 0) { p_face = 0; p_xv = -2; }
            if (p_state == 3) p_xv = 0;             // crouching: turns around but does not move
        }
        var cam = stage.lv_cam_x;
        if (p_xv > 0)
        {
            p_x += p_xv;
            if (!p_auto && p_x + 6 >= 244) p_x = 238;                       // right edge of the screen
            if (p_x + 6 < 256)
            {
                if (scr_pl_wall(p_x + 6))
                {
                    p_x = ((p_x + 6 + cam) div 16) * 16 - 6 - cam;
                    scr_pl_pick(pressed);                                   // walked into a block: a crate?
                }
            }
        }
        else if (p_xv < 0)
        {
            p_x += p_xv;
            if (p_x - 6 < 12) p_x = 18;                                     // left edge of the screen
            if (scr_pl_wall(p_x - 6))
            {
                p_x = ((p_x + 9 + cam) div 16) * 16 + 6 - cam;
                scr_pl_pick(pressed);
            }
        }
        if (p_auto && p_x >= 256) p_out = true;     // walked off the right edge
    }
    p_moved = p_x - x0;
}

// ---- 5) picture and body height --------------------------------------------------------
p_hide = false;
p_h = 22;
if (p_throw > 0)                                // throwing: 3 frames picture 12, 12 frames picture 13
{
    p_blink = 0;
    if (p_throw < 4) p_pic = 12; else p_pic = 13;
    p_throw = (p_throw + 1) mod 16;
}
else if (p_pose == 0)
{
    p_blink = (p_blink + 255) mod 256;
    if ((p_blink & 112) == 0) p_pic = 6; else p_pic = 0;
    if (p_carry != noone) p_pic = 7;
}
else
{
    p_blink = 0;
    if (p_pose == 1)
    {
        if (p_walk == 0) p_pic = 1; else if (p_walk == 2) p_pic = 3; else p_pic = 2;
        if (p_carry != noone) p_pic += 7;
    }
    else if (p_pose == 2)
    {
        if (p_carry != noone) p_pic = 11; else p_pic = 5;
    }
    else
    {
        p_pic = 4;
        if (p_pose == 4) p_h = 16;
        if (p_pose == 4 && p_carry != noone && p_state == 3)
        {
            // crouching under the crate: it comes down over the player, who is hidden from the 2nd frame on
            p_h = p_duck[min(p_cnt - 1, 9)];
            if (p_cnt > 1) p_hide = true;
        }
    }
}

// ---- 6) the carried crate sits on the head -------------------------------------------------
if (p_carry != noone)
{
    p_carry.c_wx = p_x + stage.lv_cam_x;
    if (p_h == 0) p_carry.c_y = p_y; else p_carry.c_y = p_y - p_h - 1;
}
