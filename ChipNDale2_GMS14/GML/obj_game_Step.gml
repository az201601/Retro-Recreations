//=============================================================================
// obj_game  --  Step event   (game rules: damage, lives, game over)
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
// Paste into the Step event of  obj_game.
//=============================================================================

// Enemy touches player -> lose a heart (with a brief invincible period).
var p = instance_nearest(0, 0, obj_player);
if (p != noone and p.invincible_timer <= 0) {
    var e = instance_nearest(p.x, p.y, obj_enemy);
    if (e != noone and abs(e.x - p.x) < 12 and abs(e.y - p.y) < 12) {
        p.health -= 1;
        p.invincible_timer = 90; // ~1.5 seconds of mercy (original behaviour)
        audio_play_sound(snd_hurt, 5, false); // (add this sound resource)
        if (p.health <= 0) {
            p.lives -= 1;
            if (p.lives < 0) {
                game_restart(); // out of lives -> back to the start
            } else {
                p.health = global.START_HEALTH; // new life, full hearts
                // Respawn at the room start (move player to a safe spot).
                p.x = 32;
                p.y = 32;
                p.hsp = 0;
                p.vsp = 0;
            }
        }
    }
}
