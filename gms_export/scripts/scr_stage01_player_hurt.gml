/// scr_stage01_player_hurt() | called with obj_player as self
if (invuln > 0 || global.stage01_game_over || global.stage01_clear) exit;
hp -= 1;
invuln = 90;
if (hp <= 0) {
    global.stage01_lives -= 1;
    if (global.stage01_lives <= 0) {
        global.stage01_game_over = true;
        hp = 0;
        exit;
    }
    hp = 3;
    scr_stage01_enter(global.stage01_part);
}
