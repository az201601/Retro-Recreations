// obj_title Step event — 1-player is the only available selection.
// Enter/Space represents Start/A. The next room should be rm_character_select.

if (keyboard_check_pressed(vk_enter) || keyboard_check_pressed(vk_space)) {
    audio_stop_sound(MUS_menu);
    room_goto_next();
}
