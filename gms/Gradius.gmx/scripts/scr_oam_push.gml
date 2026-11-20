/// scr_oam_push(slot_cursor, y, sid, attr, x, frame)
// Stages one metasprite slot into global.oam_sh_* ($0200-$02FF) and returns the
// rotated next OAM slot cursor (1..63), matching sub_8AAC's +$C4 (+49 slots) step.

var cur;
cur = argument0;

if (cur <= 0 || cur >= 64) {
    cur = 1;
}

global.oam_sh_y[cur] = floor(argument1);
global.oam_sh_sid[cur] = argument2;
global.oam_sh_attr[cur] = argument3;
global.oam_sh_x[cur] = floor(argument4);
global.oam_sh_frame[cur] = argument5;

cur = (cur + 49) & 63;
if (cur == 0) {
    cur = 1;
}

return cur;
