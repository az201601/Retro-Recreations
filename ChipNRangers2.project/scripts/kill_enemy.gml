/// kill_enemy()
// called from a crate that hit this enemy
global.score += 100;
instance_create(x, y - 2, objSpark);
audio_play_sound(sndEnemyHit, 6, false);
instance_destroy();
