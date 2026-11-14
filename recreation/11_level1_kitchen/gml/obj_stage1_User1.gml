/// obj_stage1 : User Defined 1   (one frame of the sound effects; run by End Step)
// Sound effects: 1 pick up, 2 throw, 3 bonus, 4 far throw, 5 landing, 6 the flyer's buzz, 7 the cook
//     throws, 8 an enemy is knocked out, 9 hurt, 10 stunned. Only one plays at a time.
//     A new one stops the one before it 1 frame after its cause and starts 2 frames after its cause.
//     The landing sound is the exception: it stops nothing, and is left out while another effect is playing.
//     All but 4 use the music's 2nd square channel: the music's part is silent meanwhile. 4 is noise only
//     (8 and 9 are both: 8 has the square channel for 17 frames, 9 for 16 of its 24).
//     The buzz is asked for again every 3 or 4 frames while a flyer is about: whatever else starts is cut
//     off by it after 1 to 3 frames, as in the original.
if (lv_fx_wait > 0)
{
    lv_fx_wait -= 1;
    if (lv_fx_wait == 1)
    {
        if (lv_fx_k != 5 && lv_fx_now != 0)
        {
            // A buzz is only stopped during its 2 sounding frames. After those the file is silent, and
            // stopping it would only risk cutting the buzz short if the sound card started it late.
            if (lv_fx_now != 6 || lt < lv_fx_end - 2) audio_stop_sound(lv_fx_inst);
            audio_sound_gain(lv_music_b, 1, 0);
            lv_fx_now = 0;
        }
    }
    else if (!(lv_fx_k == 5 && lv_fx_now != 0 && lv_fx_now != 5 && lt < lv_fx_end))
    {
        if (lv_fx_now != 0) audio_stop_sound(lv_fx_inst);       // (only a landing sound can still be playing here)
        switch (lv_fx_k)
        {
            case 1: lv_fx_inst = audio_play_sound(snd_pick, 20, false);      lv_fx_end = lt + 14; break;
            case 2: lv_fx_inst = audio_play_sound(snd_throw, 20, false);     lv_fx_end = lt + 25; break;
            case 3: lv_fx_inst = audio_play_sound(snd_bonus, 20, false);     lv_fx_end = lt + 53; break;
            case 4: lv_fx_inst = audio_play_sound(snd_throw_far, 20, false); lv_fx_end = lt + 73; break;
            case 5: lv_fx_inst = audio_play_sound(snd_land, 20, false);      lv_fx_end = lt + 6;  break;
            case 6: lv_fx_inst = audio_play_sound(snd_buzz, 20, false);      lv_fx_end = lt + 4;  break;
            case 7: lv_fx_inst = audio_play_sound(snd_cook_throw, 20, false); lv_fx_end = lt + 10; break;
            case 8: lv_fx_inst = audio_play_sound(snd_enemy_hit, 20, false); lv_fx_end = lt + 17; break;
        case 9: lv_fx_inst = audio_play_sound(snd_hurt, 20, false);      lv_fx_end = lt + 24; break;
        case 10: lv_fx_inst = audio_play_sound(snd_stun, 20, false);     lv_fx_end = lt + 97; break;
        }
        lv_fx_now = lv_fx_k;
        if (lv_fx_k == 4) audio_sound_gain(lv_music_b, 1, 0);
        else audio_sound_gain(lv_music_b, 0, 0);
    }
}
if (lv_fx_now == 9 && lt == lv_fx_end - 8) audio_sound_gain(lv_music_b, 1, 0);     // hurt: only noise is left
if (lv_fx_now != 0 && lt >= lv_fx_end)
{
    lv_fx_now = 0;
    audio_sound_gain(lv_music_b, 1, 0);
}
