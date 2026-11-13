/// scr_game_state.gml
/// 游戏状态机（对应原版 $40 + $D610 表 + $D63D 加载器 + $C54E 分发器）
/// 状态表（$D610）：0=$D719 1=$D738 2=$D785 3=$D8A0 4=$D8A0 5=$D813 6=$D8A0 7=$D855 8=$D871 9=$D705
/// FCEUX 验证（docs/09 §7）：1=标题(31/29) 2=过场(30/31) 3=剧情(24/25→31/14) 4=第一关开始(15/0)
/// 状态头 20 字节（见 docs/03 §6）——GMS 侧用房间/对象代替，此脚本只管状态流转。

function scr_game_state_init() {
    global.state = 0; // $40
    global.state_prev = -1;
}

function scr_game_state_set(_s) {
    if (_s == global.state) exit;
    global.state_prev = global.state;
    global.state = _s;
    // 对应 $D63D：加载状态头（CHR 银行、调色板、滚动、OAM 初始）
    // 原型：按状态切房间
    switch (_s) {
        case 0: room_goto(rm_title); break;   // 标题（CHR 31/31）
        case 1: room_goto(rm_title); break;   // 标题（CHR 31/29，FCEUX 帧356）
        case 2: room_goto(rm_title); break;   // 过场（CHR 30/31，FCEUX 帧864）
        case 3: room_goto(rm_title); break;   // 剧情（CHR 24/25→31/14，FCEUX 帧1224）
        case 4: room_goto(rm_stage1); break;  // 第一关开始（CHR 15/0，FCEUX 帧10810）
        case 9: room_goto(rm_title); break;   // Logo
        case 5: case 6: case 7: case 8:
            room_goto(rm_stage1); break;      // 游戏（原型只有第一关）
    }
}

function scr_game_state_tick() {
    // 对应 $C54E 分发（每帧在 obj_game Step 中调用）
    // 原型：状态内逻辑在各对象 Step 中实现，此处仅处理全局流转
    switch (global.state) {
        case 0: // 标题：按 Start 进状态 1
            if (joy_new_pressed(3)) scr_game_state_set(1);
            break;
        case 1: // 标题：按 Start 进状态 2
            if (joy_new_pressed(3)) scr_game_state_set(2);
            break;
        case 2: // 过场：按 Start 进状态 3
            if (joy_new_pressed(3)) scr_game_state_set(3);
            break;
        case 3: // 剧情：按 Start 进状态 4（第一关）
            if (joy_new_pressed(3)) scr_game_state_set(4);
            break;
        case 4: case 5: case 6: case 7: case 8:
            // 游戏中：过关/死亡由 obj_player 触发（TODO）
            break;
    }
}
