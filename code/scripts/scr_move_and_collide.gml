/// scr_move_and_collide  (GameMaker: Studio 1.4)
// Axis separated collision against obj_ground.
// Operates on the calling instance: x, y, hsp, vsp -> on_ground.
// ============================================================================
var _hsp, _vsp, _step, _on;
_hsp = hsp;
_vsp = vsp;
_on  = false;

// ---- horizontal ----------------------------------------------------------
if (_hsp != 0) {
    x += _hsp;
    if (place_meeting(x, y, obj_ground)) {
        _step = sign(_hsp);
        // walk back out of the solid, one pixel at a time (max 32 steps)
        var _i;
        _i = 0;
        while (place_meeting(x, y, obj_ground) && _i < 32) {
            x -= _step;
            _i += 1;
        }
        hsp = 0;
    }
}

// ---- vertical ------------------------------------------------------------
if (_vsp != 0) {
    y += _vsp;
    if (place_meeting(x, y, obj_ground)) {
        _step = sign(_vsp);
        var _j;
        _j = 0;
        while (place_meeting(x, y, obj_ground) && _j < 32) {
            y -= _step;
            _j += 1;
        }
        if (_vsp > 0) _on = true;
        vsp = 0;
    }
}

// ---- "standing on" probe: one pixel below the feet -----------------------
if (!_on && place_meeting(x, y + 1, obj_ground)) _on = true;

on_ground = _on;
