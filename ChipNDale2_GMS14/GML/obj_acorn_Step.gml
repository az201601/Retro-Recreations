//=============================================================================
// obj_acorn  --  Step event   (thrown acorn projectile)
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
// Paste into the Step event of  obj_acorn.
// Flies mostly flat (small gravity), defeats enemies on contact, then
// disappears. The player creates this when throwing an acorn.
//=============================================================================

// Slight gravity -> gentle arc (acorns fly flatter than blocks).
vsp = min(vsp + global.ACORN_GRAVITY, global.P_MAX_FALL);

scr_move_x(hsp);
scr_move_y(vsp);

// Spin while flying (acorns tumble in the original).
image_angle += 10;

// Defeat an enemy on contact.
var e = instance_nearest(x, y, obj_enemy);
if (e != noone and abs(e.x - x) < 10 and abs(e.y - y) < 10) {
    with (e) instance_destroy();
    audio_play_sound(snd_hit, 5, false); // (add this sound resource)
    instance_destroy();
    exit;
}

// Destroy if it leaves the room.
if (x < -32 or x > room_width + 32 or y < -32 or y > room_height + 32) {
    instance_destroy();
}
