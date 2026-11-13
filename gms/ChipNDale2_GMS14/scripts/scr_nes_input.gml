/// scr_nes_input.gml
/// NES 手柄 ($4016/$4017) -> GMS 键盘映射
/// 对应原版 $C17C：$38/$39=当前，$36/$37=上一帧，$3C/$3D=新按下（边沿）
/// 位序：bit0=A bit1=B bit2=Select bit3=Start bit4=Up bit5=Down bit6=Left bit7=Right
///
/// 用法（obj_game Step 中每帧调用）：
///   scr_nes_input_update(0); // 手柄1
///   scr_nes_input_update(1); // 手柄2（预留）

function scr_nes_input_init() {
    // 手柄1/2 的当前/上一帧/新按下（8 位掩码）
    global.joy_cur[0] = 0; global.joy_prev[0] = 0; global.joy_new[0] = 0;
    global.joy_cur[1] = 0; global.joy_prev[1] = 0; global.joy_new[1] = 0;
    // 键位（可改）
    global.key_a = ord('Z');       // A：跳/确认
    global.key_b = ord('X');       // B：扔橡子
    global.key_select = vk_shift;  // Select
    global.key_start = vk_enter;   // Start
}

function scr_nes_input_update(_pad) {
    // _pad: 0=手柄1，1=手柄2
    global.joy_prev[_pad] = global.joy_cur[_pad];
    var _cur = 0;
    if (_pad == 0) {
        if (keyboard_check(global.key_a))      _cur |= (1 << 0); // A
        if (keyboard_check(global.key_b))      _cur |= (1 << 1); // B
        if (keyboard_check(global.key_select)) _cur |= (1 << 2); // Select
        if (keyboard_check(global.key_start))  _cur |= (1 << 3); // Start
        if (keyboard_check(vk_up))             _cur |= (1 << 4); // Up
        if (keyboard_check(vk_down))           _cur |= (1 << 5); // Down
        if (keyboard_check(vk_left))           _cur |= (1 << 6); // Left
        if (keyboard_check(vk_right))          _cur |= (1 << 7); // Right
    } else {
        // 手柄2：预留（可接第二键盘 WASD + J/K，或 GMS 手柄扩展）
        if (keyboard_check(ord('J'))) _cur |= (1 << 0);
        if (keyboard_check(ord('K'))) _cur |= (1 << 1);
        if (keyboard_check(ord('W'))) _cur |= (1 << 4);
        if (keyboard_check(ord('S'))) _cur |= (1 << 5);
        if (keyboard_check(ord('A'))) _cur |= (1 << 6);
        if (keyboard_check(ord('D'))) _cur |= (1 << 7);
    }
    global.joy_cur[_pad] = _cur;
    // 边沿：当前 & ~上一（对应 $C1A8: EOR #$FF AND $38）
    global.joy_new[_pad] = _cur & (~global.joy_prev[_pad]);
}

// 便捷查询（手柄1）
function joy_pressed(_bit) { // _bit 0-7
    return (global.joy_cur[0] >> _bit) & 1;
}
function joy_new_pressed(_bit) {
    return (global.joy_new[0] >> _bit) & 1;
}
