/// scr_stage01_collision_at(world_x, world_y)
/// Return 0=empty, 1=one-way platform, 2=solid; uses ROM thresholds.
/// Boxes and actors are not in this static grid; test their objects separately.
var cx, cy;
cx = floor(argument0 / 16);
cy = floor(argument1 / 16);
if (cx < 0 || cx >= 128 || cy < 0 || cy >= 128) return 0;
return ds_grid_get(global.stage01_collision_grid, cx, cy);
