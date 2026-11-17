/// obj_player - Draw
// Blink while invulnerable (same cadence as the NES flicker).
// ============================================================================
if (invuln > 0) {
    if ((invuln div 3) mod 2 == 0) exit;   // skip drawing on these frames
}
draw_self();
