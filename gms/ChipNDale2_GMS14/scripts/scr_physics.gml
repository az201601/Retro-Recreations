/// scr_physics.gml
/// 平台物理（对应原版 $803F 实体移动：$07AE+=$07BA，$07B4+=$07C0，DEC $07A2）
/// GMS 1.4 无物理引擎，用 AABB + place_meeting 手动碰撞（见 docs/07 §6）

function scr_physics_init() {
    global.gravity = 0.5;      // 重力（像素/帧²，待调）
    global.move_speed = 2;     // 水平速度（待调，对应 $07BA）
    global.jump_speed = -8;    // 跳速（待调）
}

function scr_physics_move(_obj, _hspd, _vspd) {
    // 水平
    if (place_meeting(_obj.x + _hspd, _obj.y, obj_solid)) {
        while (!place_meeting(_obj.x + sign(_hspd), _obj.y, obj_solid)) {
            _obj.x += sign(_hspd);
        }
        _hspd = 0;
    } else {
        _obj.x += _hspd;
    }
    // 垂直
    if (place_meeting(_obj.x, _obj.y + _vspd, obj_solid)) {
        while (!place_meeting(_obj.x, _obj.y + sign(_vspd), obj_solid)) {
            _obj.y += sign(_vspd);
        }
        _vspd = 0;
        _obj.on_ground = true;
    } else {
        _obj.y += _vspd;
        _obj.on_ground = false;
    }
    return [_hspd, _vspd];
}
