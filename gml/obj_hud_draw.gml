// obj_hud -- Draw event (place one instance; set depth = -100 so it draws on top)
// The NES HUD shows the heart row bottom-left and a boxed counter above it
// (see assets/sprites/obj_00.png / obj_01.png -- import as spr_hud_hearts,
// spr_hud_counter).
var i;
for (i = 0; i < global.max_hearts; i += 1) {
    if (i < obj_player.hearts) draw_sprite(spr_heart, 0, 16 + i * 12, room_height - 16);
    else draw_sprite(spr_heart_empty, 0, 16 + i * 12, room_height - 16);
}
// counter (spr_hud_counter is the "3-box" strip; crop per your import)
draw_sprite(spr_hud_counter, 0, 12, room_height - 32);
