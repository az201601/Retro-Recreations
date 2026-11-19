//=============================================================================
// obj_game  --  Create event   (game-wide state)
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
// Paste into the Create event of an object named  obj_game.
// NOTE: scr_init() is called from the GAME START event (see scr_init.gml),
// so all global.* physics constants already exist by the time this runs.
//=============================================================================

global.score = 0;   // total score (flowers/stars add to this)
// Lives and health live on obj_player (each character has their own).
