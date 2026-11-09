/// scr_approach(value, target, amount)
var v = argument0;
var t = argument1;
var a = argument2;
if (v < t) return min(v + a, t);
if (v > t) return max(v - a, t);
return v;
