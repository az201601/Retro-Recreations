/// scr_cutscene_add  (GameMaker: Studio 1.4)
// Append one shot to a cut-scene object's shot list.
//
// @param inst     id of the obj_cutscene instance
// @param anim     animation key registered in scr_anim_init
// @param x, y     screen position
// @param steps    how long the shot stays on screen (60 = 1 second)
// ============================================================================
var _s;
_s = ds_map_create();
ds_map_add(_s, "anim",  argument1);
ds_map_add(_s, "x",     argument2);
ds_map_add(_s, "y",     argument3);
ds_map_add(_s, "steps", argument4);
ds_list_add(argument0.shots, _s);
