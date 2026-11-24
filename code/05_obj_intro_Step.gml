// obj_intro Step event — hold the completed title image; Enter/Space continues.

// Allow the player to skip the intro at any point.
if (keyboard_check_pressed(vk_enter) || keyboard_check_pressed(vk_space)) {
    audio_stop_sound(MUS_intro);
    room_goto(rm_title);
    exit;
}

// The captured sequence is non-looping. Freeze on its final title frame.
if (image_index >= image_number - 1) {
    image_index = image_number - 1;
    image_speed = 0;
}
