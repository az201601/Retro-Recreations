# GMS 1.4.1760 工程说明

## 打开方式（首选）

1. 安装 **GameMaker Studio 1.4.1760**（Windows 官方旧版，勿用 GMS2）
2. 打开 `ChipNDale2_GMS14.project.gmx`
3. 若提示版本/配置缺失，点“确定”让 GMS 补全默认值，然后**另存为**新工程再继续
4. 按 F5 运行：`rm_title` → 按 Enter → `rm_stage1`（方向键移动，Z 跳）

## 若 .project.gmx 打不开（备用：手动重建）

1. GMS 新建空工程（256×240，room_speed=60）
2. **脚本**：资源树右键 → 新建脚本，逐个粘贴 `scripts/*.gml` 内容
   - `scr_nes_input`、`scr_nes_ppu`、`scr_nes_apu`、`scr_nes_mmc1`、`scr_game_state`、`scr_physics`
3. **精灵**：新建精灵，导入 `sprites/images/*.png`（`spr_chip` 16×16、`spr_solid` 16×16、`spr_title` 256×64）
4. **声音**：新建声音，导入 `sound/audio/*.wav`（`sfx_jump`、`mus_title`，均为静音占位）
5. **对象**：按 `objects/*.object.gmx` 的事件代码重建（Create/Step/Draw）
   - `obj_game`（Create 初始化 + Step 主循环）、`obj_player`、`obj_enemy`、`obj_camera`、`obj_title`、`obj_solid`
6. **房间**：`rm_title`（256×240，放 obj_game + obj_title）、`rm_stage1`（1024×240，视图 256×224，放 obj_game/obj_camera/obj_player/obj_enemy/obj_solid 地面）

## 键位

| 动作 | 键 |
|---|---|
| 移动 | 方向键 |
| 跳（A） | Z |
| 扔橡子（B，占位） | X |
| 开始（Start） | Enter |
| 选择（Select） | Shift |

## 目录结构（GMS 1.4 约定）

```
ChipNDale2_GMS14/
├── ChipNDale2_GMS14.project.gmx  # 工程主文件（XML）
├── Configs/Default.config.gmx
├── scripts/*.gml                 # GML 源码（纯文本）
├── objects/*.object.gmx
├── rooms/*.room.gmx
├── sprites/*.sprite.gmx + images/*.png
├── sound/*.sound.gmx + audio/*.wav
└── extensions/                   # 空（预留）
```

> 路径分隔符为 Windows 反斜杠（`.gmx` 内 `sprites\spr_chip`），在 Windows 上打开无误。
