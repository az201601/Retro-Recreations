-- fceux_palette_dump.lua - FCEUX helper to log the NES palette RAM every frame.
--
-- Palette RAM lives at $3F00-$3F1F (32 bytes: 4 background palettes +
-- 4 sprite palettes, 4 bytes each). NES colours are 6-bit NES master
-- palette indices; convert to RGB with any NES palette table.
--
-- Usage (in FCEUX on YOUR machine):
--   1. Load the ROM, let the attract loop reach the spotlight sweep.
--   2. File > Load Lua Script...  (or Debug > Lua > New Lua Script)
--   3. Pick this file. It runs one dump per frame (bounded by MAX_FRAMES).
--   4. Output goes to palette_log.txt next to the ROM.
--
-- NOTE: FCEUX exposes palette RAM via memory.readbyte on $3F00. If OAM
-- reads fail on your FCEUX version, use the PPU Viewer (Tools > PPU Viewer)
-- Sprites tab and screenshot that instead - same data, minus scripting.
-- API names can vary slightly between FCEUX 2.x releases; adjust if it errors.

local MAX_FRAMES = 3600
local frame = 0

local function log(s)
    local f = io.open("palette_log.txt", "a")
    f:write(s .. "\n")
    f:close()
end

local function dump_palette(tag)
    local bytes = {}
    for i = 0, 31 do
        bytes[#bytes + 1] = string.format("%02x", memory.readbyte(0x3F00 + i))
    end
    log(tag .. " frame=" .. frame .. " pal=" .. table.concat(bytes, " "))
end

memory.usememoryfillsave = false -- no-op guard for older cores
log("--- palette_log start (frame " .. emu.framecount() .. ") ---")

while frame < MAX_FRAMES do
    frame = frame + 1
    dump_palette("pal")
    emu.frameadvance()
end

log("--- done ---")
