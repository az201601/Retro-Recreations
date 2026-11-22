// obj_charsel -- Step event
if (keyboard_check_pressed(vk_left) || keyboard_check_pressed(vk_right)) choice = 1 - choice;
if (keyboard_check_pressed(vk_enter) || keyboard_check_pressed(vk_space)
 || keyboard_check_pressed(ord("Z"))) {
    global.play_dale = (choice == 1);   // Dale recolour can be applied in obj_player_draw
    sound_stop(mus_charsel);
    room_goto(rm_stage);
}
