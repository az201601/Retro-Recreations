// obj_intro Create event — Chip 'n Dale Rescue Rangers 2 opening.
// Resource requirements: SPR_spotlight_intro, MUS_intro.
// The sprite contains emulator-captured NES frames 1..900 in order.

image_speed = 1;          // one source frame per GMS game step (room speed 60)
image_index = 0;

// Play the already-extracted opening audio once, synchronized from room start.
audio_play_sound(MUS_intro, 1, false);
