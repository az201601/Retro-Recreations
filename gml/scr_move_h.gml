/// scr_move_h(dx) -- move the CALLING instance horizontally, stop at walls
var dx, i;
dx = argument0;
x += dx;
if (dx > 0) {
    if (scr_solid_at(x + global.player_w/2, y - 2)
     || scr_solid_at(x + global.player_w/2, y - global.player_h/2)
     || scr_solid_at(x + global.player_w/2, y - global.player_h + 2)) {
        x = floor((x + global.player_w/2) / global.tile_size) * global.tile_size - global.player_w/2 - 0.01;
    }
} else if (dx < 0) {
    if (scr_solid_at(x - global.player_w/2, y - 2)
     || scr_solid_at(x - global.player_w/2, y - global.player_h/2)
     || scr_solid_at(x - global.player_w/2, y - global.player_h + 2)) {
        x = floor((x - global.player_w/2) / global.tile_size) * global.tile_size + global.tile_size + global.player_w/2 + 0.01;
    }
}
