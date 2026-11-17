/// scr_player_hit  (GameMaker: Studio 1.4)
// @param dmg   hearts removed
// @param from_x  x of the damage source (knockback direction)
// ============================================================================
var _dmg, _fx;
_dmg = argument0;
_fx  = argument1;

if (invuln > 0) exit;

hp     = hp - _dmg;
invuln = 90;
stun   = 30;

if (x < _fx) hsp = -2.0; else hsp = 2.0;
vsp = -2.4;

if (hp <= 0) scr_player_die();
