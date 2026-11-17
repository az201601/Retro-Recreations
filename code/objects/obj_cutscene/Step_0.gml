/// obj_cutscene - Step
// ============================================================================
if (done) exit;
if (ds_list_size(shots) == 0) { done = true; exit; }

var _s;
_s = ds_list_find_value(shots, cur);
if (_s == -1) { done = true; exit; }

// first step of a shot: switch the sprite
if (t == 0) {
    x = _s[? "x"];
    y = _s[? "y"];
    scr_anim_set(_s[? "anim"]);
}

t += 1;
scr_anim_update();

if (t >= _s[? "steps"]) {
    t   = 0;
    cur += 1;
    if (cur >= ds_list_size(shots)) done = true;
}

// START skips the rest of the scene
if (global.IN[? "start_p"]) done = true;
