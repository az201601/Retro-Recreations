/// Create
t = 0;                          // 本场景第几帧 (第 1 帧 = Mesen 开机后的第 166 帧)
fade = 699;                     // 从第几帧开始淡出，按键跳过时会提前
wall = bg_spotlight_wall1;
x = 192;                        // 聚光灯圆心
y = -62;

/// Step
t += 1;
if (t >= 25 && t < fade)
{
    if (t <= 638 && keyboard_check_pressed(vk_anykey)) fade = t;      // 任意键跳过
    else if (t <= 151) y += 2;
    else if (t <= 247) { x -= 1.375; y -= 1.375; }
    else if (t <= 311) x += 2;
    else if (t <= 359) { x -= 1.375; y += 1.375; }
    else if (t <= 487) x -= 2;
    else if (t == 488) { x += 2; y = 104; wall = bg_spotlight_wall2; audio_play_sound(snd_drumroll, 0, false); }
    else if (t <= 621) x += 2;
    else if (t <= 637) x -= 4;
    else if (t == 638) audio_play_sound(snd_applause, 0, false);
}
if (t == fade + 23) room_goto_next();       // 本场景最后一帧(全黑)，下一帧就是标题画面

/// Draw
var lv, sy, cut;
lv = max(0, t - fade) div 4;    // 淡出亮度：0 正常，1~3 逐级变暗，4 以上全黑
sy = floor(y);
cut = 16 * (sy < 32) + 15 * (sy < 16) + 16 * (sy < 1) + 16 * (sy < -15);   // 聚光灯上边被切掉的行数 (见 README)
if (lv < 4) draw_sprite_part(spr_spotlight, lv, 0, cut, 64, 63 - cut, floor(x) - 32, sy - 31 + cut);
draw_background(wall, 0, 0);    // 砖墙(只有黑色砖缝和剪影，其余透明)盖在聚光灯上
