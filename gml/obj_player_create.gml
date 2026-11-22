// obj_player -- Create event
// Origin of every chip sprite must be set to BOTTOM-CENTER on import
// (x,y = feet position, matching the NES $00C2 Y convention).
hspeed = 0;
vspeed = 0;
on_ground = false;
facing = 1;              // 1 = right, -1 = left
jump_held = 0;
anim_timer = 0;
anim_frame = 0;
state = "idle";          // idle / walk / jump / throw
hearts = global.max_hearts;
invuln = 0;
