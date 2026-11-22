// obj_title -- Step event
blink += 1;
if (keyboard_check_pressed(vk_enter) || keyboard_check_pressed(vk_space)
 || keyboard_check_pressed(ord("Z")) || gamepad_button_check_pressed(0, gp_start)) {
    sound_stop(mus_title);
    if (room_exists(rm_charsel)) room_goto(rm_charsel);
    else room_goto(rm_stage);
}
