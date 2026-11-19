/// scr_game_state_step(state)
// GML equivalent shell for the ROM dispatcher at $C54E.
// The ROM reads a little-endian handler address from the inline table after
// the JSR call site. Boot call site $D07C table starts at $D081:
//   state $00 -> $D0C3 (boot entry), $01 -> $D0D7, $02 -> $D0E6,
//   $03 -> $D0F8, $04/$06 -> $D139, $05 -> $D102, $07 -> $D120,
//   $08 -> $D12F, $09 -> $D0CD.
// Bodies are filled in as each handler is decoded; unknown states idle here
// rather than inventing behaviour.

switch (argument0) {
    case 0:
        // ROM $D0C3: LDY #$01; JSR $F001 with inline data $D2 $F2; JMP $D095.
        // $F001 record format not decoded yet (M1 next task).
        break;
    default:
        // Handler not yet transcribed. Keep frame timing alive; do not guess.
        break;
}
