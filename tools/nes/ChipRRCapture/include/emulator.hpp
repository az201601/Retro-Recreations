//  Program:      nes-py
//  File:         emulator.hpp
//  Description:  This class houses the logic and data for an NES emulator
//
//  Copyright (c) 2019 Christian Kauten. All rights reserved.
//

#ifndef EMULATOR_HPP
#define EMULATOR_HPP

#include <string>
#include "common.hpp"
#include "cartridge.hpp"
#include "controller.hpp"
#include "cpu.hpp"
#include "ppu.hpp"
#include "main_bus.hpp"
#include "picture_bus.hpp"

namespace NES {

/// An NES Emulator and OpenAI Gym interface
class Emulator {
 private:
    /// The number of cycles in 1 frame
    static const int CYCLES_PER_FRAME = 29781;
    /// the virtual cartridge with ROM and mapper data
    Cartridge cartridge;
    /// the 2 controllers on the emulator
    Controller controllers[2];

    /// the main data bus of the emulator
    MainBus bus;
    /// the picture bus from the PPU of the emulator
    PictureBus picture_bus;
    /// The emulator's CPU
    CPU cpu;
    /// the emulators' PPU
    PPU ppu;

    /// the main data bus of the emulator
    MainBus backup_bus;
    /// the picture bus from the PPU of the emulator
    PictureBus backup_picture_bus;
    /// The emulator's CPU
    CPU backup_cpu;
    /// the emulators' PPU
    PPU backup_ppu;

 public:
    /// [ChipRRCapture] the mapper in use (SxROM/MMC1 on this cartridge)
    inline Mapper* raw_mapper() { return bus.raw_mapper(); }
    /// [ChipRRCapture] render frames without sprites (clean backgrounds)
    inline void raw_set_hide_sprites(bool v) { ppu.raw_hide_sprites = v; }
    /// [ChipRRCapture] the picture bus (VRAM / palette access)
    inline PictureBus& raw_picture_bus() { return picture_bus; }
    /// [ChipRRCapture] the PPU (OAM access)
    inline PPU& raw_ppu() { return ppu; }
    /// [ChipRRCapture] JOY1 read log
    inline const NES_Byte* raw_joy_log() { return bus.joy_log; }
    inline int raw_joy_reads() { return bus.joy_reads; }
    inline NES_Byte raw_joy_pressed() { return bus.joy_pressed; }
    inline int raw_joy_bursts() { return bus.joy_bursts; }
    inline int raw_joy2_reads() { return bus.joy2_reads; }
    /// [ChipRRCapture] the CPU (for tracing)
    inline CPU& raw_cpu() { return cpu; }
    /// [ChipRRCapture] the main bus
    inline MainBus& raw_bus() { return bus; }
    /// [ChipRRCapture] the frame limit the PPU works towards
    static const int RAW_CYCLES_PER_FRAME = 29781;
    /// [ChipRRCapture] cycles consumed so far in the current manual frame
    int raw_cycle_budget = 0;
    /// [ChipRRCapture] step exactly one CPU instruction
    inline void step_instruction() {
        int want = cpu.op_count + 1;
        do {
            cpu.cycle(bus);
            ppu.cycle(picture_bus);
            ++raw_cycle_budget;
        } while (cpu.op_count < want);
    }
    /// [ChipRRCapture] step one whole frame instruction by instruction
    inline void step_manual_frame() {
        raw_cycle_budget = 0;
        while (raw_cycle_budget < RAW_CYCLES_PER_FRAME) step_instruction();
    }

    /// [ChipRRCapture] the CPU RAM buffer
    inline NES_Byte* raw_ram() { return bus.get_memory_buffer(); }

    /// The width of the NES screen in pixels
    static const int WIDTH = SCANLINE_VISIBLE_DOTS;
    /// The height of the NES screen in pixels
    static const int HEIGHT = VISIBLE_SCANLINES;

    /// Initialize a new emulator with a path to a ROM file.
    ///
    /// @param rom_path the path to the ROM for the emulator to run
    ///
    explicit Emulator(std::string rom_path);

    /// Return a 32-bit pointer to the screen buffer's first address.
    ///
    /// @return a 32-bit pointer to the screen buffer's first address
    ///
    inline NES_Pixel* get_screen_buffer() { return ppu.get_screen_buffer(); }

    /// Return a 8-bit pointer to the RAM buffer's first address.
    ///
    /// @return a 8-bit pointer to the RAM buffer's first address
    ///
    inline NES_Byte* get_memory_buffer() { return bus.get_memory_buffer(); }

    /// Return a pointer to a controller port
    ///
    /// @param port the port of the controller to return the pointer to
    /// @return a pointer to the byte buffer for the controller state
    ///
    inline NES_Byte* get_controller(int port) {
        return controllers[port].get_joypad_buffer();
    }

    /// Load the ROM into the NES.
    inline void reset() { cpu.reset(bus); ppu.reset(); }

    /// Perform a step on the emulator, i.e., a single frame.
    void step();

    /// Create a backup state on the emulator.
    inline void backup() {
        backup_bus = bus;
        backup_picture_bus = picture_bus;
        backup_cpu = cpu;
        backup_ppu = ppu;
    }

    /// Restore the backup state on the emulator.
    inline void restore() {
        bus = backup_bus;
        picture_bus = backup_picture_bus;
        cpu = backup_cpu;
        ppu = backup_ppu;
    }
};

}  // namespace NES

#endif  // EMULATOR_HPP
