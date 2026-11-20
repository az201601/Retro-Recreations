//=============================================================================
// obj_block  --  Step event   (throwable crate / barrel / ball)
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
// Paste into the Step event of  obj_block.
// Sits still until picked up. When thrown it flies, bounces once, and can
// knock out enemies -- just like the original.
//=============================================================================

if (held) {
    // Follow the player, held overhead.
    var p = instance_nearest(x, y, obj_player);
    if (p != noone) {
        x = p.x;
        y = p.y - 20;
    }
    exit; // no physics while held
}

// Gravity (gentle arc for thrown blocks)
vsp = min(vsp + global.BLOCK_GRAVITY, global.P_MAX_FALL);

scr_move_x(hsp);
var hit_floor = scr_move_y(vsp);
if (hit_floor) {
    if (thrown and abs(vsp) > 1) {
        vsp = -vsp * 0.4; // bounce once
        audio_play_sound(snd_bounce, 5, false); // (add this sound resource)
    } else {
        vsp = 0;
        hsp = 0; // come to rest
    }
}

// Hit an enemy? Knock it out (original: one hit = enemy defeated).
if (thrown) {
    var e = instance_nearest(x, y, obj_enemy);
    if (e != noone and abs(e.x - x) < 12 and abs(e.y - y) < 12) {
        with (e) instance_destroy();
        thrown = false;
        hsp = 0;
        audio_play_sound(snd_hit, 5, false); // (add this sound resource)
    }
}
