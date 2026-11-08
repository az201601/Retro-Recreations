# 资源研究与提取进度

目标环境：GameMaker Studio 1.4.1760。当前阶段仅研究、提取与分类，不实现游戏逻辑。

## 已确认

仓库中的美版 ROM 使用 iNES 容器，Mapper 1；包含 128 KiB PRG ROM 和 128 KiB CHR ROM。CHR ROM 共 8192 个 8×8、2 位色深的图案，其中有重复图案。图案本身只包含色号，不包含最终颜色、透明度、精灵拼装、关卡布局或用途。

`tools/extract_chr.py` 能无损解码这些图案的色号，输出按 ROM 顺序排列的灰度索引图及位置清单，供后续研究：

```sh
python3 tools/extract_chr.py "Chip 'n Dale - Rescue Rangers 2 (USA).nes" extracted/chr
```

每张 PNG 是 16×16 个图案，每个图案 8×8 像素，左上起逐行排列；黑到白分别表示色号 0–3。`manifest.json` 给出源文件 SHA-256、每张图在 CHR 内的字节偏移及起始图案编号。输出的灰度 **不是游戏配色**；色号 0 也不能一概视作透明。输出文件仅用于研究，不是最终 GameMaker 资源。

## 尚未完成，需要逐项验证

- 研究运行时的调色板、CHR 分页及场景切换，恢复正确颜色及图案组合。
- 解析关卡布局与滚动方式，区分最底层背景、装饰 tileset，以及需代码控制的 sprite；逐场景核对，避免仅凭外观分类。
- 还原角色、敌人、物件及动画帧的拼装、原点和透明区域；提取界面、文字图形并制作 sprite font 字符映射。
- 分析音频驱动与音乐、音效数据，确认曲目、循环和播放方式，再确定可用于 GMS 1.4 的导出格式。NES 音频由程序驱动 APU 产生，不能将 ROM 字节直接当作现成音频文件。
- 建立逐场景及逐资源清单，在模拟器运行画面和音频中验证完整性，并最终组织为 GMS 1.4 可导入的资源。当前没有完成上述内容，也没有建立 GameMaker 工程。

提取结果源自原游戏，使用与分发时需自行确认相关权利。

## 运行时采样（研究用）

已用 libretro-fceumm 在无窗口环境中运行仓库 ROM，取得标题画面和选择界面的截图，以及同步录制的混合音频；这些文件是参考记录，并非已拆分的素材。运行所用核心源码版本为 `e0f3086`，核心本身没有加入仓库。示例构建与采集命令（需要 Git、C 编译工具链和 Python 3）：

```sh
mkdir -p .cache
git clone https://github.com/libretro/libretro-fceumm.git .cache/libretro-fceumm
git -C .cache/libretro-fceumm checkout e0f3086
make -C .cache/libretro-fceumm -j4
python3 tools/capture_runtime.py .cache/libretro-fceumm/fceumm_libretro.so \
  "Chip 'n Dale - Rescue Rangers 2 (USA).nes" extracted/runtime \
  --frames 1300 --capture 650,750,900,1100,1300 --start 650,800,1000
```

采集工具以 1 为起点计帧，`--start` 在列出的帧按下第一手柄的 START 一帧。输出的 `manifest.json` 包含 ROM 与核心 SHA-256、帧率、音频采样率和操作记录，方便复现。截图使用核心渲染结果；`mixed_audio.wav` 是整段游戏的混音，可能包含音乐、音效或静音，不能直接作为独立曲目或音效交付。不同模拟器、调色板、裁边与音频设置可能产生不同结果。

已观察到标题画面、单人/双人选择及 Chip/Dale 选择；目前还没有完成关卡采样、图层拆分、音轨分离或资源穷举。游戏内操作、更多场景以及声音触发方式仍需继续研究。

## 逐帧状态与关卡采样

扩展采样工具后，已进入并截图采集到一个关卡画面（`extracted/runtime3/frame_001800.png`），并在第 650、1500、1800 帧提取了模拟器的帧末状态。示例：

```sh
python3 tools/capture_runtime.py .cache/libretro-fceumm/fceumm_libretro.so \
  "Chip 'n Dale - Rescue Rangers 2 (USA).nes" extracted/runtime3 \
  --frames 1800 --capture 650,900,1300,1500,1800 \
  --start 650,800,1000,1300,1500 --save-state
python3 tools/inspect_fceumm_state.py extracted/runtime3/state_001800.fcs \
  "Chip 'n Dale - Rescue Rangers 2 (USA).nes" extracted/ppu/001800
```

`--press` 还支持 `帧号:按键`（例如 `--press 1900:A,1910:RIGHT`），每项仅按一帧。状态解析器针对上述版本的 FCEU 未压缩状态格式及本 ROM 的标准 MMC1 映射，输出帧末活动 CHR 数据、2 KiB nametable RAM、32 字节调色板 RAM、256 字节 OAM，以及可读 JSON（含精灵位置、翻转、调色板选择和 MMC1 寄存器）。第 1800 帧的 MMC1 寄存器为 `1e 0f 00 05`，帧末映射到 PPU 的 4 KiB CHR 页为 15 和 0，镜像模式为垂直镜像。

**重要限制：** 状态取自帧末，不能证明整帧的 CHR 页、寄存器、滚动或调色板没有在扫描线中途切换。OAM 的 64 条记录包含未使用、遮挡或屏外精灵，不能直接当作 64 个完整角色；游戏角色通常由多个硬件精灵拼装。NES 色号不是 RGB，精灵调色板的透明色也不能直接作为实色。现有输出是分析数据，不是最终素材。没有完成全部场景、动画、背景层或音乐音效的提取。

## 关卡画面图形拆解试验

从第 1800 帧的帧末状态生成了两张物理 nametable 背景、四张不同调色板版本的背景图块表，以及 11 个屏内硬件精灵片段。经目视对照，第一张 nametable 包含截图中的关卡背景及平台等图像；它不包含角色图像。这是 PPU 背景平面，并不等于最终设计分类：平台和其他可交互元素即便由 PPU 背景绘制，重制时仍需按行为拆为 sprite。

```sh
python3 tools/render_ppu.py extracted/ppu/001800 \
  .cache/libretro-fceumm/src/palettes/palettes.h extracted/render/001800
python3 tools/assemble_oam.py extracted/ppu/001800 \
  .cache/libretro-fceumm/src/palettes/palettes.h \
  extracted/render/001800/chip_candidate.png --indices 1,2,3,4,5,6,7
```

图块表以 16×16 排列，物理 nametable 按属性表选择背景调色板；OAM 片段保留透明色、调色板和翻转。颜色表读取自本地编译所用 FCEUmm 源码，输出为该模拟器配色近似，非唯一的 NES 色彩标准。手工选取这 7 个 OAM 片段得到一个疑似 Chip 的单帧候选图，保留透明背景及拼装坐标；尚未验证动画、原点、角色身份或全部可能姿态。

此方法不还原扫描线中途切换、背景滚动、精灵与背景之间的遮挡、精灵每行数量限制，也不能自动断定物件的逻辑用途。nametable 是帧末物理内存，可能包含屏外内容或未使用内容；图块表也包含当前未使用的图块。所有结果都是研究草稿，不能算作完整素材库。后续仍需扩大关卡、角色状态、场景和声音覆盖范围并人工核对。
