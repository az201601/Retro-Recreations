/// break_crate()
// shatters the calling crate into a puff of debris
instance_create(x - 2, y - 4, objSpark);
audio_play_sound(sndBreak, 6, false);
instance_destroy();
