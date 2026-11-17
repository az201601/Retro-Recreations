/// obj_crate - Draw
// ============================================================================
if (state == "carried" || state == "thrown") {
    draw_sprite_ext(sprite_index, image_index, x, y,
                    image_xscale, image_yscale, image_angle, c_white, 1);
} else {
    draw_self();
}
