// obj_title -- Create event (room: rm_title, 256x240)
// Background art: import assets/ui/title.png as bg_title (assign to the room).
// Music: import audio/title_theme.ogg as mus_title.
if (!audio_is_playing(mus_title)) sound_loop(mus_title);
blink = 0;
