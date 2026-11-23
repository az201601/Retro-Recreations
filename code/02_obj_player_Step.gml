// ============================================================
// obj_player 的 Step 事件（每帧执行一次）
// 在 GMS 中：双击 obj_player → 选择事件 → Add Event → Step → Step
// （注意选 "Step"，不是 Begin Step / End Step）
// 然后把下面全部内容复制粘贴到代码窗口里
// ============================================================

// ---------- 1. 落地检测（先做，下蹲判断要用） ----------
onground = place_meeting(x, y + 1, obj_solid);

// ---------- 2. 下蹲判断 ----------
// 按住 ↓ 且站在地上 = 下蹲（原版特性：下蹲时不能走动）
var crouch;
crouch = keyboard_check(vk_down) && onground;

// ---------- 3. 左右移动 ----------
var h;
h = 0;
if (keyboard_check(vk_right)) h = h + 1;   // 按住 →
if (keyboard_check(vk_left))  h = h - 1;   // 按住 ←

if (h != 0 && !crouch) {
    // 先试着往前走，撞到实心物就不走（防止穿墙）
    if (!place_meeting(x + h * movespd, y, obj_solid)) {
        x = x + h * movespd;
    }
    face = h;   // 记住朝向
}

// ---------- 4. 跳跃 ----------
if (keyboard_check_pressed(vk_space) && onground) {
    fallspd = jumpv;    // 给一个向上的初速度
    y = y - 1;          // 先抬离地面 1 像素
    onground = false;
    crouch = false;
}

// ---------- 5. 重力与垂直移动 ----------
if (onground && fallspd >= 0) {
    fallspd = 0;        // 站稳：不再下落
} else {
    fallspd = fallspd + grav;               // 加重力
    if (fallspd > maxfall) fallspd = maxfall; // 限速

    if (place_meeting(x, y + fallspd, obj_solid)) {
        // 这一帧会撞进实心物：一点点挪到贴住表面为止
        while (!place_meeting(x, y + sign(fallspd), obj_solid)) {
            y = y + sign(fallspd);
        }
        if (fallspd > 0) onground = true;   // 是向下撞的 = 落地
        fallspd = 0;
    } else {
        y = y + fallspd;    // 没撞到：正常移动
    }
}

// ---------- 6. 动画切换 ----------
if (!onground) {
    // 跳跃中：按速度挑姿势（0=起跳 1=上升 2=顶点 3/4=下落）
    sprite_index = SPR_chip_jump;
    image_speed  = 0;
    if (fallspd < -4)      image_index = 0;
    else if (fallspd < 0)  image_index = 1;
    else if (fallspd < 2)  image_index = 2;
    else if (fallspd < 5)  image_index = 3;
    else                   image_index = 4;
} else if (crouch) {
    // 下蹲（静态单帧）
    sprite_index = SPR_chip_crouch;
    image_speed  = 0;
    image_index  = 0;
} else if (h != 0) {
    // 走路：循环播放 3 帧
    sprite_index = SPR_chip_walk;
    image_speed  = 0.3;    // 动画速度，想更快改成 0.4~0.5
} else {
    // 站立
    sprite_index = SPR_chip_idle;
    image_speed  = 0;
    image_index  = 0;
}

// ---------- 7. 左右翻转 ----------
if (face < 0) image_xscale = -1;   // 向左：镜像
else          image_xscale = 1;    // 向右：正常
