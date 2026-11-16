/// scr_pl_wall(x)
// Called by obj_player. x = screen position of the player's left or right edge.
// Returns true if that edge is inside a solid block, anywhere between the head and just above the feet.
// p_wc, p_wr then hold the column and row of the topmost such block.
if (p_y < 1 || p_y > 255) return false;
var c = (argument0 + stage.lv_cam_x) div 16;
if (c < 0 || c > 127) return false;
var cy = stage.lv_cam_y;                        // 0 except in the kitchen
var r0 = (max(p_y - p_h, 0) + cy) div 16;       // row of the head
var r1 = ((p_y + cy + 15) div 16) - 1;          // row just above the one the feet stand on
r1 = min(r1, (cy + 239) div 16, stage.lv_rows - 1);     // (not below the picture)
var r;
for (r = r0; r <= r1; r += 1)
{
    if (stage.lv_kind[r, c] >= 2) { p_wc = c; p_wr = r; return true; }
}
return false;
