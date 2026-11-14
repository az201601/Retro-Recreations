/// scr_pl_wall(x)
// Called by obj_player. x = screen position of the player's left or right edge.
// Returns true if that edge is inside a solid block, anywhere between the head and just above the feet.
if (p_y < 1 || p_y > 255) return false;
var c = (argument0 + stage.lv_cam_x) div 16;
if (c < 0 || c > 127) return false;
var r0 = max(p_y - p_h, 0) div 16;              // row of the head
var r1 = min(((p_y + 15) div 16) - 1, 14);      // row just above the one the feet stand on
var r;
for (r = r0; r <= r1; r += 1)
{
    if (real(string_char_at(stage.lv_map[r], c + 1)) >= 2) return true;
}
return false;
