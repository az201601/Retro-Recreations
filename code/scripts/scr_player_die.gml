/// scr_player_die  (GameMaker: Studio 1.4)
// Called on the player instance when hp reaches 0.
// ============================================================================
if (hp > 0) exit;

global.lives -= 1;

if (global.lives <= 0) {
    global.game_state = "gameover";
    room_goto(rm_title);
} else {
    room_restart();
}
