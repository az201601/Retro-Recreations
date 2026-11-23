// ============================================================
// obj_title 的 Step 事件（标题画面：按回车或空格开始游戏）
// 在 GMS 中：创建对象 obj_title（不需要精灵）
// → Add Event → Step → Step，粘贴下面代码
// ============================================================

if (keyboard_check_pressed(vk_enter) || keyboard_check_pressed(vk_space)) {
    room_goto(rm_stage1);   // 进入第 1 关
}
