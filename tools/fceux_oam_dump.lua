-- fceux_oam_dump.lua - FCEUX helper to dump sprite (OAM) coordinates
-- every N frames, e.g. while the spotlight sweep plays out.
--
-- OAM is 64 sprites x 4 bytes: Y, tile index, attributes, X.
-- The chip/Dale silhouettes are ~40-50 px tall, so ~6-8 OAM entries each
-- per frame; this log is what lets you reconstruct sprite *placement*
-- frame-perfectly instead of guessing it from screenshots.
--
-- Usage:
--   1. Load ROM, navigate to the scene you want.
--   2. Set SAMPLE_EVERY to how often to log (1 = every frame).
--   3. Run this script; it writes oam_dump.txt next to the ROM.
--
-- Reading OAM from Lua: some FCEUX builds expose it via memory.readbyte
-- on $0200 (typical sprite shadow RAM in zero/page 2 - check the debugger's
-- Memory Watch to find the exact address the game DMAs from $4014).
-- If your build blocks it, fall back to PPU Viewer > Sprites screenshots.

local MAX_FRAMES   = 3600
local SAMPLE_EVERY = 1
local OAM_BASE     = 0x0200   -- common shadow-RAM base; VERIFY in memory watch

local function log(s)
    local f = io.open("oam_dump.txt", "a")
    f:write(s .. "\n")
    f:close()
end

log("--- oam_dump start ---")
for frame = 1, MAX_FRAMES do
    if frame % SAMPLE_EVERY == 0 then
        local parts = {}
        for i = 0, 63 do
            local y  = memory.readbyte(OAM_BASE + i * 4 + 0)
            local t  = memory.readbyte(OAM_BASE + i * 4 + 1)
            local at = memory.readbyte(OAM_BASE + i * 4 + 2)
            local x  = memory.readbyte(OAM_BASE + i * 4 + 3)
            if y ~= 0xEF or x ~= 0xFF then  -- skip off-screen entries
                parts[#parts + 1] = string.format("[%02d x=%3d y=%3d tile=%02x a=%02x]", i, x, y, t, at)
            end
        end
        log("frame=" .. frame .. " " .. table.concat(parts, " "))
    end
    emu.frameadvance()
end
log("--- done ---")
