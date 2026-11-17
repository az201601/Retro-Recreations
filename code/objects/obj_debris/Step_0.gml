/// obj_debris - Step
// ============================================================================
if (global.game_state != "play") exit;

vsp += global.GRAVITY * 0.7;
x   += hsp;
y   += vsp;
image_angle += 8;
life -= 1;
if (life <= 0) instance_destroy();
