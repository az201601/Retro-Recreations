//=============================================================================
// Script name:  scr_move_x
// GameMaker Studio 1.4.1760  |  Chip 'n Dale Rescue Rangers 2 recreation
//-----------------------------------------------------------------------------
// Create a Script resource named  scr_move_x  and paste this in.
// Moves the CALLING instance horizontally by argument0 pixels, stopping
// against solid tiles. Returns true if a wall was hit.
// Uses the calling instance's bbox_*_offset variables (set in Create).
//=============================================================================

var amount = argument0;
if (amount == 0) return false;
var step = sign(amount);
var remaining = abs(amount);
var hit = false;
while (remaining > 0) {
    var move = min(step, remaining); // step at most 1px, never overshoot
    var nx = x + move;
    var edge_x = (move > 0) ? (nx + bbox_right_offset) : (nx - bbox_left_offset);
    if (scr_rect_solid(edge_x, y - bbox_top_offset, edge_x, y + bbox_bottom_offset)) {
        hit = true;
        break;
    }
    x = nx;
    remaining -= abs(move);
}
return hit;
