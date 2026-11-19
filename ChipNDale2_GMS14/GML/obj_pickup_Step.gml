//=============================================================================
// obj_pickup  --  Step event   (flower = health, star = points)
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
// Paste into the Step event of  obj_pickup.
// Bobs gently up and down. Collected when the player touches it.
//=============================================================================

// Gentle bobbing (+/- 2 px), like the original pickups.
bob_timer += 1;
y = base_y + sin(bob_timer * 0.1) * 2;

// Collect on player contact.
var p = instance_nearest(x, y, obj_player);
if (p != noone and abs(p.x - x) < 12 and abs(p.y - y) < 12) {
    if (kind == 0) {
        p.health = min(global.START_HEALTH, p.health + 1); // flower: +1 heart
        audio_play_sound(snd_pickup, 5, false);            // (add this sound)
    } else {
        global.score += global.SCORE_STAR;                  // star: points
        audio_play_sound(snd_pickup, 5, false);            // (add this sound)
    }
    instance_destroy();
}
