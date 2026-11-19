/// obj_nes_core - Create
// Boot sequence equivalent: the ROM clears RAM, initialises mapper/PPU
// shadows and enters the main loop (docs/01_rom_analysis.md). The GMS
// equivalent initialises globals and starts frame counting.
scr_nes_init();
use_accumulator = false; // true = NTSC-exact 16639us accumulator; false = 1 step per Step event (room_speed 60)
if (!use_accumulator) room_speed = 60;
