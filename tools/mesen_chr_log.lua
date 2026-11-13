-- mesen_chr_log.lua
-- Mesen Lua：记录 MMC1 CHR/PRG 切换 + 状态，解 CHR 0-14 之谜（docs/09 V1）
-- 用法：Mesen -> 工具 -> Lua 脚本 -> 加载本文件 -> 运行 -> 播放游戏
-- 输出：mesen_chr_log.txt（与 ROM 同目录）
--
-- 原理：轮询 RAM（$1D-$20 CHR 银行，$26 PRG 银行，$40 状态），变化时记日志。
-- 不设断点，避免打断播放；如需断点，在 Mesen 调试器中手动加 $C298/$C2C5/$D63D。

local log_path = "mesen_chr_log.txt"
local f = io.open(log_path, "w")
local last = { chr0 = -1, chr1 = -1, prg = -1, state = -1 }

local function log(msg)
    local line = string.format("[%d] %s\n", emu.getFrameCount(), msg)
    f:write(line)
    f:flush()
    print(line)
end

log("=== Mesen CHR log start (Chip 'n Dale Rescue Rangers 2) ===")
log("RAM: $1D/$1E=CHR0/CHR1 (C04A), $1F/$20=CHR0/CHR1 (C225), $26=PRG, $40=state")

local function tick()
    -- Mesen Lua API: emu.readCpuMemory / emu.readMemory（版本差异，两种都试）
    local function rd(addr)
        if emu.readCpuMemory then
            return emu.readCpuMemory(addr, 1)[1]
        elseif emu.readMemory then
            return emu.readMemory(addr, 1)[1]
        else
            return 0
        end
    end
    local chr0 = rd(0x001D)
    local chr1 = rd(0x001E)
    local prg = rd(0x0026)
    local state = rd(0x0040)
    if chr0 ~= last.chr0 or chr1 ~= last.chr1 then
        log(string.format("CHR switch: CHR0=%d CHR1=%d (dec) / $%02X/$%02X", chr0, chr1, chr0, chr1))
        last.chr0, last.chr1 = chr0, chr1
    end
    if prg ~= last.prg then
        log(string.format("PRG switch: bank=%d", prg))
        last.prg = prg
    end
    if state ~= last.state then
        log(string.format("STATE change: $40=%d", state))
        last.state = state
    end
end

-- Mesen Lua 回调（每帧）
if emu.addEventCallback then
    emu.addEventCallback(tick, emu.eventType.frameStart)
else
    -- 旧版：用 while + emu.frameAdvance（需手动步进）
    log("WARN: emu.addEventCallback not found, polling loop (press Stop to end)")
    while true do
        tick()
        emu.frameAdvance()
    end
end
