/// scr_string_split_vals(str) -> array of number strings split on commas
// GMS 1.4 has no string_split; this returns a fixed-size array.
var s, out, i, cur, n;
s = argument0;
for (i = 0; i < 64; i += 1) out[i] = "0";
n = 0;
cur = "";
for (i = 1; i <= string_length(s); i += 1) {
    var ch;
    ch = string_char_at(s, i);
    if (ch == ",") {
        out[n] = cur; n += 1; cur = "";
    } else {
        cur = cur + ch;
    }
}
out[n] = cur;
return out;
