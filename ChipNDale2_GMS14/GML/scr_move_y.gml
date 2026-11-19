//=============================================================================
// Script name:  scr_move_y
// GameMaker Studio 1.4.1760  |  Chip 'n Dale Rescue Rangers 2 recreation
//-----------------------------------------------------------------------------
// Create a Script resource named  scr_move_y  and paste this in.
// Moves the CALLING instance vertically by argument0 pixels, stopping
// against floors/ceilings. Returns true if a floor/ceiling was hit.
// Uses the calling instance's bbox_*_offset variables (set in Create).
//=============================================================================

var amount = argument0;
if (amount == 0) return false;
var step = sign(amount);
var remaining = abs(amount);
var hit = false;
while (remaining > 0) {
    var move = min(step, remaining);
    var ny = y + move;
    var edge_y = (move > 0) ? (ny + bbox_bottom_offset) : (ny - bbox_top_offset);
    if (scr_rect_solid(x - bbox_left_offset, edge_y, x + bbox_right_offset, edge_y)) {
        hit = true;
        break;
    }
    y = ny;
    remaining -= abs(move);
}
return hit;
