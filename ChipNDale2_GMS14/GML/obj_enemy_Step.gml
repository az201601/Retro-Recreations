//=============================================================================
// obj_enemy  --  Step event   (patrol enemy)
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
// Paste into the Step event of  obj_enemy.
// Walks back and forth, turning at walls and ledges -- like the original.
//=============================================================================

// Gravity
vsp = min(vsp + global.E_GRAVITY, global.E_MAX_FALL);

// Walk; turn around if we hit a wall.
facing = sign(hsp);
if (scr_move_x(hsp)) {
    hsp = -hsp; // reverse direction
    facing = sign(hsp);
}

// Turn around at ledges (don't walk off edges) -- original enemy behaviour.
if (on_ground) {
    var ahead_x = x + facing * (bbox_right_offset + 2);
    var below_y = y + bbox_bottom_offset + 2;
    if (!scr_tile_solid_at(ahead_x, below_y)) {
        hsp = -hsp;
        facing = sign(hsp);
    }
}

// Vertical movement
var hit_floor = scr_move_y(vsp);
on_ground = hit_floor and vsp > 0;
if (on_ground) vsp = 0;

// Animation (2 frames, every E_WALK_ANIM steps)
anim_timer += 1;
if (anim_timer >= global.P_ENEMY_ANIM) {
    anim_timer = 0;
    anim_frame = 1 - anim_frame;
}
image_index = anim_frame;
image_xscale = facing;
