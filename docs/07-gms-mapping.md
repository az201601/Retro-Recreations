# 07 — NES → GMS 1.4.1760 映射手册

> 目标引擎：**GameMaker Studio 1.4.1760**（Windows 旧版）。GMS2 不兼容 `.gmx`，请勿用 GMS2 打开。
> 工程骨架：`gms/ChipNDale2_GMS14/`（`.project.gmx` + `scripts/*.gml` + `objects/` + `rooms/` + `sprites/` + `sound/`）。

## 1. 分辨率与房间

| NES | GMS 1.4 |
|---|---|
| PPU 256×240（可见约 256×224，上下 overscan） | 房间 `256×240`，`room_speed=60` |
| 整数缩放 ×3 = 768×720，×4 = 1024×960 | 显示设置整数缩放（`display_set_gui_maximise` 不可用，手动设窗口） |
| 60Hz NMI | `Step` 事件 60Hz（`room_speed=60`，`sleep` 无关） |

房间：`rm_title`（256×240）、`rm_stage1`（256×240，视图 256×224 跟随玩家）。
视图：`view_wview=256`，`view_hview=224`，`view_xport=0`，`view_yport=0`，`view_wport=768`，`view_hport=672`（×3）。

## 2. PPU → GMS 绘制

| NES PPU | GMS 等价 |
|---|---|
| Nametable 32×30 图块（8×8）+ 属性表 | 离线渲染整关背景图（`background`）或 `draw_tile` 循环；垂直镜像布局 |
| 图案表 CHR ROM（4KB×2） | GMS 精灵（每图块一精灵，或合并大精灵 + `image_index`） |
| 调色板 `$3F00` 32 色 | 烘焙进精灵 PNG（当前提取为灰度，需按调色板上色）或 `surface` 调色板替换 |
| 精灵 OAM 64 个（8×8/8×16，优先级） | GMS 实例（每精灵一实例，`depth` 按 OAM 顺序，`$0600` 缓冲 → 实例列表） |
| 滚动 `$2005`（X/Y） | `view_xview/view_yview`（相机对象跟随玩家，钳制关卡边界） |
| `$2000` bit3/4（图案表选择） | 精灵集切换（背景集 / 精灵集） |
| `$2001` 使能位 | `visible` 开关 |

**背景策略**（推荐）：离线把 nametable + CHR + 调色板渲染为整张关卡背景 PNG（宽 256×关卡宽），GMS `background` 平铺关闭，视图滚动。
**精灵策略**：每角色一精灵（多帧），`image_speed` 按原版动画计数（`$07A2`）。

## 3. CPU / MMC1 → GMS

| NES | GMS |
|---|---|
| 6502 @1.79MHz，NMI 驱动 | GMS `Step`（60Hz）+ `Alarm`（帧计数 `$2D/$2F`） |
| MMC1 PRG/CHR 切换 | **无需模拟**：GMS 资源（精灵/背景/声音）常驻内存，按需 `sprite_index` 切换 |
| `$C54E` 间接分发 | `switch (global.state)`（`scr_game_state`） |
| `$C34F` CHR 队列 | 绘制队列（每帧限量，避免卡顿） |

兼容层 `scr_nes_mmc1` 仅作**参考/测试**（记录原版银行号序列，用于对照），不参与实际运行。

## 4. 输入（`$4016/$4017` → 键盘）

原版位序：A / B / Select / Start / Up / Down / Left / Right（`$38` 当前，`$3C` 新按下）。

| NES | GMS 1.4 默认键 | 备注 |
|---|---|---|
| Right/Left/Up/Down | 方向键（`vk_right` 等） |  |
| A（跳/确认） | `Z`（`ord('Z')`） |  |
| B（扔橡子） | `X`（`ord('X')`） |  |
| Start | `Enter` |  |
| Select | `Shift` |  |

GMS 1.4 手柄：`io_clear()` + `keyboard_check` 为主；`gamepad` API 在 1.4 有限（`gamepad_is_connected` 等需扩展）。
建议：键盘为主，手柄为辅（`scr_nes_input` 已预留 `use_gamepad` 开关）。

边沿检测（`$3C` 新按下）→ GMS `keyboard_check_pressed`（已在 `scr_nes_input` 实现）。

## 5. APU → GMS 声音

| NES APU | GMS |
|---|---|
| 脉冲 1/2（`$4000–$4007`） | 序列器（`scr_nes_apu`，占位）→ 后续解码转 ogg |
| 三角（`$4008–$400B`） | 同上 |
| 噪声（`$400C–$400F`） | 同上 |
| DMC（`$4010–$4013`，本作禁） | 无需 |
| 帧计数器 `$4017=$C0`（4 步进，禁 IRQ） | GMS `sound` 播放（`sound_play`，ogg/wav） |

GMS 1.4 声音：`sound/` 下 `.ogg/.wav/.mp3`，`.sound.gmx` 引用 `sound/audio/*.wav`。
原型阶段：占位音效（跳、扔、命中）+ 音乐占位轨。完整解码后转 ogg（推荐 ogg，体积小）。

## 6. 碰撞与物理

GMS 1.4 无内置物理（`PhysicsObject` 字段存在但不推荐）。原版为 AABB + 地形图块碰撞：

- 地形：背景图块属性表（实心/单向/梯子）→ GMS `obj_solid` 碰撞体或 `ds_grid` 地形图
- 玩家：`$07AE/$07B4` 速度累加 → GMS `hspd/vspd` + `place_meeting`（`scr_physics`）
- 敌人：巡逻（`$92B6` 脚本）→ GMS `obj_enemy` 状态机

## 7. 对象与房间清单（骨架）

| 对象 | 作用 | 对应 NES |
|---|---|---|
| `obj_game` | 内核（状态机、NMI 步进、MMC1 兼容） | 固定银行 |
| `obj_player` | Chip（移动、跳、扔橡子） | 实体 X=3 |
| `obj_enemy` | 敌人（巡逻、脚本） | 实体数组 |
| `obj_camera` | 视图跟随 | `$2005` 滚动 |
| `obj_title` | 标题画面 | 状态 0/9 |

| 房间 | 尺寸 | 内容 |
|---|---|---|
| `rm_title` | 256×240 | 标题 Logo（CHR 30）+ 字体（CHR 31） |
| `rm_stage1` | 256×240（视图滚动） | 第一关背景 + 玩家 + 敌人 |

## 8. GMS 1.4.1760 注意事项

- 打开 `.project.gmx` 时若报版本不符：新建空工程 → 复制 `scripts/*.gml`（GMS 里“新建脚本”粘贴）→ 重建对象/房间（见 `README-GMS.md`）
- 精灵 PNG 放 `sprites/images/`，`.sprite.gmx` 引用 `images\*.png`（Windows 路径反斜杠）
- 声音放 `sound/audio/`，`.sound.gmx` 引用 `sound\audio\*.wav`
- 代码用 GML（`var`、`argument0`、`instance_create` 等），勿用 GMS2 的 `function`/`method` 语法
- `room_speed=60`，`display_get_gui_width` 等 GMS2 API 不可用
