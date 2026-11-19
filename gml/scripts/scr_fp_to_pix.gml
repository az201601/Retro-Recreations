/// scr_fp_to_pix(value)
// Convert an 8.8 fixed-point value to whole pixels.
// Intended for non-negative world/screen coordinates (the common NES case
// of high-byte = pixel). For signed motion use scr_s8()/velocity code paths.
return floor(argument0 / 256);
