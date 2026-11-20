//=============================================================================
// obj_game  --  Draw event   (HUD: score, lives, health)
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
// Paste into the Draw event of  obj_game.
// Draws the heads-up display in SCREEN space (it follows the view).
//=============================================================================

draw_set_alpha(1);
draw_set_color(c_white);
// Top-left of the visible screen:
var sx = view_xview + 8;
var sy = view_yview + 8;
draw_text(sx, sy, "SCORE " + string(global.score));

var p = instance_nearest(view_xview + 128, view_yview + 128, obj_player);
if (p != noone) {
    draw_text(sx, sy + 12, "LIVES " + string(p.lives));
    // Hearts (health) as small squares -- swap for heart sprites later.
    for (var i = 0; i < p.health; i += 1) {
        draw_set_color(c_red);
        draw_rectangle(sx + 8 + i * 10, sy + 26, sx + 15 + i * 10, sy + 33, false);
    }
    draw_set_color(c_white);
}
