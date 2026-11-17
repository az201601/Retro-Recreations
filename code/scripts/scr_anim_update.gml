/// scr_anim_update  (GameMaker: Studio 1.4)
// Keeps GameMaker's automatic strip animation inside [0, frames-1] and clamps
// non-looping clips to their last frame.
// Call from the object's End Step (after the state machine chose the anim).
// ============================================================================
if (anim_count <= 0) exit;

if (anim_loop) {
    if (image_index >= anim_count) image_index -= anim_count;
    if (image_index < 0) image_index += anim_count;
} else {
    if (image_index > anim_count - 1) {
        image_index = anim_count - 1;
        image_speed = 0;
    }
}
