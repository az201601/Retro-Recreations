# 搬运指南 —— 把素材与代码导入 GameMaker: Studio 1.4.1760

这份文档对应仓库里的两个目录：

| 目录 | 内容 |
|---|---|
| `assets_vec/` | 全部素材（逐像素提取，未重绘、未放大） |
| `code/` | GML 1.4 代码清单（每个事件一个 `.gml` 文件） |

导入顺序建议：**先素材 → 再脚本 → 再对象 → 最后房间**。全程不需要 `.project.gmx`，
你只需要在自己的空工程里按下面的步骤建资源。

---

## 0. 工程基本设置

1. 新建工程，`Target` 选 **Windows**（或你要的平台）。
2. `Game Settings → Window`：分辨率关掉 “Interpolate colors between pixels”，
   `Scaling` 选 **Keep aspect ratio**。
3. 房间尺寸 **256 × 240**，`Room Speed` **60**。NES 是 256×240，60 fps，
   所有物理参数（重力、速度）都是按这个帧率调好的，不要改成 30 或 120。
4. 显示缩放交给窗口：`Global Game Settings → Graphics` 里 `Scaling = 3x`
   得到 768×720 的窗口。

---

## 1. 精灵（Sprites）—— 逐帧图与命名

素材是**横向排列的整条动画带**（strip），一帧宽 × 帧数 = 图片宽度。

### 1.1 命名规则

```
assets_vec/sprites/<角色>/<动画>.png   ->  精灵名  spr_<角色>_<动画>
assets_vec/ui/<名字>.png               ->  精灵名  spr_ui_<名字>
```

代码通过 `asset_get_index("spr_chip_walk")` 找精灵，**所以名字必须一致**，
大小写也要一致。如果 GMS 报 “name already exists” 或你改了名，
改 `code/scripts/scr_anim_init.gml` 里的字符串即可，不用改别处。

### 1.2 导入一条动画带

以 `assets_vec/sprites/chip/walk.png`（20×25，4 帧）为例：

1. `Create Sprite`，名字填 `spr_chip_walk`。
2. 勾掉 `Preview`（不要自动裁剪）。
3. `Load Sprite` 选 `assets_vec/sprites/chip/walk.png`。
4. 在 `Sprite Properties` 窗口左上角把 `Width / Height` 改成 **20 × 25**
   （这就是单帧尺寸），GMS 会自动把 80 px 宽的图切成 4 帧。
5. 设置 **Origin**：`X = 10, Y = 25`（底边中点）。整组 Chip 精灵都是“脚底对齐”，
   这样在地面上时 `y` 就是接地点。
6. `Collision Checking` → `Precise collision checking` 建议 **关**，
   改用 `Bounding box`，然后把 `Left/Right/Top/Bottom` 调成
   **-6 / 6 / -24 / 0**（比画出来的小，接近原版宽松的判定）。

### 1.3 全部精灵清单（尺寸 / 帧数 / 原点）

下面这张表由 `python tools/gen_readme_table.py` 从 `assets_vec/sprites/sprites.json`
自动生成，和素材包永远一致（不要手改，改完跑一下脚本）。

<!-- BEGIN SPRITE TABLE -->
| 文件 | 精灵名 | 帧尺寸 | 帧数 | Origin |
|---|---|---|---|---|
| `sprites/chip/idle.png` | `spr_chip_idle` | 20x24 | 2 | 10, 24 |
| `sprites/chip/walk.png` | `spr_chip_walk` | 20x25 | 4 | 10, 25 |
| `sprites/chip/jump.png` | `spr_chip_jump` | 23x25 | 2 | 11, 25 |
| `sprites/chip/fall.png` | `spr_chip_fall` | 20x24 | 2 | 10, 24 |
| `sprites/chip/land.png` | `spr_chip_land` | 23x18 | 1 | 11, 18 |
| `sprites/chip/push.png` | `spr_chip_push` | 18x25 | 1 | 9, 25 |
| `sprites/chip/throw.png` | `spr_chip_throw` | 20x25 | 2 | 10, 25 |
| `ui/heart.png` | `spr_heart` | 8x8 | 1 | 4, 4 |
| `ui/hud_hearts.png` | `spr_hud_hearts` | 34x18 | 1 | 0, 0 |
| `ui/pixel.png` | `spr_pixel` | 1x1 | 1 | **0, 0** |
| `ui/title_screen.png` | `spr_title_screen` | 256x240 | 1 | 0, 0 |
<!-- END SPRITE TABLE -->

> `spr_pixel` 的原点必须是 **左上角 (0,0)**：`obj_ground` 用 `image_xscale`
> 把 1×1 白点拉成整块平台，原点在中心的话位置会整体偏移半个平台。
>
> `sprites/<角色>/<动画>_fNN.png` 是**单帧图**，只是方便你核对/微调用的，
> 不要单独导入。
>
> 每个精灵的 `播速` 不用在精灵里设，`image_speed` 由 `scr_anim_init` 控制，
> 所以精灵的 `Animation Speed` 随便填 0 就行。

### 1.4 HUD 与标题画面

- `spr_hud_hearts`：整块 HUD（小人头像 + 3 颗心）已是透明底，原点 (0,0)，
  直接画在 (8, 200) 附近即可。
- `spr_heart`：单颗心，`obj_hud` 用它按血量重复画。
- `spr_title_screen` / `spr_scene_house`：整屏背景图，原点 (0,0)。

---

## 2. 背景（Backgrounds）与关卡

`assets_vec/backgrounds/level01/` 是第一关（汉堡柜台屋内）：

| 文件 | 用途 |
|---|---|
| `screen_00.png` | **完整的 256×240 无精灵关卡图**，逐像素等于真机画面 |
| `canvas.png` | 512×480 的整幅滚动画布（参考用，关卡是单屏所以用不到） |
| `tileset.png` | 16×16 元格子图集（若你想用真正的 GMS Tile 层） |
| `tileset_8x8.png` | 原生 8×8 图集，按 `info.json` 的 `tiles_8x8` 顺序排列 |
| `info.json` | 调色板、CHR 窗口、滚动值、15×16 的元格子索引表 |
| `collision.json` | 可站立平台的矩形（脚本自动从像素里推出来的） |

### 2.1 最快的方式（推荐先做这一步）

1. `Create Background`，名字 `bg_level01`，`Load` `screen_00.png`。
2. 房间 `Backgrounds` 标签里指定 `bg_level01`，`Depth = 1000`，
   **取消勾选 `Stretch`**、`Horizontal tile / Vertical tile` 都关。
3. 平台碰撞直接照抄 `collision.json`（或下面这几行），
   用 `scr_platform_add(x, y, w, h)` 生成：

```
scr_platform_add(128,  80, 128, 16);   // 上层搁板
scr_platform_add( 65, 160, 174, 16);   // 长餐桌
scr_platform_add( 11, 192,  68, 16);   // 矮凳
```

`y` 是**画面里那条台面的顶线**，和原版的落脚高度一致。

### 2.2 想用 Tile 层

`tileset.png` 是 16×16、每行 16 个的元格子图集；`info.json` 里
`map[15][16]` 是这一屏用到的索引（行优先）。把图集导成 Tile Set
（`Create Tileset`，`Tile Size 16×16`，`Separation 0`），
再按 `map` 手动铺 15 行即可。这条路更“正规”，但慢；先用 2.1 跑起来再说。

---

## 3. 脚本（Scripts）

`code/scripts/*.gml` 里的每一个文件 = GMS 里的**一个 Script 资源**，
名字就是文件名去掉 `.gml`（例如 `scr_config_init.gml` → `scr_config_init`）。

| 脚本 | 作用 |
|---|---|
| `scr_config_init` | 全局常量：重力、速度、跳跃、层深度、NES 调色板 |
| `scr_input_init` | 键位映射（方向键/WASD、X 跳、Z 抓/扔、Enter 暂停） |
| `scr_input_poll` | 每帧刷新 `global.IN`，含“刚按下”边沿与手柄支持 |
| `scr_anim_add/get/set/update/init` | 动画表：键名 → 精灵条 + 帧数 + 播放速度 |
| `scr_move_and_collide` | 对 `obj_ground` 的分轴碰撞（设置 `on_ground`） |
| `scr_platform_add` | 生成一块矩形实体平台 |
| `scr_player_hit` / `scr_player_die` | 受伤无敌帧、掉血、死亡重开 |
| `scr_enemy_hit` | 敌人受击（击退、掉血、死亡） |
| `scr_cutscene_add` | 给过场对象追加一个镜头 |

导入方式：`Create Script` → 名字填好 → 把对应 `.gml` 的内容整段粘进编辑器。
**脚本里不能有 `function`、`enum`、`#region`**（那是 GMS2 的语法），
打包时已经检查过（`python tools/check_gml.py`）。

---

## 4. 对象（Objects）

`code/objects/<对象名>/<事件>.gml`，事件名对应 GMS 里的事件：

| 文件名 | GMS 事件 |
|---|---|
| `Create_0.gml` | Create |
| `Step_0.gml` | Step |
| `Draw_0.gml` | Draw |
| `Draw_64.gml` | **Draw GUI**（64 = GUI） |
| `Other_4.gml` | Other → **Room Start** |

| 对象 | 需要的事件 | 说明 |
|---|---|---|
| `obj_gamecontroller` | Create / Step / Draw GUI | 全局初始化、暂停。**Persistent 勾上** |
| `obj_player` | Create / Step / Draw / Room Start | Chip，跑跳抓扔 |
| `obj_ground` | Create | 不可见实体平台（由 `scr_platform_add` 生成） |
| `obj_hud` | Draw GUI | 心 + 分数 |
| `obj_title` | Create / Step / Draw | 标题画面 |
| `obj_cutscene` | Create / Step | 过场播放器（逐个镜头） |
| `obj_crate` | Create / Step / Draw | 箱子（会挡住/被扔出） |
| `obj_debris` | Create / Step / Draw | 碎裂粒子 |
| `obj_enemy_walker` | Create / Step | 巡逻敌人（素材待补，见第 7 节） |

对象需要的 `Sprite` 可以在 Create 里 `asset_get_index` 找不到时保持 `-1`，
所以**即使某些精灵还没导，工程也能跑**（那几个对象会隐身但仍存在）。

---

## 5. 房间（Rooms）

`code/rooms/<房间名>/RoomCreationCode.gml` = 房间的 **Creation Code**。

需要建两个房间：

1. **rm_title** —— 256×240，放 `obj_gamecontroller`（Persistent），
   把 `rm_title/RoomCreationCode.gml` 贴进 Creation Code。
2. **rm_level01** —— 256×240，背景 `bg_level01`（Depth 1000），
   把 `rm_level01/RoomCreationCode.gml` 贴进 Creation Code。
   `obj_gamecontroller` 因为有 Persistent，会自己带过来。

房间顺序：`rm_title` → `rm_level01`。

---

## 6. 常见问题

**画面模糊 / 有彩边**
关掉 “Interpolate colors between pixels”，窗口缩放用整数倍（3×）。

**角色悬空或陷进地板**
`spr_chip_*` 的 Origin 必须是底边中点；`obj_ground` 的矩形 `y` 是台面顶线。

**报 `asset_get_index` 找不到**
说明精灵名和上表不一致。跑 `python tools/check_assets.py`，
它会把代码里用到、但素材包里没有的名字全部列出来。

**想核对提取对不对**
`assets_vec/backgrounds/level01/screen_00.png` 与真机截图像素级一致
（差异只有精灵，因为背景是从 VRAM 直接重建的，不含任何 sprite）。

---

## 7. 目前的进度 / 还没做的

### 已完成（可以直接导入并跑起来）

- 第一关（汉堡柜台屋内）完整背景 `bg_level01` + 平台碰撞
- Chip：待机 / 跑（4 帧循环）/ 跳 / 落 / 落地 / 抱起 / 扔出
- HUD（头像 + 生命心）、单颗心、1×1 像素、标题画面
- 全套 GML 1.4 代码：标题 → 关卡、移动、分轴碰撞、抓箱子扔箱子、
  受伤无敌帧、暂停、过场播放器骨架

### 还没提取（代码已写好，素材缺）

| 缺的素材 | 说明 |
|---|---|
| `spr_crate` / `spr_debris` / `spr_enemy_walker` | 第一关里箱子是"炮弹"、敌人只在小窗口出现过，需要先录到它们完整出现的画面 |
| 原版的"双手举箱"姿势 | 目前 `spr_chip_push` 暂用一帧行走图；录到的第一关里 Chip 没有做举箱动作，等录到再替换 |
| 过场角色（Dale / Gadget / 博士 / 标题合体图） | FATCAM 过场在 6000 帧之后才开始，现有录制窗口只覆盖开头，需要更长的录制 |
| 第 2 关及以后 | 目前只完整提取了第 1 关 |
| 中文点阵字体 | NES 原版没有中文字库，需要用系统字体或自制点阵 |

上面三类都**不影响已导出的内容**：`scr_anim_init` 用
`asset_get_index()` 查名字，缺的精灵会被跳过，代码里相关对象也会自动隐身，
所以你现在导入现有素材就能跑第一关。

### 怎么自己扩展

```
tools/capture_all.sh            # 重新录制全部 trace（约 70 秒）
.venv/bin/python tools/find_poses.py pi_holdR   # 列出某个 trace 里的所有不同姿势
.venv/bin/python tools/build_assets.py          # 重新生成精灵
.venv/bin/python tools/build_level.py           # 重新生成关卡背景与图集
.venv/bin/python tools/build_collision.py       # 重新推导平台
.venv/bin/python tools/verify.py                # 一键自检（尺寸 / 像素 / 代码 / 命名）
```

新增一条动画的流程：用 `find_poses.py` 找到帧号 → 在
`tools/build_assets.py` 的 `ANIMS` 里加一行 `("trace", frame)` →
跑 `build_assets.py` → 在 `scr_anim_init.gml` 里注册名字 →
跑 `gen_readme_table.py` 刷新本文件的精灵表。
