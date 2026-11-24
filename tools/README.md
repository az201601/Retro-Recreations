# 素材提取工具链（NES → GMS 1.4）

用准确的 NES 模拟器（FCEUmm，libretro 核心）无头运行 ROM，
按时间轴脚本截图/录音，并把 CHR 图形数据与游戏实际画面做逐格精确验证。

## 开场 spotlight / silhouette 场景

`python3 tools/capture_spotlight_intro.py` captures NES frames 1–900 at native
256×240 and writes 15 row-major sprite-strip atlases to
`extracted/spotlight_intro/`, plus `frame_map.csv`. The 900 cells have been
verified pixel-for-pixel against emulator captures. For GMS import steps and
playback GML, see [`docs/spotlight_intro.md`](../docs/spotlight_intro.md).
The script needs Pillow and the emulator frontend built below; raw PPM captures
are scratch data under ignored `tools/out/`.

## 重新构建模拟器前端

```bash
# 1) 获取核心与头文件（已包含在仓库中则跳过）
git clone --depth 1 https://github.com/libretro/libretro-fceumm tools/emu/libretro-fceumm
git clone --depth 1 https://github.com/libretro/libretro-common  tools/emu/libretro-common
cp tools/emu/libretro-common/include/libretro.h tools/emu/lc_include/

# 2) 编译核心
cd tools/emu/libretro-fceumm && make -f Makefile.libretro -j$(nproc) && cd ../..

# 3) 编译前端
cd tools/emu
gcc -O2 -o retroshot retroshot.c -I lc_include ./libretro-fceumm/fceumm_libretro.so \
    -Wl,-rpath,'$ORIGIN/libretro-fceumm' -lm
```

## 运行（截图 + 录音）

```bash
mkdir -p tools/out/run
cd tools/emu
./retroshot -c libretro-fceumm/fceumm_libretro.so \
    -r "../../Chip 'n Dale - Rescue Rangers 2 (USA).nes" \
    -t play4.txt -o ../out/run -m 8050
```

时间轴格式（每行 `帧号 命令 [参数]`，60fps；命令在该帧结束后执行）：

```
1000 tap START 6      # 按下 START，6 帧后松开
4400 press RIGHT      # 持续按住右
4500 tap A 8          # 跳跃
4440 shot p4440       # 截图 → out/p4440.ppm
5800 quit
```

按键：`A B SELECT START UP DOWN LEFT RIGHT`。

## 验证（tools/verify_chr2.py）

把画面切成 8x8 格，在 CHR 数据中反查能精确复现该格的图块
（枚举 P(4,k) 颜色→索引映射）。结果：

| 画面 | 精确匹配率 | 未匹配 |
|---|---|---|
| 标题画面 | 96.9% | 跳舞的 Dale、logo 老鼠头（精灵覆盖） |
| 第 1 关起始画面上半 | 99.6% | Chip 的头部 |
| 第 1 关 HUD 区 | 96.1% | Chip 身体、HUD 图标 |

未匹配格全部落在精灵位置，**背景图块与提取的 CHR 数据逐像素一致**。
`extracted/verify_recon_stack.png` 为「原画面 | CHR 重建（红=精灵格）」对照。

精灵格验证：`tools/verify_sprite.py`（单帧，已知背景调色板）、
`tools/sprite2.py`（双帧差分）。

## 精灵动画提取（OAM，tools/oam_extract.py）

`retroshot` 支持 `ram <name>` / `rampre <name>` 命令，导出完整 2KB CPU RAM。
实测本作 OAM DMA 源页为 **$0600**（每帧 64×4 字节：Y/tile/attr/X）：

- 带翻转位(0x40)、tile<0x40 的条目 = 角色；固定不动的 tile 0x87/0x88 = HUD 图标
- 截图 + OAM 配对 → 按 OAM 坐标切格（处理精灵重叠优先级、水平/垂直翻转）
- 每格在全部 CHR 中反查：严格角色色必须映射到非零索引，背景色可映射到 0
  或认领空闲索引（解决「描边黑 == 阴影黑」的同色冲突），按背景色落透明位数评分
- 当前成绩：**327/359 = 91.1% 格子为 CHR 精确命中**，精灵图形全部来自 bank7

产物：`extracted/sprites/chip_{idle,walk,jump}_*.png`（全格精确的姿势，RGBA 透明）
与 `frames/`（逐帧）、`strip_*.png`（预览条）。

**最终成绩：100%（722/722 格 CHR 精确命中）**。三次关键修复：
① 屏幕显示的是镜像，匹配前按翻转位还原；② NES 精灵优先级是"低索引覆盖、
透明像素穿透到下层精灵"——上层精灵的透明处颜色属于下层，须记入 wild；
③ 全背景色格子（最低优先级+地板色）没有严格锚点时走全软匹配，并优先信任
OAM 图块号指示的 bank7 结构。

产物（组内尺寸统一、水平居中、脚底对齐，可直接进 GMS）：
- `extracted/sprites/chip_idle_0.png`（17×24）
- `extracted/sprites/chip_walk_0..2.png`（21×32，走路循环 3 帧）
- `extracted/sprites/chip_jump_0..4.png`（25×32，跳跃 5 姿势）
- `extracted/sprites/chip_crouch_0.png`（24×18，下蹲；29+13 帧采样全同 →
  静态 1 帧，原版下蹲锁横向移动，无下蹲走动画）
- `frames/` 逐帧、`strip_*.png` 预览条
- `extracted/bg/BG_title.png`（256×240 标题）、`BG_stage1.png`（256×240 第1关，
  Chip 站位区用滚动差=0 的干净帧补齐）
- `extracted/collide/GND_256x24.png`、`WALL_16x240.png` 碰撞块
- `code/*.gml` 玩家/标题逻辑；`docs/GMS_1.4_新手指引.md` 编辑器操作指引

## 已提取素材（extracted/）

- `chr/bank00..15.png` — 16 个 8KB CHR 银行（512 图块/银行，灰阶预览）
- `audio/music_intro.wav`（15.0s 开场）、`music_title.wav`（10.3s 标题）、
  `music_menu.wav`（35.6s 菜单）、`music_cutscene.wav`（4.0s 过场）、
  `music_stage1.wav`（62.4s 第 1 关 BGM）— 均为 48kHz 单声道，直接来自模拟器输出
- `verify_*.png` — 验证对照图

## 游戏流程（实测）

开机版权 → 弹跳砖球动画 → 标题（START）→ 1player/2players（A）→
角色选择 Chip/Dale（A）→ 新闻播报过场（A 翻页）→ 夜景城市动画 → **第 1 关（厨房）**
