/// scr_stage01_hex_byte(row, column) -> ROM metatile byte
/// Hex string parser compatible with GameMaker Studio 1.4.
var digits, hi, lo;
digits = "0123456789abcdef";
hi = string_pos(string_char_at(argument0, argument1 * 2 + 1), digits) - 1;
lo = string_pos(string_char_at(argument0, argument1 * 2 + 2), digits) - 1;
return hi * 16 + lo;
