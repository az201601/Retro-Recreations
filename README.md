# Retro-Recreations — 松鼠大战2 (Chip 'n Dale Rescue Rangers 2) GMS 1.4.1760 重制

> 宏伟计划第一站：从全方位反汇编 / 逆向工程开始，用 **GameMaker Studio 1.4.1760** 重制童年经典。
> 本仓库当前只收录《松鼠大战2》美版 NES ROM 的逆向成果与 GMS 工程骨架，后续游戏将按同一流水线推进。

## 快速开始

1. **先读文档**（按顺序）：
   - [`docs/00-roadmap.md`](docs/00-roadmap.md) — 宏伟计划路线图、阶段划分、里程碑
   - [`docs/01-rom-forensics.md`](docs/01-rom-forensics.md) — ROM 取证：iNES 头、MMC1、向量、银行
   - [`docs/02-cpu-memory-map.md`](docs/02-cpu-memory-map.md) — CPU 内存映射、RAM 变量表
   - [`docs/03-fixed-bank-kernel.md`](docs/03-fixed-bank-kernel.md) — 固定银行内核：NMI / 复位 / MMC1 / PPU / 手柄
   - [`docs/04-bank6-game-logic.md`](docs/04-bank6-game-logic.md) — 可切换银行游戏逻辑：实体系统、音乐、音效
   - [`docs/05-data-banks.md`](docs/05-data-banks.md) — 数据银行 0–5：关卡、调色板、CHR 银行表
   - [`docs/06-chr-graphics.md`](docs/06-chr-graphics.md) — CHR 图形：图块格式、银行 15–31 已确认图形、银行 0–14 之谜
   - [`docs/07-gms-mapping.md`](docs/07-gms-mapping.md) — NES → GMS 1.4.1760 映射手册（分辨率、输入、声音、碰撞）
   - [`docs/08-legal-and-ethics.md`](docs/08-legal-and-ethics.md) — 版权与伦理声明（必读）

2. **看反汇编**：
   - [`disassembly/fixed_bank7_C000.asm`](disassembly/fixed_bank7_C000.asm) — 固定银行 `$C000–$FFFF` 线性反汇编（8600 行）
   - [`disassembly/bank6_8000.asm`](disassembly/bank6_8000.asm) — 游戏逻辑银行 `$8000–$BFFF` 线性反汇编（9709 行）
   - 重新生成：`python3 tools/dis6502.py --rom "Chip 'n Dale - Rescue Rangers 2 (USA).nes" --bank 7 --base 0xC000 --out disassembly/fixed_bank7_C000.asm`

3. **跑取证工具**：
   ```bash
   python3 tools/analyze_rom.py --rom "Chip 'n Dale - Rescue Rangers 2 (USA).nes" --out analysis/rom_forensics.md
   python3 tools/dis6502.py --rom "Chip 'n Dale - Rescue Rangers 2 (USA).nes" --trace
   ```

4. **打开 GMS 工程**：
   - 工程目录：[`gms/ChipNDale2_GMS14/`](gms/ChipNDale2_GMS14/)
   - 用 **GameMaker Studio 1.4.1760** 打开 `ChipNDale2_GMS14.project.gmx`
   - 若版本校验报错，先按 [`gms/ChipNDale2_GMS14/README-GMS.md`](gms/ChipNDale2_GMS14/README-GMS.md) 的“新建工程 + 导入脚本”备用方案重建
   - GML 源码同时以独立 `.gml` 文件存放在 `scripts/` 下，可用任意文本编辑器修改后粘贴回 GMS

## ROM 身份（已验证）

| 项目 | 值 |
|---|---|
| 文件 | `Chip 'n Dale - Rescue Rangers 2 (USA).nes` |
| 大小 | 262160 字节（16 头 + 128KB PRG + 128KB CHR） |
| SHA256 | `34ca559b733ed910b0a493a0cb1f5d64e5cd9e7e4796032d986c08079573e047` |
| MD5 | `e78eb3226a9e09113be319fee1a84f4d` |
| iNES | PRG 8×16KB，CHR 16×8KB，Mapper 1 (MMC1)，flags6=`$10` flags7=`$00` |
| CHR 校验 | SHA1 `c49107f8280c56fc3ac72d4e8c80e20b4ed4ad58` / CRC32 `A0C30578` —— 与 NesCartDB 已知正版转储完全一致 |
| PRG 校验 | SHA1 `cc9dcddc871036032d9ed6714f30ae8b2986b1f6` / CRC32 `2F97D456`（NES-DV-0 PRG 修订版） |
| 向量 | NMI=`$C003` RESET=`$FFE0` IRQ=`$FFE0` |
| MMC1 控制字 | `$1E` = 垂直镜像 + 16KB PRG @ `$8000` + CHR 4KB×2（见 `docs/01` 纠正说明） |
| PCB | NES-SLROM-06，MMC1B2，Ricoh PRG/CHR Mask ROM |

> ⚠️ iNES 头里的“水平镜像”位对 MMC1 游戏**无效**，真实镜像由 MMC1 控制字决定（垂直）。头文件位仅为占位。

## 仓库结构

```
Retro-Recreations/
├── Chip 'n Dale - Rescue Rangers 2 (USA).nes   # 原始 ROM（仅供个人逆向参考，勿分发）
├── README.md
├── docs/            # 逆向文档（00–08）
├── tools/
│   ├── dis6502.py       # 6502 反汇编器（递归追踪 + MMC1/PPU/APU 标注）
│   └── analyze_rom.py   # ROM 取证（银行统计、熵、CHR 图块统计）
├── disassembly/     # 线性反汇编输出（.asm）
├── analysis/
│   ├── rom_forensics.md # 取证报告（工具生成）
│   └── chr/             # CHR 图块 PNG（32 个 4KB 银行 + 实验渲染）
└── gms/ChipNDale2_GMS14/  # GMS 1.4.1760 工程
    ├── ChipNDale2_GMS14.project.gmx
    ├── scripts/*.gml    # GML 源码（NES 抽象层 + 游戏状态机）
    ├── objects/*.object.gmx
    ├── rooms/*.room.gmx
    ├── sprites/*.sprite.gmx + images/*.png
    ├── sound/*.sound.gmx + audio/*.wav（占位）
    └── README-GMS.md
```

## 当前进度（里程碑 M0）

- [x] ROM 取证 + 校验和验证
- [x] 6502 反汇编器 + 固定银行 / 游戏逻辑银行线性反汇编
- [x] 复位 / NMI / MMC1 / PPU / 手柄 / 状态机递归追踪
- [x] 10 个游戏状态表 `$D610` + 20 字节状态头解析
- [x] 实体系统（`$0700` 数组 + `$92B6` 脚本指针 + `$FE` 终止符）初步解析
- [x] 音乐调度（`$8220` 7 轨跳表）+ 脉冲通道输出（`$812D/$8154/$8193`）初步解析
- [x] CHR 银行 15–31 图形提取（标题 Logo、字体、背景、Chip 精灵已确认）
- [ ] CHR 银行 0–14 之谜（精灵银行 12/14 呈噪声，见 `docs/06` 开放问题）
- [ ] 关卡数据（银行 0–2 图块地图）完整解码
- [ ] 音乐数据（银行 5 指针表）完整解码 + GMS 音频转换
- [ ] GMS 可玩原型（标题 → 第一关）

## 工具链要求

- Python 3.11+（仅标准库，无第三方依赖）
- GameMaker Studio **1.4.1760**（Windows，官方旧版；GMS2 不兼容 `.gmx` 格式）
- （可选）FCEUX / Mesen / BizHawk 用于动态验证（断点、PPU 查看器、CHR 查看器）

## 免责

本项目为个人学习 / 怀旧重制目的的逆向工程记录。原游戏版权归 Capcom / Disney 所有。
仓库中的 ROM 仅供本地分析参考，**请勿分发**。重制时请勿直接分发原版美术 / 音乐素材，
建议重绘或获得授权。详见 [`docs/08-legal-and-ethics.md`](docs/08-legal-and-ethics.md)。
