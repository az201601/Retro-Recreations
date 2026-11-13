# 03 — 固定银行内核（`$C000–$FFFF`，PRG 银行 7）

> 内核 = NMI 中断 + 复位初始化 + MMC1 驱动 + PPU 上传 + 手柄 + 状态机分发。
> 反汇编：`disassembly/fixed_bank7_C000.asm`。递归追踪：`python3 tools/dis6502.py --rom "...nes" --trace`（740 字节代码，20 个 JSR 目标）。

## 1. 复位与主初始化（`$FFE0` → `$C106` → `$D043`）

```
$FFE0 SEI; INC $FFE1 (MMC1 复位); CLD; JMP $C000
$C000 JMP $C106
$C106 SEI
      LDA #$08 STA $2000   ; PPUCTRL：精灵 8×8？（bit3=0 背景 $0000，bit4=0 精灵 $0000）
      LDA #$1E STA $2001   ; PPUMASK：背景+精灵使能（$18），灰度 0
      LDX #$02
      BIT $2002 / BPL 等待 VBlank ×2（确保 PPU 稳定）
      LDX #$13 / LDA #$00 / STA $4000,X / DEX / BPL  ; 清 APU $4000–$4013
      LDA #$08 STA $4001 / STA $4005  ; 脉冲 sweep 禁用
      LDA #$8F STA $4015   ; APU 状态：脉冲1/2+三角+噪声使能（DMC 禁）
      LDA #$C0 STA $4017   ; 帧计数器：禁 IRQ + 4 步进
      LDX #$00 / STA $00,X / STA $0100,X / … / STA $0700,X / INX / BNE  ; 清 RAM $0000–$07FF
      LDX #$FF / TXS       ; 栈顶
      STX $0600            ; OAM 状态 = $FF（空闲）
      JSR $C272            ; MMC1 控制字 $1E
      LDA #$00 STA $40     ; 状态 = 0
      LDA #$1E STA $2A     ; PPUMASK 影子
      LDA #$08 STA $29     ; PPUCTRL 影子
      JSR $C1DD            ; 使能 NMI（$29 |= $80 → $2000）
      JMP $D043            ; 游戏主初始化
```

`$D043`（仍在固定银行）：

```
LDX #$FF / TXS
JSR $C23F          ; $0600=$F0，$2B=0，$2A &= $E7，LDA #$01 JMP $C1E7（等待循环）
LDA #$01 STA $60   ; CHR 队列忙=1（阻止 NMI 上传）
清零 $30,$61,$053A,$053B,$90,$92,$41,$B5,$B7,$4D,$75,$98,$7F
JSR $EFCE          ; 清 $0200–$040F
JSR $F0C8          ; $0600 起每 4 字节填 $F0（精灵隐藏，Y=$F0 在屏外）
JSR $C272          ; MMC1 控制字重写（保险）
DEC $60            ; 忙=0
JSR $D63D          ; 加载状态 0 头
JSR $D624          ; 分发状态 0（$C54E 间接跳转）
LDA $40 / JSR $C54E
```

## 2. NMI 中断（`$C003`）— 每帧 60Hz 的心脏

```asm
$C003 PHA / TYA / PHA / TXA / PHA     ; 保存 A/X/Y
      LDA #$00 STA $2001 / STA $2003  ; 关渲染（PPUMASK=0，OAMADDR=0）
      STA $2B                         ; PPU 忙=0
      LDA #$06 STA $4014              ; OAM DMA：$0600 页 → OAM
      LDA $2A / AND #$18 / BEQ $C042  ; 若背景/精灵使能：
        JSR $C521                     ;   调色板上传 $058E → $3F00
        JSR $C34F                     ;   CHR 上传队列处理
      LDA $2A STA $2001               ; 恢复 PPUMASK
      LDX #$00 / JSR $C2E5            ; 滚动更新（$10/$16 → $2005）
      LDA $2F / BEQ 跳过              ; 帧跳过计数
        JSR $C17C                     ;   手柄读取
      LDX $0600 / CPX #$50 / BCS 跳过 ; 若 $0600 < $50（游戏进行中）：
        JSR $C202                     ;   PPU 更新（PPUADDR+滚动+CHR 切换）
      LDA $2F / BEQ 跳过
        DEC $2F / INC $2D / BNE 跳过 / INC $2E  ; 帧计数器
$C100 PLA / TAX / PLA / TAY / PLA / RTI
```

NMI 后半（`$C042` 起）是**游戏逻辑分发**：

```
LDA $27 / BNE $C06C        ; MMC1 进行中？跳过（防重入）
LDX $1D / LDY $1E / JSR $C298  ; CHR 切换（背景/精灵银行）
LDA $26 / PHA              ; 保存当前 PRG 银行
LDA #$06 / JSR $C2C5       ; 切 PRG 银行 6（游戏逻辑）
JSR $8000                  ; ★ 游戏逻辑入口（见 docs/04）
LDX $B7 / BEQ 跳过
  LDA $F1 / AND #$0F / BNE 跳过
  STA $B7 / STX $B6 / STX $F0  ; 音效请求传递
PLA / JSR $C2C5            ; 恢复 PRG 银行
; 调色板动画（$62/$64/$65/$66，掩码表 $C174 = 01 02 04 08 10 20 40 80）
; 帧计数、$C202 调用…
```

## 3. MMC1 驱动

| 例程 | 作用 |
|---|---|
| `$C272` | 控制字：`LDA #$1E` → 5×`STA $9FFF`（LSR 串行）。另置 `$24/$25=$7F`、`$23=$1E`、`$27`  guard |
| `$C298` | CHR 切换：X→`$BFFF`（CHR0），Y→`$DFFF`（CHR1），各 5 次串行。`$27` guard |
| `$C2C5` | PRG 切换：A→`$EFFF` 5 次串行。若 A==`$26`（当前）直接返回。`$27` guard |

> MMC1 串行协议：每寄存器 5 位，LSB 先行，5 次写后生效；写 `$FFFF` bit7=1 可复位移位寄存器（复位桩即用此法）。

## 4. PPU 例程

| 例程 | 作用 |
|---|---|
| `$C2E5` | 滚动：`$10,X`→`$2005`（X），`$16,X`→`$2005`（Y），`$19/$13`→`$1C`→`$29`→`$2000`（Nametable 选择） |
| `$C202` | PPU 更新：等 VBlank（`BIT $2002 / BVC`），`$B4/$B5`→`$2006`，`JSR $C2E5`（X=1），`$1F/$20` CHR 切换，`DEC $2B` |
| `$C309` | Nametable 填充：A=PPUADDR 高字节，X=填充图块，Y=属性填充。`$2000` 起填 512/1024 字节，属性表 `$23C0` 填 64 字节 |
| `$C34F` | CHR 上传队列：`$053A` 头，`$053B` 流 `[hi,lo,count,data…]` → `$2006/$2007`。`$60` 忙时跳过。`$61` OR 进 `$29` |
| `$C521` | 调色板上传：`$058E`（32B）→`$3F00`，再写 `$3F00`（镜像） |
| `$C25E` | PPUCTRL 清 bit2（`$29 &= $FB` → `$2000`） |
| `$C1DD` | 使能 NMI：`$29 \|= $80` → `$2000` |

## 5. 手柄（`$C17C`）

```
LDA #$01 STA $4016 / LDA #$00 STA $4016  ; 锁存
LDX #$08
  LDA $4016 / ROR A / BCS 跳过 / ROR A / ROR $38  ; 读 8 位 → $38（手柄1）
  LDA $4017 / ROR A / BCS 跳过 / ROR A / ROR $39  ; 读 8 位 → $39（手柄2）
  DEX / BNE
LDX #$01
  LDA $38,X / LDY $36,X / STA $36,X / TYA / EOR #$FF / AND $38,X / STA $3C,X  ; 边沿 → $3C/$3D
  DEX / BPL
```

位序（ROR 移入，bit0 先读）：bit0=A，bit1=B，bit2=Select，bit3=Start，bit4=Up，bit5=Down，bit6=Left，bit7=Right。
`$38/$39`=当前，`$36/$37`=上一帧，`$3C/$3D`=本帧新按下。GMS 映射见 `docs/07`。

## 6. 状态机（`$40` + `$D610` 表 + `$D63D` 加载器 + `$C54E` 分发器）

**状态表**（`$D610`，每项 2 字节指针，索引 `$40*2`）：

| 状态 | 入口 | 推测含义（待动态验证） |
|---|---|---|
| 0 | `$D719` | 标题？ |
| 1 | `$D738` | 演示/过场？ |
| 2 | `$D785` | 游戏？ |
| 3 | `$D8A0` | 游戏（变体） |
| 4 | `$D8A0` | 同 3 |
| 5 | `$D813` | 游戏（变体） |
| 6 | `$D8A0` | 同 3 |
| 7 | `$D855` | 游戏（变体） |
| 8 | `$D871` | 游戏（变体） |
| 9 | `$D705` | 标题/Logo？ |

**状态头**（20 字节，`$D63D` 解析）：

```
[0]    flags：bit5（$20）→ 精灵大小（$28=$08/$10）+ PPUCTRL bit5；bits2-1（$06）→ PPUMASK（$2A）
[1-2]  指针1 $00/$01（PRG 银行 3 数据：调色板源 A → $05AE）
[3-4]  指针2 $02/$03（调色板源 B → $05BE；另 $058E/$059E 置 $0F）
[5-6]  CHR 上传参数（$46/$00）
[7]    $00（PPUADDR？）
[8]    A 参数（$C309 第一次调用）
[9-12] $1D–$20（CHR 银行号）
[13]   $10/$11（同值）
[14]   $13/$14
[15]   $16/$17
[16]   $19/$1A
[17-20] $0600–$0603（OAM 初始）
```

例（状态 0 @ `$D719`）：`02 81 B0 91 B0 40 00 24 1F 1F 1F 1F 00 00 00 00 F0 00 00 00`
→ flags=`$02`，指针 `$B081/$B091`（银行 3 调色板），CHR 银行 `31,31,31,0`（字体银行为主，符合标题画面）。

**分发器**（`$C54E`）：`STA $02 / PLA→$00 / PLA→$01 / LDA $02 ASL TAY INY LDA ($00),Y STA $02 INY LDA ($00),Y STA $03 JMP ($0002)` —— Capcom 经典“经表间接跳转”。

## 7. 其他内核例程

| 地址 | 作用 |
|---|---|
| `$C1E7` | 等待循环（`JSR $C202 / INC $2F / LDA $2F BNE` 自旋，`$31` 计数） |
| `$C23F` | 清 `$0600`，`$2B=0`，`$2A &= $E7`，`JMP $C1E7` |
| `$C576` | 栈返回地址改写（`$0104,X` +2，`($0E)` 指针）——CHR 队列续行用 |
| `$EFCE` | 清 `$0200–$040F` |
| `$F0C8` | `$0600` 每 4 字节填 `$F0`（精灵隐藏） |

## 8. GMS 对应

- NMI → GMS `Step` 事件（60Hz 固定步进，`room_speed=60`）
- `$C298/$C2C5` MMC1 → GMS 无需模拟，用精灵/背景资源切换代替（兼容层 `scr_nes_mmc1` 仅作参考/测试）
- `$C34F` 队列 → GMS 绘制队列（`scr_chr_queue`）
- `$C54E` 分发器 → GMS `switch (global.state)`（`scr_game_state`）
