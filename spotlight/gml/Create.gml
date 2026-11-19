room_speed = 60;
texture_set_interpolation(false);
page_count = 30;
for (var p = 0; p < page_count; p += 1) {
    pages[p] = background_add(working_directory + "spot_" + string(p) + ".png", false, false);
}
var f = file_text_open_read(working_directory + "spot_frames.txt");
frame_count = 994;
for (var t = 0; t < frame_count; t += 1) {
    tiles[t] = file_text_read_real(f);
    file_text_readln(f);
}
file_text_close(f);
cursor_frame = -1;
paused = false;
