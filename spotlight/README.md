# 第一幕：探照灯（GMS 1.4.1760 / Windows）

基准是仓库的 USA ROM，SHA-256 `34ca559b733ed910b0a493a0cb1f5d64e5cd9e7e4796032d986c08079573e047`。JSNES 3.0.0 默认画面设置，冷启动，无按键。以第一次 `nes.frame()` 完成为第 1 帧。不是按视频时间戳估算。

|JSNES 帧（含两端）|内容|
|---|---|
|157–212|版权页之后的 56 帧纯黑；本房间从这里开始|
|213–595|第一段光斑；第一帧只在顶部出现一小片砖墙|
|596–708|完全离开画面，113 帧纯黑，不要提前切镜|
|709–867|光斑从左侧再次进入，出现剪影并停留|
|868–879|剪影画面分级变暗|
|880–892|13 帧纯黑|
|893–904|标题分级显现|
|905–1150|本次记录中的稳定标题画面|

## 在 GMS 里重现

1. 新建 **GameMaker: Studio** 空工程，目标选 Windows。右键 **Included Files → Insert Included File**，将 `data` 下的 **30 张 PNG 和 1 个 TXT** 加入（可分批）。导出位置保留默认，与游戏数据在同一层，不要创建 `data` 子目录。PNG 是不透明的整帧图集，**不要**当作带透明色的 Sprite 导入。
2. 创建 Object，命名 `obj_spotlight`，不选 Sprite，勾选 Visible，不勾 Persistent。
3. 在这个对象中添加 **Create、Step → Step、Draw → Draw、Destroy** 四个事件。每个事件拖一个 **Control → Execute Code**，分别粘贴 `gml` 中同名文件的全部内容。不是建四个 Script，也不用写 GMS2 的函数或序列。
4. 创建第一个 Room `rm_spotlight`，Settings 中 Width **256**、Height **240**、Speed **60**；不启用 Views。在 Objects 页把 `obj_spotlight` 放入一次，坐标设为 `(0,0)`。全局图形设置关闭插值，测试时优先原尺寸或整数倍显示。
5. F5 运行。**空格**暂停/继续；暂停时 **左右方向键**逐帧；**R** 回到版权页后的第一帧黑屏。标题最后一帧停住，不循环。
6. 对照检查：暂停后按 R，再按右键 56 次，应在原图 `x=172..212, y=8..17` 看见第一小片亮区。`frames.csv` 的 `F` 以此帧为 0；`tile` 是图集编号，不是时间。相邻相同图像仍各占一个 Step。

## 核验和范围

两次独立冷启动输出的前 1150 帧 RGB 完全一致。播放区间连续 994 帧、469 种不同图像。`tools/pack.py` 从写回磁盘的 PNG 和索引逐帧还原并与原始 RGB 比较；`frames.csv` 附每一帧 RGB SHA-256 和非黑像素边界（右、下为开区间）。复核时用 Node 22+、`npm install --no-save jsnes@3.0.0`、Python 3 + Pillow，运行 `node spotlight/tools/capture.cjs "ROM路径" 临时输出目录` 后运行 `python spotlight/tools/pack.py 临时输出目录`。

这是合成画面的无损回放，不是分层重建 NES 的遮罩、背景或角色逻辑。逐帧相同指图集还原结果相对上述 JSNES 输出，不是实机验证；GMS 设为 60 Step/s，不等同于 NTSC 的精确刷新时钟。尚未在 GMS IDE 实跑；本阶段不含声音、标题输入或后续关卡。
