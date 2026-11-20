//=============================================================================
// scr_spot_pattern.gml
// Chip 'n Dale Rescue Rangers 2 recreation  |  GameMaker Studio 1.4.1760
//-----------------------------------------------------------------------------
// WHAT THIS IS
//   A tiny helper that sums a repeating integer pattern.
//
// WHY IT EXISTS
//   The spotlight's diagonal drift on the NES is not a constant speed like
//   1.375 px/step. The ROM adds an exact repeating sequence of 1 and 2 pixel
//   steps:   [-1,-2,-1,-1,-2,-1,-1,-2]   (which averages -1.375).
//
//   If you model this with a float accumulator (x -= 1.375) you get drift and
//   the disk slowly desyncs from the wall it is supposed to reveal. Summing the
//   integer pattern instead keeps the path bit-exact forever.
//
// HOW TO USE IT
//   Create a Script resource named  scr_spot_pattern  and paste this in.
//
//   var oy = scr_spot_pattern(global.SPOT_DIAG_Y, frame - 316);
//   disk_y = 159 + oy;
//
//   pattern  an 8-entry array of integers (ds_list also works)
//   n        how many steps to sum (0 or more)
//   returns  the sum of the first n entries, wrapping the pattern
//=============================================================================

/// scr_spot_pattern(pattern, n)
var pattern, n, whole, part, acc, i, plen;

pattern = argument0;
n       = argument1;

plen  = array_length_1d(pattern);
whole = floor(n / plen);
part  = n - whole * plen;

// One full cycle is always the same sum, so multiply instead of looping.
acc = 0;
for (i = 0; i < plen; i += 1) {
    acc += pattern[i];
}
acc = whole * acc;

// Then add the leftover partial cycle.
for (i = 0; i < part; i += 1) {
    acc += pattern[i];
}

return acc;
