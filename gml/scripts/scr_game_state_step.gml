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
        // ROM $D0D7: sound request $7F, spawn script $F2DB (second screen).
        // Decoded script timing (docs/06_screens_sequence.md):
        //   spawn 3 linked children, movement phases of 128/96/64/48/128
        //   frames, SOUND $74, 134+16 frames, SOUND $73, WAIT 60,
        //   then state 2. Any pressed button skips to state 2 immediately.
        // TODO M1: run this on the script-VM timing model once the state-1
        // graphics (palettes/nametables/CHR banks 31+29) are extracted.
        break;
    default:
        // Handler not yet transcribed. Keep frame timing alive; do not guess.
        break;
}
