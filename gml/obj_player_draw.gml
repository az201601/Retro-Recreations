// obj_player -- Draw event
// The pose sprites were extracted from the NES ROM (assets/sprites/pose_chip_XX.png).
// Import each PNG as a sprite resource named pose_chip_XX (same two digits),
// origin BOTTOM-CENTER.  The table below is the measured NES animation map
// (indices follow poses_meta.json, sorted by how often the pose occurs).
// Faces RIGHT in the source art; facing=-1 flips via draw_sprite_ext.

var spr;
spr = -1;

if (state == "idle") {
    // idle = 00 / 01 (subtle two-frame idle like the NES)
    if ((obj_game.frame div 30) mod 2 == 0) spr = asset_get_index("pose_chip_00");
    else spr = asset_get_index("pose_chip_01");
}
else if (state == "walk") {
    // side-on walk cycle: 06, 07, 12, 13 (4 frames, 8 game frames each)
    switch (anim_frame) {
        case 0: spr = asset_get_index("pose_chip_06"); break;
        case 1: spr = asset_get_index("pose_chip_07"); break;
        case 2: spr = asset_get_index("pose_chip_12"); break;
        case 3: spr = asset_get_index("pose_chip_13"); break;
    }
}
else if (state == "jump") {
    // 18 = rising, 19 = apex, 22 = falling (measured jump arc ~39 frames)
    if (vspeed < -2)      spr = asset_get_index("pose_chip_18");
    else if (vspeed < 1)  spr = asset_get_index("pose_chip_19");
    else                  spr = asset_get_index("pose_chip_22");
}

if (spr == -1) spr = asset_get_index("pose_chip_00");

// blink during invulnerability (hit feedback)
if (invuln > 0 && (invuln mod 4) < 2) exit;

draw_sprite_ext(spr, 0, x, y, facing, 1, 0, c_white, 1);
