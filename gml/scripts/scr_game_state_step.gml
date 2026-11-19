/// scr_game_state_step(state)
// GML equivalent shell for the ROM dispatcher at $C54E.
// The ROM reads a little-endian handler address from the inline table after
// the JSR call site. Boot call site $D07C table starts at $D081:
//   state $00 -> $D0C3 (copyright, SKIPPED - see scr_nes_init),
//   $01 -> $D0D7 (second screen), $02 -> $D0E6, $03 -> $D0F8,
//   $04/$06 -> $D139, $05 -> $D102, $07 -> $D120, $08 -> $D12F, $09 -> $D0CD.
// Each state spawns a type-1 script-VM object (docs/05_vm_opcodes.md).
// Bodies are filled in as each screen is decoded; unknown states idle here
// rather than inventing behaviour.

switch (argument0) {
    case 0:
        // ROM $D0C3: spawn script $F2D2 = WAIT 120, WRITE state 1, fade exit.
        // Skipped by project decision - this case should never be entered.
        break;
    case 1:
        // ROM $D0D7: sound request $7F, spawn script $F2DB (docs/06, docs/07).
        // The script moves a spotlight (parent + 3 mirrored children) with
        // velocity phases; any pressed button skips to state 2.
        // Positions are 8.8 fixed point, like the ROM (docs/05).
        // Sound (docs/08_sound_engine.md): the ROM's $7F request is the
        // sound-engine reset/stop, so this screen starts silent; the
        // script's SOUND $74 (frame 464) and SOUND $73 (frame 614) are
        // WAVs rendered from the real bank-6 engine (extracted/sounds/).
        var t;
        t = global.game_state_timer;
        if (t == 0) {
            // Script start: SETX $C0,$00 / SETY $C0,$FF (signed Y = -64)
            global.s1_x = 192 * 256;
            global.s1_y = -64 * 256;
            // $7F = engine reset at $8274: silence anything playing.
            audio_stop_all();
        }
        if (global.pad_pressed != 0 && t < 614) {
            // PADJ in the ROM's $F352 subroutine: skip straight to state 2.
            global.game_state = 2;
            global.game_state_timer = 0;
            break;
        }
        if (t < 128) {
            global.s1_y += 512;                    // SETVY $20 = +2 px/frame
        } else if (t < 224) {
            global.s1_x -= 352;                    // SETVX $EA = -1.375
            global.s1_y -= 352;                    // SETVY $EA
        } else if (t < 288) {
            global.s1_x += 512;                    // SETVX $20
        } else if (t < 336) {
            global.s1_x -= 352;                    // SETVX $EA
            global.s1_y += 352;                    // SETVY $16 = +1.375
        } else if (t < 464) {
            global.s1_x -= 512;                    // SETVX $E0 = -2
        } else if (t < 598) {
            if (t == 464) {
                global.s1_y = 104 * 256;           // SETY $68,$00
                // SOUND $74 here in the script (spotlight whoosh).
                audio_play_sound(snd_74, 10, false);
            }
            global.s1_x += 512;                    // SETVX $20
        } else if (t < 614) {
            global.s1_x -= 1024;                   // SETVX $C0 = -4
        }
        if (t == 614) {
            // SOUND $73 here in the script (second whoosh, at the WAIT).
            // On the NES the SFX channels are independent of the state
            // change, so this is left to ring out into state 2.
            audio_play_sound(snd_73, 10, false);
        }
        // t 614..673: WAIT 60. ROM then fades (20f) into state 2.
        if (t >= 674) {
            global.game_state = 2;
            global.game_state_timer = 0;
        }
        break;
    default:
        // Handler not yet transcribed. Keep frame timing alive; do not guess.
        break;
}
