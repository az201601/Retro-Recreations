/// scr_nes_ppu.gml
/// NES PPU 抽象层 -> GMS 绘制
/// 对应原版：$2000 PPUCTRL / $2001 PPUMASK / $2005 滚动 / $2006/$2007 上传 / $3F00 调色板
/// GMS 策略：背景离线整图 + 精灵实例 + 视图滚动（见 docs/07）

function scr_nes_ppu_init() {
    global.ppu_ctrl = $08;   // $29 影子（对应 $C106: LDA #$08）
    global.ppu_mask = $1E;   // $2A 影子（对应 $C106: LDA #$1E）
    global.ppu_scroll_x = 0; // $10
    global.ppu_scroll_y = 0; // $16
    global.ppu_nametable = 0;// $13/$19
    global.ppu_chr0 = 31;    // $1D（CHR0 银行，标题默认字体）
    global.ppu_chr1 = 31;    // $1E（CHR1 银行）
    global.ppu_chr0_b = 31;  // $1F
    global.ppu_chr1_b = 0;   // $20
    global.ppu_sprite_size = 8; // $28（8 或 16）
    global.ppu_palette = ds_list_create(); // $058E（32 色，NES 索引 0-63）
    for (var i = 0; i < 32; i++) ds_list_add(global.ppu_palette, 0);
    global.ppu_chr_queue = ds_queue_create(); // $053A 队列（[hi,lo,count,data...]）
    global.ppu_busy = 0;     // $2B
}

function scr_nes_ppu_set_ctrl(_v) {
    global.ppu_ctrl = _v;
    // GMS 无寄存器，记录即可；精灵大小/图案表选择在绘制时查此值
    if ((_v & $20) != 0) global.ppu_sprite_size = 16; else global.ppu_sprite_size = 8;
}

function scr_nes_ppu_set_mask(_v) {
    global.ppu_mask = _v;
    // bit3（$08）背景使能，bit4（$10）精灵使能
    global.ppu_bg_enabled = ((_v & $08) != 0);
    global.ppu_spr_enabled = ((_v & $10) != 0);
}

function scr_nes_ppu_set_scroll(_x, _y) {
    global.ppu_scroll_x = _x;
    global.ppu_scroll_y = _y;
    // GMS 视图在 obj_camera 中跟随（view_xview/view_yview）
}

function scr_nes_ppu_set_palette(_idx, _nes_color) {
    // _nes_color: NES 调色板索引 0-63（对应 $058E）
    if (_idx >= 0 && _idx < 32) ds_list_set(global.ppu_palette, _idx, _nes_color);
}

function scr_nes_ppu_chr_enqueue(_ppu_addr, _data_array) {
    // 对应 $C34F 队列：[hi, lo, count, data...]
    // _ppu_addr: $0000-$3FFF，_data_array: GML 数组
    var _hi = (_ppu_addr >> 8) & $FF;
    var _lo = _ppu_addr & $FF;
    ds_queue_enqueue(global.ppu_chr_queue, _hi);
    ds_queue_enqueue(global.ppu_chr_queue, _lo);
    ds_queue_enqueue(global.ppu_chr_queue, array_length(_data_array));
    for (var i = 0; i < array_length(_data_array); i++) {
        ds_queue_enqueue(global.ppu_chr_queue, _data_array[i]);
    }
}

function scr_nes_ppu_chr_process(_max_per_frame) {
    // 对应 NMI 中的 JSR $C34F（每帧限量，避免卡顿）
    // GMS 无 CHR RAM，实际绘制用精灵/背景资源；此队列仅作兼容/调试记录
    var _n = 0;
    while (!ds_queue_empty(global.ppu_chr_queue) && _n < _max_per_frame) {
        var _hi = ds_queue_dequeue(global.ppu_chr_queue);
        var _lo = ds_queue_dequeue(global.ppu_chr_queue);
        var _count = ds_queue_dequeue(global.ppu_chr_queue);
        for (var i = 0; i < _count; i++) {
            var _b = ds_queue_dequeue(global.ppu_chr_queue);
            // TODO：按 (_hi<<8)|_lo 更新精灵/背景资源（原型阶段跳过）
            _lo = (_lo + 1) & $FF;
            if (_lo == 0) _hi = (_hi + 1) & $FF;
        }
        _n++;
    }
}

function scr_nes_ppu_draw_background(_bg_sprite) {
    // 背景绘制：离线整图（见 docs/07 §2）
    // _bg_sprite: 已渲染的整关背景精灵（256×关卡高）
    if (global.ppu_bg_enabled) {
        draw_sprite(_bg_sprite, 0, -global.ppu_scroll_x, -global.ppu_scroll_y);
    }
}
