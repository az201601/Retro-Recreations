-- bizhawk_chr_log.lua
-- BizHawk Lua（NES）：记录 CHR/PRG/状态（docs/09 V1）
-- 用法：BizHawk -> Tools -> Lua Console -> Load Script -> 本文件 -> Play
-- 输出：bizhawk_chr_log.txt

local f = io.open("bizhawk_chr_log.txt", "w")
local last = { chr0 = -1, chr1 = -1, prg = -1, state = -1 }

local function log(msg)
    local line = string.format("[%d] %s\n", emu.framecount(), msg)
    f:write(line)
    f:flush()
    print(line)
end

log("=== BizHawk CHR log start ===")

while true do
    local chr0 = memory.readbyte(0x001D)
    local chr1 = memory.readbyte(0x001E)
    local prg = memory.readbyte(0x0026)
    local state = memory.readbyte(0x0040)
    if chr0 ~= last.chr0 or chr1 ~= last.chr1 then
        log(string.format("CHR switch: CHR0=%d CHR1=%d", chr0, chr1))
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
    emu.frameadvance()
end
