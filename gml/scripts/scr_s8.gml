/// scr_s8(byte)
// Interpret a 0-255 value as a signed 6502 byte (-128..127).
var b;
b = argument0 & $FF;
if (b >= $80) b -= $100;
return b;
