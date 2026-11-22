/// scr_move_v(dy) -- move the CALLING instance vertically; sets .on_ground
var dy;
dy = argument0;
y += dy;
on_ground = false;
if (dy > 0) {
    if (scr_solid_at(x - global.player_w/2 + 2, y) || scr_solid_at(x + global.player_w/2 - 2, y)) {
        y = floor(y / global.tile_size) * global.tile_size - 0.01;
        vspeed = 0;
        on_ground = true;
    }
} else if (dy < 0) {
    if (scr_solid_at(x - global.player_w/2 + 2, y - global.player_h) || scr_solid_at(x + global.player_w/2 - 2, y - global.player_h)) {
        y = floor((y - global.player_h) / global.tile_size) * global.tile_size + global.tile_size + global.player_h + 0.01;
        vspeed = 0;
    }
}
