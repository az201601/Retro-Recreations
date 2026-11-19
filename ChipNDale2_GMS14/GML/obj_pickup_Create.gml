//=============================================================================
// obj_pickup  --  Create event   (flower = health, star = points)
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
// Paste into the Create event of an object named  obj_pickup.
// Set  kind  to 0 (flower) or 1 (star) in the Creation Code, or just
// place two different objects (obj_flower / obj_star) if that's easier.
//=============================================================================

kind = 0;        // 0 = flower (restores 1 heart), 1 = star (bonus points)
base_y = y;      // remember start height for the bobbing animation
bob_timer = 0;
