if (keyboard_check_pressed(vk_space)) paused = !paused;
if (!paused || keyboard_check_pressed(vk_right)) cursor_frame = min(frame_count-1, cursor_frame+1);
if (paused && keyboard_check_pressed(vk_left)) cursor_frame = max(0, cursor_frame-1);
if (keyboard_check_pressed(ord("R"))) cursor_frame = 0;
