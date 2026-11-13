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

// ---- title screen -----------------------------------------------------------
if (title_fade >= 0)
{
    draw_sprite(spr_title_bg, title_fade, 0, 0);   // NES background layer
    draw_sprite(spr_title_fg, title_fade, 0, 0);   // NES sprite layer (22 sprites that add extra colours to the artwork)
}
