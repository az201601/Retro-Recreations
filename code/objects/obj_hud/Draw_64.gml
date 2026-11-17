/// obj_hud - Draw GUI
// NES style HUD: portrait + hearts bottom-left, score top-right.
// Everything is drawn with the GameMaker default font so the layout works
// before the extracted font strip is imported.
// ============================================================================
var _hx, _hy, _i, _heart;

_hx = 8;
_hy = room_height - 32;

_heart = asset_get_index("spr_ui_heart");
if (_heart < 0) _heart = asset_get_index("spr_hud_hearts");

if (instance_exists(obj_player)) {
    if (_heart >= 0) {
        for (_i = 0; _i < obj_player.hp; _i += 1) {
            draw_sprite_ext(_heart, 0, _hx + 16 + _i * 8, _hy + 10,
                            1, 1, 0, c_white, 1);
        }
    }
}

draw_set_colour(c_white);
draw_set_halign(fa_right);
draw_set_valign(fa_top);
draw_set_font(-1);

draw_text(room_width - 8, 6, string(global.score));

draw_set_halign(fa_left);
draw_set_valign(fa_top);
