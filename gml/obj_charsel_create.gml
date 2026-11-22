// obj_charsel -- Create event (room: rm_charsel)
// Background art: assets/ui/character_select.png as bg_charsel.
// Music: audio/character_select.ogg as mus_charsel.
if (!audio_is_playing(mus_charsel)) sound_loop(mus_charsel);
choice = 0;   // 0 = Chip, 1 = Dale
