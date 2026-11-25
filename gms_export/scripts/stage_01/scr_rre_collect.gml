/// scr_rre_collect()
/// Rescue Ranger Emblem collectible.
/// Attach to obj_rre Collision with obj_player.

global.rre_count += 1;
// TODO: play SFX, spawn sparkle effect
instance_destroy();
