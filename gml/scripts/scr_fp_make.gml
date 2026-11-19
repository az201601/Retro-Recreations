/// scr_fp_make(pixel, subpixel)
// Build an 8.8 fixed-point value: pixel * 256 + subpixel (subpixel 0-255).
// NES code typically keeps these as separate low/high bytes; one integer
// here keeps the arithmetic identical and exact.
return (argument0 * 256) + (argument1 & $FF);
