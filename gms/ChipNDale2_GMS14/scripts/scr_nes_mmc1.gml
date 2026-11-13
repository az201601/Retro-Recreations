/// scr_nes_mmc1.gml
/// MMC1 兼容层（参考/测试用，不参与实际运行）
/// 对应原版：$C272 控制字 $1E / $C298 CHR 切换 / $C2C5 PRG 切换
/// GMS 无需模拟银行切换（资源常驻），此层仅记录原版银行号序列用于对照验证。
///
/// 控制字 $1E = 垂直镜像 + 16KB PRG @ $8000 + CHR 4KB×2（见 docs/01 §4）

function scr_nes_mmc1_init() {
    global.mmc1_ctrl = $1E;
    global.mmc1_prg = 6;   // $26（当前 PRG 银行，NMI 切 6）
    global.mmc1_chr0 = 31; // $1D
    global.mmc1_chr1 = 31; // $1E
    global.mmc1_busy = 0;  // $27
    global.mmc1_log = ds_list_create(); // 银行切换日志（调试）
}

function scr_nes_mmc1_set_prg(_bank) {
    // 对应 $C2C5: CMP $26 / BEQ 返回 / STA $26 / 5×STA $EFFF
    if (_bank == global.mmc1_prg) exit;
    global.mmc1_prg = _bank;
    ds_list_add(global.mmc1_log, "PRG->" + string(_bank));
    // GMS：无需实际切换（精灵/背景常驻）
}

function scr_nes_mmc1_set_chr(_chr0, _chr1) {
    // 对应 $C298: X-> $BFFF（CHR0），Y-> $DFFF（CHR1）
    global.mmc1_chr0 = _chr0;
    global.mmc1_chr1 = _chr1;
    ds_list_add(global.mmc1_log, "CHR->" + string(_chr0) + "," + string(_chr1));
    // GMS：切换精灵集（背景集/精灵集）——原型阶段记录即可
    global.ppu_chr0 = _chr0;
    global.ppu_chr1 = _chr1;
}
