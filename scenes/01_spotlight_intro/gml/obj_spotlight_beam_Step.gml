/// obj_spotlight_beam — Step Event
// ============================================================================
// Exact frame-for-frame recreation of the NES Pre-Title Spotlight Intro:
//   - 8.8 fixed-point spotlight search path across the brick wall (Phase 1)
//   - Seamless off-screen transition to silhouette reveal + drumroll (Phase 2)
//   - Overshoot & snap-back lock onto Chip & Dale's silhouette + brass swell
//   - Authentic 4-step NES hardware palette fade-in / fade-out via image_index
//   - Instant Start-button skip fade-out (Enter / Space / Gamepad Start)
// ============================================================================

// 1. Check for START button skip (matches NES behavior when pressing Start)
var pressed_start = keyboard_check_pressed(vk_enter)
                 || keyboard_check_pressed(vk_space)
                 || gamepad_button_check_pressed(0, gp_start);

if (!skipping && pressed_start && timer < 692) {
    skipping  = true;
    skip_step = 0;
}

// 2. Handle fast NES palette fade-out when skipped (4 frames per palette step)
if (skipping) {
    skip_step += 1;
    if (skip_step < 4) {
        image_index = 1;
    } else if (skip_step < 8) {
        image_index = 2;
    } else if (skip_step < 12) {
        image_index = 3;
    } else {
        visible = false;
    }

    // After 22 frames (matching NES Start-skip delay), stop intro SFX and go to Title Screen
    if (skip_step >= 22) {
        audio_stop_sound(snd_spotlight_drumroll);
        audio_stop_sound(snd_spotlight_brass_swell);
        if (room_exists(room_next(room))) {
            room_goto_next();
        }
    }
    exit;
}

// 3. Hardware NES 4-step palette fade-in (t = 0..12)
if (timer < 4) {
    image_index = 3; // [$06, $0F, $0F]
} else if (timer < 8) {
    image_index = 2; // [$16, $0F, $06]
} else if (timer < 12) {
    image_index = 1; // [$26, $06, $16]
} else if (timer < 692) {
    image_index = 0; // [$36, $16, $26] Full brightness
}

// 4. Spotlight motion script (exact NES Bank 6 entity script keyframes)
switch (timer) {
    case 12:
        // Sweep straight down right side of brick wall: (192, -62) -> (192, 192)
        vx_256 = 0;
        vy_256 = 512;   // +2.000 px/frame
        break;

    case 139:
        // Sweep diagonally up-left: (192, 192) -> (60, 60)
        vx_256 = -352;  // -1.375 px/frame ($FFEA in 8.8 fixed-point)
        vy_256 = -352;  // -1.375 px/frame
        break;

    case 235:
        // Sweep horizontally right across upper wall: (60, 60) -> (188, 60)
        vx_256 = 512;   // +2.000 px/frame
        vy_256 = 0;
        break;

    case 299:
        // Sweep diagonally down-left toward center: (188, 60) -> (122, 126)
        vx_256 = -352;  // -1.375 px/frame
        vy_256 = 352;   // +1.375 px/frame ($0160 in 8.8 fixed-point)
        break;

    case 347:
        // Sweep left and exit off-screen left: (122, 126) -> (-134, 126)
        vx_256 = -512;  // -2.000 px/frame
        vy_256 = 0;
        break;

    case 475:
        // Reposition off-screen left at Y = 104 and reverse direction right
        pos_x  = -132;
        sub_x  = 0;
        pos_y  = 104;
        sub_y  = 0;
        vx_256 = 512;   // +2.000 px/frame
        vy_256 = 0;
        break;

    case 477:
        // Phase 2 begins while spotlight is still off-screen left:
        // Switch nametable to show Chip & Dale silhouette + play snare drumroll!
        tile_layer_show(-10);
        if (instance_exists(obj_chip_dale_silhouette)) {
            obj_chip_dale_silhouette.visible = true;
        }
        audio_play_sound(snd_spotlight_drumroll, 10, false);
        break;

    case 609:
        // Spotlight overshoots silhouette at X = 134, then snaps rapidly left!
        vx_256 = -1024; // -4.000 px/frame
        vy_256 = 0;
        break;

    case 625:
        // Lock dead-center onto Chip & Dale's silhouette at (70, 105)!
        vx_256 = 0;
        vy_256 = 0;
        break;

    case 627:
        // Play dramatic brass swell right after locking onto silhouette!
        audio_play_sound(snd_spotlight_brass_swell, 10, false);
        break;
}

// 5. Update screen position BEFORE integrating velocity so OAM 1-frame latch matches NES!
x = pos_x;
y = pos_y + 1;

// 6. Integrate 8.8 fixed-point velocity (matches NES 6502 two's complement math)
if (timer >= 12 && timer != 475) {
    var total_x = (pos_x * 256) + sub_x + vx_256;
    pos_x = floor(total_x / 256);
    sub_x = total_x - (pos_x * 256);

    var total_y = (pos_y * 256) + sub_y + vy_256;
    pos_y = floor(total_y / 256);
    sub_y = total_y - (pos_y * 256);
}

// 7. Hardware NES 4-step palette fade-out at end of scene (t = 692..710)
if (timer >= 692 && timer < 696) {
    image_index = 1;
} else if (timer >= 696 && timer < 700) {
    image_index = 2;
} else if (timer >= 700 && timer < 704) {
    image_index = 3;
} else if (timer >= 704) {
    visible = false;
}

// 8. Advance timer and transition cleanly to Title Screen room at t = 712 (NES Frame 888)
timer += 1;
if (timer >= 712) {
    if (room_exists(room_next(room))) {
        room_goto_next();
    }
}
