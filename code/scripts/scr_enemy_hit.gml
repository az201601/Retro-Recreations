/// scr_enemy_hit  (GameMaker: Studio 1.4)
// Enemy-side damage handling; called with the enemy as self.
//
// @param dmg     hearts/hits removed
// @param from_x  x coordinate of the damage source
// ============================================================================
var _dmg, _fx;
_dmg = argument0;
_fx  = argument1;

hp   = hp - _dmg;
hurt = 20;
if (x < _fx) hsp = -1.6; else hsp = 1.6;
vsp = -1.8;

if (hp <= 0) {
    instance_create(x, y - 8, obj_debris);
    instance_destroy();
}
