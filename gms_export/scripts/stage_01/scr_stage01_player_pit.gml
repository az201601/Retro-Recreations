/// scr_stage01_player_pit() | bottomless gaps cost a life even during i-frames
global.stage01_lives -= 1;
if (global.stage01_lives <= 0) {
    hp = 0;
    global.stage01_game_over = true;
} else {
    hp = 3;
    scr_stage01_enter(global.stage01_part);
}
