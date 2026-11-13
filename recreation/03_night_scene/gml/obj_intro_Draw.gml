/// obj_intro : Draw
// (the room background colour is black)

// ---- spotlight (NES: 32 8x16 sprites, drawn BEHIND the background) ---------
if (spot_on)
{
    var ox = floor(spot_x / 256);
    var oy = floor(spot_y / 256);

    // the NES hides sprites in the left-most 8 pixels of the screen
    var left = max(0, 8 - ox);

    // the game drops a 16 pixel high row of sprites while its Y is still above the screen.
    // rows start at 0, 16, 31 and 47 inside the 64x63 image.
    var top;
    if      (oy      >= 1) top = 0;
    else if (oy + 16 >= 1) top = 16;
    else if (oy + 31 >= 1) top = 31;
    else if (oy + 47 >= 1) top = 47;
    else                   top = -1;

    if (top >= 0 && left < 64)
    {
        draw_sprite_part(spr_spotlight, spot_fade, left, top, 64 - left, 63 - top, ox + left, oy + top);
    }
}

// ---- black mask in front of the spotlight (NES: background layer) ----------
if (bg_mode == 1)      draw_background(bg_intro_wall, 0, 0);
else if (bg_mode == 2) draw_background(bg_intro_silhouette, 0, 0);

// ---- title screen and menus ---------------------------------------------------
if (title_fade >= 0 && menu_state < 4)
{
    var t   = frame - menu_t;       // frames since the menu changed
    var par = frame & 1;            // the two face sprites swap drawing order every frame (NES sprite flicker)
    var k   = -1;                   // fade-out step 0..2, -1 = not fading
    if (menu_state == 3) k = (t div 4) - 1;

    if (k < 0)
    {
        draw_sprite(spr_title_bg, title_fade, 0, 0);   // NES background layer
        draw_sprite(spr_title_fg, title_fade, 0, 0);   // NES sprite layer (22 sprites that add extra colours to the artwork)
    }
    else
    {
        draw_sprite(spr_title_out, k, 0, 0);           // whole title picture, fade-out colours
    }

    // menu panel: 160x32 pixels at (48,188), covers "Press START button"
    var sub = -1;
    if (menu_state == 1)
    {
        if (t < 2) sub = t;                             // 0, 1: the text is being replaced
        else       sub = 2 + menu_cursor;               // 2, 3: 1player / 2players with the cursor
    }
    else if (menu_state == 2)
    {
        if (t < 1) sub = 4;                             // Chip / Dale text, faces not there yet
        else       sub = 5 + menu_cursor * 2 + par;     // 5..8
    }
    else if (menu_state == 3)
    {
        if (menu_from == 1)
        {
            if (k < 0) sub = 3;
            else       sub = 9 + k;                     // 9..11
        }
        else
        {
            if (k < 0) sub = 5 + menu_cursor * 2 + par;
            else       sub = 12 + menu_cursor * 6 + k * 2 + par;   // 12..17 Chip, 18..23 Dale
        }
    }
    if (sub >= 0) draw_sprite(spr_menu, sub, 48, 188);
}

// ---- night scene ------------------------------------------------------------------------
if (menu_state == 4 && !ns_done)
{
    var t = frame - (menu_t + 41);
    if (t >= 0 && (ns_exit_t < 0 || t < ns_exit_t + 55))
    {
        // background: two bands that scroll at different speeds (screen row 178 between them stays black)
        var top = min(max(t - 43, 0), 256);                 // sky and skyline: 1 pixel per frame, 256 pixels
        var bot = (2 * min(max(t - 42, 0), 256)) mod 512;   // fence: 2 pixels per frame, once around its 512 pixels
        if (ns_lv_bg < 3)
        {
            var sub;
            if (ns_lv_bg == 0) sub = min(t div 4, 3);       // 0..3: fade-in, 3 = full brightness
            else               sub = 3 + ns_lv_bg;          // 4, 5: fade-out
            draw_sprite(spr_prison_far, sub, -top, 0);
            draw_sprite(spr_prison_fence, sub, -bot, 179);
            draw_sprite(spr_prison_fence, sub, 512 - bot, 179);
        }

        // searchlight beams (NES: part of the background, made visible by changing two palette colours)
        if (ns_beam_mode > 0 && t >= 526)
        {
            // the unlit beam has the colour of the sky: invisible, except when the sky is already black
            if (ns_beam_mode == 1)
            {
                if (ns_beam == 0) draw_sprite(spr_prison_beam_b, 4, 0, 0);
                else              draw_sprite(spr_prison_beam_a, 4, 0, 0);
            }
            if (ns_lv_beam < 4)
            {
                if (ns_beam == 0) draw_sprite(spr_prison_beam_a, ns_lv_beam, 0, 0);
                else              draw_sprite(spr_prison_beam_b, ns_lv_beam, 0, 0);
            }
        }

        // blimp (NES: 11 sprites in front of the background)
        if (t >= 44 && ns_lv_blimp < 4)
        {
            var prop = ((t + 12) >> 3) & 1;                 // propeller: 2 pictures, 8 frames each
            var bx   = (ns_blimp_x >> 8) - 32;              // left edge of the 40x24 image
            var by   = (ns_blimp_y >> 8) + 1;
            var left = max(0, 8 - bx);                      // the NES hides sprites in the left-most 8 pixels
            if (left < 40)
            {
                draw_sprite_part(spr_prison_blimp, ns_blimp_lit * 8 + ns_lv_blimp * 2 + prop,
                                 left, 0, 40 - left, 24, bx + left, by);
            }
        }
    }
}
