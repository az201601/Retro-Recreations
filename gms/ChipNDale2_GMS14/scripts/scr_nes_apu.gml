/// scr_nes_apu.gml
/// NES APU 抽象层 -> GMS 声音（占位，后续接解码数据）
/// 对应原版：$4000-$400F 脉冲/三角/噪声，$4015 状态，$4017 帧计数器（$C0）
/// 音乐调度 $8200（7 轨跳表 $8220），序列器 $81C2（$F8-$FB），脉冲输出 $812D/$8154/$8193
///
/// 原型阶段：用 GMS sound_play 占位。完整版：解码银行 5 音乐数据后转 ogg 或 GML 序列器。

function scr_nes_apu_init() {
    global.apu_music = 0;      // $F0（0=停，$79+=轨号）
    global.apu_seq_enable = 0; // $F8
    global.apu_seq_dir = 0;    // $F9
    global.apu_seq_a = 0;      // $FA
    global.apu_seq_b = 0;      // $FB
    global.apu_sfx_request = 0;// $F1 低 4 位
    global.apu_music_snd = -1; // 当前音乐 sound 索引（GMS）
}

function scr_nes_apu_music_play(_track) {
    // 对应 $8200: ORA #$80 STA $F0 ... JMP ($00F3)（$8220 跳表）
    // _track: 0=停，1-7=轨号（$8220 7 项）
    global.apu_music = _track;
    if (_track == 0) {
        if (global.apu_music_snd != -1) sound_stop(global.apu_music_snd);
        global.apu_music_snd = -1;
    } else {
        // TODO：按轨号播放对应 ogg（mus_title / mus_stage1 ...）
        // 原型占位：无声
    }
}

function scr_nes_apu_sfx(_id) {
    // 对应 $80A9 音效分发（$80E5 跳表 6 项）
    // _id: 0-5
    global.apu_sfx_request = _id;
    // TODO：按 _id 播放占位音效（sfx_jump / sfx_throw / sfx_hit ...）
    switch (_id) {
        case 0: /* 跳 */ break;
        case 1: /* 扔橡子 */ break;
        case 2: /* 命中 */ break;
        case 3: /* 拾取 */ break;
        case 4: /* 受伤 */ break;
        case 5: /* 过关 */ break;
    }
}

function scr_nes_apu_tick() {
    // 对应 $81C2 序列器 tick（每帧调用）
    if (global.apu_seq_enable == 0) exit;
    global.apu_seq_a++;
    if (global.apu_seq_a >= 4) {
        global.apu_seq_a = 0;
        global.apu_seq_b++;
        if (global.apu_seq_b >= 16) {
            global.apu_seq_b = 0;
            if (global.apu_seq_dir == 0) global.apu_seq_enable = 0;
        }
    }
    // TODO：按 ($F8-$FB) 推进音符，写脉冲寄存器（GMS 侧：触发音高）
}
