# Chip 'n Dale: Rescue Rangers 2 — GMS 1.4.1760 新手操作指引

> 本文假设你完全没有用过 GameMaker Studio 1.4。按顺序做即可跑起来。
> 你负责在 GMS 编辑器里操作；素材和代码我已经提取/写好，直接用。
> 遇到任何一步和描述对不上，截图问我。

---

## 0. 交付物清单

| 文件 | 用途 |
|---|---|
| `extracted/bg/BG_title.png` | 标题画面背景（256×240，原版画面） |
| `extracted/bg/BG_stage1.png` | 第 1 关厨房背景（256×240，已把 Chip 站位补干净） |
| `extracted/sprites/chip_idle_0.png` | 站立姿势（17×24，透明底） |
| `extracted/sprites/chip_walk_0/1/2.png` | 走路循环 3 帧（21×32，透明底） |
| `extracted/sprites/chip_jump_0..4.png` | 跳跃 5 姿势（25×32，透明底） |
| `extracted/sprites/chip_crouch_0.png` | 下蹲姿势（24×18，透明底，静态 1 帧） |
| `extracted/collide/GND_256x24.png` | 地面碰撞块（不可见，仅用于碰撞） |
| `extracted/collide/WALL_16x240.png` | 墙壁碰撞块（不可见） |
| `extracted/audio/music_title.wav` | 标题音乐（可选） |
| `extracted/audio/music_stage1.wav` | 第 1 关音乐（62 秒，循环） |
| `code/01_obj_player_Create.gml` | obj_player 的 Create 事件代码 |
| `code/02_obj_player_Step.gml` | obj_player 的 Step 事件代码 |
| `code/03_obj_title_Step.gml` | obj_title 的 Step 事件代码 |

所有角色图都经过 **100% CHR 精确验证**（722/722 格子与原版 ROM 图块完全一致），
透明底、像素干净，可直接用。

---

## 1. 打开工程

1. 双击 `CnD Rescue Rangers 2.project.gmx`（用 GMS 1.4.1760 打开）。
2. 打开后左侧是**资源树**（Sprites、Sounds、Backgrounds、Objects、Rooms…），
   中间是工作区，顶部是菜单栏。
3. 先点菜单 **File → Save All**（Ctrl+Shift+S）确认工程能正常保存。

---

## 2. 创建背景（Backgrounds）

资源树里右键 **Backgrounds → Create Background**：

### 2.1 BG_title
1. Name 改成 `BG_title`。
2. 点 **Load** 按钮 → 选 `extracted/bg/BG_title.png`。
3. 其它默认不动（istileset 不勾）。

### 2.2 BG_stage1
1. 再右键 Backgrounds → Create Background，Name 改成 `BG_stage1`。
2. Load → 选 `extracted/bg/BG_stage1.png`。

> 验证：缩略图里应该能看到原版标题画面 / 厨房场景，颜色正常（不是灰块、不是花屏）。

---

## 3. 创建精灵（Sprites）

### 3.1 SPR_chip_idle（站立）
1. 资源树右键 **Sprites → Create Sprite**，Name 改成 `SPR_chip_idle`。
2. 点 **Load** → 选 `extracted/sprites/chip_idle_0.png`。
3. 右侧属性里设置 **Origin（原点）**：
   - X = `8`，Y = `24`
   - （原点 = 精灵在房间里的定位点。Y=24 是最底边 = 脚底，X≈水平中心。
     这样站立/走路/跳跃切换时角色不会左右跳动。）
4. **Bounding Box（包围盒）**：保持 Automatic（自动）即可。
5. 关闭该精灵标签页（会自动保存）。

### 3.2 SPR_chip_walk（走路，3 帧）
1. Create Sprite，Name = `SPR_chip_walk`。
2. 点 **Load** → 选 `chip_walk_0.png`（成为第 1 帧）。
3. 再点 **Load**（或 **Add Frame**，看按钮实际显示哪个）
   → 选 `chip_walk_1.png`；同样方法加 `chip_walk_2.png`。
   - 如果 Load 变成了"替换当前帧"，先点 **Add Frame** 生成空帧再 Load。
   - 最终帧列表必须是 3 帧：walk_0、walk_1、walk_2（顺序别乱）。
4. Origin：X = `10`，Y = `32`。
5. Bounding Box：Automatic。

### 3.3 SPR_chip_jump（跳跃，5 帧）
1. Create Sprite，Name = `SPR_chip_jump`。
2. 依次 Load：`chip_jump_0.png` … `chip_jump_4.png`（共 5 帧）。
3. Origin：X = `12`，Y = `32`。
4. Bounding Box：Automatic。

### 3.4 SPR_chip_crouch（下蹲，1 帧）
1. Create Sprite，Name = `SPR_chip_crouch`。
2. Load → `extracted/sprites/chip_crouch_0.png`。
3. Origin：X = `12`，Y = `18`。
4. Bounding Box：Automatic。
   - 说明：原版下蹲是**静态单帧**，且按住 ↓ 时**不能走动**（下蹲锁移动），
     代码里已按原版实现，不用你做额外设置。

### 3.5 SPR_gnd / SPR_wall（碰撞块，各 1 帧）
1. Create Sprite，Name = `SPR_gnd`，Load → `extracted/collide/GND_256x24.png`。
   Origin 保持默认（0,0）。
2. Create Sprite，Name = `SPR_wall`，Load → `extracted/collide/WALL_16x240.png`。
   Origin 保持默认（0,0）。
   - 这两个是纯色块，运行时**不会被画出来**（在对象里关掉了 Visible），
     只用来做碰撞。

> 检查清单：Sprites 下应有 6 个精灵：SPR_chip_idle、SPR_chip_walk（3帧）、
> SPR_chip_jump（5帧）、SPR_chip_crouch、SPR_gnd、SPR_wall。

---

## 4. 创建声音（Sounds）

资源树右键 **Sounds → Create Sound**：

1. Name = `MUS_stage1` → **Load** → `extracted/audio/music_stage1.wav`。
2. 其它保持默认即可。
   - 如果声音属性里有 **Streamed / 流式** 之类的选项，可以勾上（62 秒大文件更省内存）。
3. （可选）再建一个 `MUS_title`，Load → `music_title.wav`。

---

## 5. 创建对象（Objects）

### 5.1 obj_solid（碰撞父对象）
1. 资源树右键 **Objects → Create Object**，Name = `obj_solid`。
2. **不要给它选精灵**（Sprite 留 <no sprite>）。
3. 它本身不放房间里，只当"标签"用（子对象会继承它，碰撞检测统一查它）。

### 5.2 obj_ground（地面）
1. Create Object，Name = `obj_ground`。
2. Sprite 选 `SPR_gnd`。
3. 右侧属性：**Visible 取消勾选**（不显示）、**Solid 勾上**。
4. **Parent** 下拉选 `obj_solid`（关键！这样它就算"实心物"）。

### 5.3 obj_wall（墙）
1. Create Object，Name = `obj_wall`。
2. Sprite 选 `SPR_wall`。
3. Visible 取消勾选、Solid 勾上。
4. Parent = `obj_solid`。

### 5.4 obj_player（玩家）★核心
1. Create Object，Name = `obj_player`。
2. Sprite 选 `SPR_chip_idle`。
3. Visible 勾上、Solid 不用勾、Parent 留 <no object>。
4. 添加事件并粘贴代码：
   - 点下方 **Add Event → Create** → 弹出代码窗口，
     把 `code/01_obj_player_Create.gml` 的**全部内容**复制粘贴进去 → 关闭。
   - 点 **Add Event → Step → Step**（注意是 Step 分类下第一个 Step，
     不是 Begin Step / End Step）→ 粘贴 `code/02_obj_player_Step.gml` 全部内容 → 关闭。
5. 事件列表里应显示：Create、Step 各一个。

### 5.5 obj_title（标题控制）
1. Create Object，Name = `obj_title`。
2. 不选精灵（它只是个逻辑控制器，不画东西）。
3. **Add Event → Step → Step** → 粘贴 `code/03_obj_title_Step.gml`。

> 检查清单：Objects 下应有 5 个对象：obj_solid、obj_ground、obj_wall、
> obj_player（2 个事件）、obj_title（1 个事件）。

---

## 6. 创建房间（Rooms）

### 6.1 rm_title（标题房间）
1. 资源树右键 **Rooms → Create Room**。
2. 左侧分区切到 **Settings**：
   - Name = `rm_title`
   - Width = `256`，Height = `240`
   - **Speed = `60`**（默认是 30，本项目全部按 60 帧/秒调校，必须改！）
3. 分区切到 **Backgrounds**：
   - Background 1 的下拉选 `BG_title`，**Visible 勾上**，X/Y 都是 0，
     foreground 不勾。
4. 分区切到 **Objects**：
   - 上方下拉选中 `obj_title`，然后在画面**任意位置点一下**放一个实例
     （放哪都行，它没有碰撞也不画图）。
5. 关闭房间标签页。

### 6.2 rm_stage1（第 1 关）
1. 再 Create Room，Name = `rm_stage1`。
2. **Settings**：Width = `256`，Height = `240`，**Speed = `60`**。
3. **Backgrounds**：Background 1 选 `BG_stage1`，Visible 勾上，X/Y = 0。
4. **Objects** 分区，按下表摆放 4 个实例
   （选中对象 → 在画面点放；然后选中实例，在属性里把 X/Y 改成精确值，
   或用方向键微调）：

   | 对象 | X | Y | 说明 |
   |---|---|---|---|
   | obj_ground | `0` | `216` | 一整条地面（256 宽正好铺满） |
   | obj_wall | `0` | `0` | 左墙（16 宽） |
   | obj_wall | `240` | `0` | 右墙（240+16=256 正好到边） |
   | obj_player | `40` | `216` | 玩家出生点，Y=216 表示脚踩地面 |

5. 关闭房间标签页。

> 检查清单：Rooms 下有 rm_title、rm_stage1 两个房间。

---

## 7. 全局设置（画面缩放、清晰度）

1. 按 **Ctrl + Alt + G**（或资源树里双击 **Global Game Settings**）。
2. **Window 选项卡**：
   - Width = `512`，Height = `480`（房间是 256×240，正好 2 倍）
3. **Graphics 选项卡**：
   - **Interpolate colour（颜色插值）：取消勾选** ← 关键，不然像素会糊
   - Scaling 选 **Keep aspect ratio（保持宽高比）**
   - Start in full-screen：不勾（窗口模式即可）
4. 确定关闭。

---

## 8. 运行！

1. 按 **F5**（或 Run → Run Game）。
2. 预期流程：
   - 标题画面（原版画面 + 原版音乐，若你建了 MUS_title 可自行在
     rm_title 里加播放代码）
   - 按 **回车 或 空格** → 进入第 1 关
   - 厨房背景 + Chip 出现在地面上，BGM 循环
3. 操作：**← →** 走路（3 帧循环），**↓** 下蹲（原版规则：下蹲时不能走），
   **空格** 跳跃（5 姿势随速度切换），撞墙/落地正常。

---

## 9. 常用参数调整（改完 F5 立即生效）

都在 `obj_player` 的两个事件代码里改：

| 想要的效果 | 改哪里 | 怎么改 |
|---|---|---|
| 走得更快/更慢 | Create 里 `movespd = 2` | 2→3 更快 |
| 跳更高 | Create 里 `jumpv = -7.5` | 改成 -9（更高）/ -6（更低） |
| 重力手感 | Create 里 `grav = 0.45` | 越大下落越"重" |
| 走路动画快慢 | Step 里 `image_speed = 0.3` | 0.4 更快 |
| 房间帧率 | 房间 Settings 的 Speed | 保持 60，别动 |

---

## 10. 常见问题排查

| 症状 | 原因/解法 |
|---|---|
| 编译报错 `...does not exist` | 资源名打错：对照清单检查 SPR_ / obj_ / MUS_ 拼写（大小写敏感） |
| 编译报错在某一行 | 双击该事件，检查那行代码有没有复制漏/多 |
| 玩家穿地而过 | obj_ground 的 Parent 没设成 obj_solid；或房间 Speed 不是 60 |
| 玩家不显示 | obj_player 的 Visible 没勾；或 Sprite 没选 SPR_chip_idle |
| 角色切换姿势时左右抖动 | 四个角色精灵的 Origin 按 3.1~3.4 的值再核对一遍 |
| 图像模糊 | Global Game Settings → Graphics → Interpolate colour 没取消 |
| 画面太小 | Global Game Settings → Window 宽高 512×480；Scaling = Keep aspect ratio |
| 没有音乐 | 声音资源是否建了 MUS_stage1；Create 末尾那行是否在 |
| 想删实例 | 选中后 Delete；或房间 Objects 分区里选中删除 |

---

## 11. 之后可以做什么（按难度排序）

1. **标题闪烁 "PRESS START"**：在 rm_title 放一个带文字图的小精灵，
   Step 里 `image_speed = 0.5` 闪烁。
2. **房间切换淡入淡出**、**生命值/分数 HUD**（HUD 图标 CHR 也已提取）。
3. **关卡滚动**：开 Views（视口），房间做宽，摄像机跟随玩家。
4. **更多动画**：站立/走路已有完整循环；下一批可提取攀墙、搬箱子、
   受伤闪烁（用同样的 OAM+CHR 管线，直接告诉我）。
5. **敌人与碰撞伤害**：需要敌人精灵提取（管线就绪）+ 接触判定代码。
