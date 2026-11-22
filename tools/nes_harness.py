#!/usr/bin/env python3
"""
nes_harness.py -- minimal headless libretro frontend for NES extraction work.

We drive a libretro NES core (Nestopia by default) frame by frame from Python:
no GUI, exact frame counts, pixel-perfect screenshots, raw audio capture,
joypad injection, savestates and system-RAM peeking.

Used for asset/audio extraction and for capturing "ground truth" reference
frames of Chip 'n Dale: Rescue Rangers 2 (USA). Nestopia renders with an
accurate NES palette (we default to Composite Direct FBX), so unlike jsnes the
colours are trustworthy for asset work.

(C libretro frontends would be faster, but Python makes the analysis glue --
pixel probing, tile matching, RAM diffing -- much easier.)
"""
from __future__ import annotations

import ctypes
import os
import sys

import numpy as np

# ---------------------------------------------------------------------------
# libretro constants (from libretro.h)
# ---------------------------------------------------------------------------
RETRO_DEVICE_JOYPAD = 1
RETRO_DEVICE_ID_JOYPAD_B = 0
RETRO_DEVICE_ID_JOYPAD_Y = 1
RETRO_DEVICE_ID_JOYPAD_SELECT = 2
RETRO_DEVICE_ID_JOYPAD_START = 3
RETRO_DEVICE_ID_JOYPAD_UP = 4
RETRO_DEVICE_ID_JOYPAD_DOWN = 5
RETRO_DEVICE_ID_JOYPAD_LEFT = 6
RETRO_DEVICE_ID_JOYPAD_RIGHT = 7
RETRO_DEVICE_ID_JOYPAD_A = 8
RETRO_DEVICE_ID_JOYPAD_X = 9
RETRO_DEVICE_ID_JOYPAD_MASK = 256

BUTTON_BITS = {
    "b": 0, "y": 1, "select": 2, "start": 3,
    "up": 4, "down": 5, "left": 6, "right": 7,
    "a": 8, "x": 9, "l": 10, "r": 11,
}

RETRO_REGION_NTSC = 0

RETRO_MEMORY_SAVE_RAM = 0
RETRO_MEMORY_SYSTEM_RAM = 2

RETRO_ENVIRONMENT_GET_CAN_DUPE = 3
RETRO_ENVIRONMENT_SET_MESSAGE = 6
RETRO_ENVIRONMENT_SET_PERFORMANCE_LEVEL = 8
RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY = 9
RETRO_ENVIRONMENT_SET_PIXEL_FORMAT = 10
RETRO_ENVIRONMENT_SET_INPUT_DESCRIPTORS = 11
RETRO_ENVIRONMENT_GET_VARIABLE = 15
RETRO_ENVIRONMENT_SET_VARIABLES = 16
RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE = 17
RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME = 18
RETRO_ENVIRONMENT_GET_LOG_INTERFACE = 27
RETRO_ENVIRONMENT_GET_PERF_INTERFACE = 28
RETRO_ENVIRONMENT_GET_CONTENT_DIRECTORY = 30
RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY = 31
RETRO_ENVIRONMENT_SET_CONTROLLER_INFO = 35
RETRO_ENVIRONMENT_SET_MEMORY_MAPS = 36 | 0x10000
RETRO_ENVIRONMENT_SET_GEOMETRY = 37
RETRO_ENVIRONMENT_GET_INPUT_DEVICE_CAPABILITIES = 24
RETRO_ENVIRONMENT_GET_CORE_ASSETS_DIRECTORY = 30
RETRO_ENVIRONMENT_GET_VFS_INTERFACE = 45 | 0x10000
RETRO_ENVIRONMENT_GET_MESSAGE_INTERFACE_VERSION = 59
RETRO_ENVIRONMENT_SET_MESSAGE_EXT = 60
RETRO_ENVIRONMENT_GET_INPUT_BITMASKS = 51 | 0x10000
RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION = 52
RETRO_ENVIRONMENT_GET_AUDIO_VIDEO_ENABLE = 47 | 0x10000

RETRO_PIXEL_0RGB1555 = 0
RETRO_PIXEL_XRGB8888 = 1
RETRO_PIXEL_RGB565 = 2


def joypad_mask(names) -> int:
    """Build a joypad bitmask from a list/tuple of button names."""
    mask = 0
    for n in names:
        mask |= 1 << BUTTON_BITS[n.lower()]
    return mask


# ---------------------------------------------------------------------------
# C callback types
# ---------------------------------------------------------------------------
ENV_CB = ctypes.CFUNCTYPE(
    ctypes.c_bool, ctypes.c_uint32, ctypes.c_void_p)
VIDEO_CB = ctypes.CFUNCTYPE(
    None, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_size_t)
AUDIO_CB = ctypes.CFUNCTYPE(
    None, ctypes.c_int16, ctypes.c_int16)
AUDIO_BATCH_CB = ctypes.CFUNCTYPE(
    ctypes.c_size_t, ctypes.POINTER(ctypes.c_int16), ctypes.c_size_t)
INPUT_POLL_CB = ctypes.CFUNCTYPE(None)
INPUT_STATE_CB = ctypes.CFUNCTYPE(
    ctypes.c_int16, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint)
LOG_CB = ctypes.CFUNCTYPE(
    None, ctypes.c_uint32, ctypes.c_char_p)


class RetroGameInfo(ctypes.Structure):
    _fields_ = [
        ("path", ctypes.c_char_p),
        ("data", ctypes.c_void_p),
        ("size", ctypes.c_size_t),
        ("meta", ctypes.c_char_p),
    ]


class RetroSystemInfo(ctypes.Structure):
    _fields_ = [
        ("library_name", ctypes.c_char_p),
        ("library_version", ctypes.c_char_p),
        ("valid_extensions", ctypes.c_char_p),
        ("need_fullpath", ctypes.c_bool),
        ("block_extract", ctypes.c_bool),
    ]


class RetroGameGeometry(ctypes.Structure):
    _fields_ = [
        ("base_width", ctypes.c_uint),
        ("base_height", ctypes.c_uint),
        ("max_width", ctypes.c_uint),
        ("max_height", ctypes.c_uint),
        ("aspect_ratio", ctypes.c_float),
    ]


class RetroSystemTiming(ctypes.Structure):
    _fields_ = [
        ("fps", ctypes.c_double),
        ("sample_rate", ctypes.c_double),
    ]


class RetroSystemAVInfo(ctypes.Structure):
    _fields_ = [
        ("geometry", RetroGameGeometry),
        ("timing", RetroSystemTiming),
    ]


class RetroVariable(ctypes.Structure):
    # c_void_p rather than c_char_p: we must hand out *pointers* to our own
    # buffers, and c_char_p field assignment mangles lifetimes.
    _fields_ = [("key", ctypes.c_void_p), ("value", ctypes.c_void_p)]


class RetroLogCallback(ctypes.Structure):
    _fields_ = [("log", LOG_CB)]


class NesEmu:
    """A tiny headless libretro runner specialised for NES cores."""

    def __init__(self, core_path: str, system_dir: str = "system"):
        self.core_path = core_path
        self.system_dir = os.path.abspath(system_dir)
        os.makedirs(self.system_dir, exist_ok=True)

        self.options: dict[str, str] = {}
        self._option_keys: set[str] = set()
        self._option_update = False
        # ctypes string buffers handed to the core must stay alive while the
        # core keeps their pointers; park them here.
        self._keepalive: list = []
        self.trace_env = False

        self.width = 256
        self.height = 240
        self.frame = np.zeros((240, 256, 4), dtype=np.uint8)
        self.audio: list[np.ndarray] = []
        self.joypad = [0] * 5      # bitmask per port (core can query 0..3+)
        self._input_bitmask_supported = False
        self.frames_run = 0

        self._env_cb = ENV_CB(self._env)
        self._video_cb = VIDEO_CB(self._video)
        self._audio_cb = AUDIO_CB(self._audio)
        self._audio_batch_cb = AUDIO_BATCH_CB(self._audio_batch)
        self._poll_cb = INPUT_POLL_CB(self._poll)
        self._state_cb = INPUT_STATE_CB(self._input_state)
        self._log_cb = LOG_CB(self._log)

        self.lib = ctypes.CDLL(core_path)
        self._bind()
        self.lib.retro_set_environment(self._env_cb)
        self.lib.retro_set_video_refresh(self._video_cb)
        self.lib.retro_set_audio_sample(self._audio_cb)
        self.lib.retro_set_audio_sample_batch(self._audio_batch_cb)
        self.lib.retro_set_input_poll(self._poll_cb)
        self.lib.retro_set_input_state(self._state_cb)
        self.lib.retro_init()

    # -- C function signatures --------------------------------------------
    def _bind(self):
        L = self.lib
        L.retro_set_environment.argtypes = [ENV_CB]
        L.retro_set_video_refresh.argtypes = [VIDEO_CB]
        L.retro_set_audio_sample.argtypes = [AUDIO_CB]
        L.retro_set_audio_sample_batch.argtypes = [AUDIO_BATCH_CB]
        L.retro_set_input_poll.argtypes = [INPUT_POLL_CB]
        L.retro_set_input_state.argtypes = [INPUT_STATE_CB]
        L.retro_init.restype = None
        L.retro_deinit.restype = None
        L.retro_api_version.restype = ctypes.c_uint
        L.retro_get_system_info.argtypes = [ctypes.POINTER(RetroSystemInfo)]
        L.retro_get_system_av_info.argtypes = [ctypes.POINTER(RetroSystemAVInfo)]
        L.retro_set_controller_port_device.argtypes = [ctypes.c_uint, ctypes.c_uint]
        L.retro_load_game.argtypes = [ctypes.POINTER(RetroGameInfo)]
        L.retro_load_game.restype = ctypes.c_bool
        L.retro_unload_game.restype = None
        L.retro_run.restype = None
        L.retro_reset.restype = None
        L.retro_serialize_size.restype = ctypes.c_size_t
        L.retro_serialize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        L.retro_serialize.restype = ctypes.c_bool
        L.retro_unserialize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        L.retro_unserialize.restype = ctypes.c_bool
        L.retro_get_memory_data.argtypes = [ctypes.c_uint]
        L.retro_get_memory_data.restype = ctypes.c_void_p
        L.retro_get_memory_size.argtypes = [ctypes.c_uint]
        L.retro_get_memory_size.restype = ctypes.c_size_t

    # -- callbacks ---------------------------------------------------------
    def _log(self, level, msg):
        try:
            print("[core]", msg.decode("utf-8", "replace").rstrip(), file=sys.stderr)
        except Exception:
            pass

    def _set_cstr(self, data, s: str):
        """Write a C string pointer into a callback out-param, kept alive."""
        buf = ctypes.create_string_buffer(s.encode())
        self._keepalive.append(buf)
        ctypes.cast(data, ctypes.POINTER(ctypes.c_void_p))[0] = ctypes.cast(buf, ctypes.c_void_p)

    def _env(self, cmd, data):
        if self.trace_env:
            print(f"[env] cmd={cmd} (0x{cmd:x})", file=sys.stderr)
        if cmd == RETRO_ENVIRONMENT_GET_CAN_DUPE:
            ctypes.cast(data, ctypes.POINTER(ctypes.c_bool))[0] = True
            return True
        if cmd == RETRO_ENVIRONMENT_SET_PIXEL_FORMAT:
            fmt = ctypes.cast(data, ctypes.POINTER(ctypes.c_uint))[0]
            return fmt in (RETRO_PIXEL_XRGB8888, RETRO_PIXEL_RGB565)
        if cmd in (RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY,
                   RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY,
                   RETRO_ENVIRONMENT_GET_CONTENT_DIRECTORY,
                   RETRO_ENVIRONMENT_GET_CORE_ASSETS_DIRECTORY):
            self._set_cstr(data, self.system_dir)
            return True
        if cmd == RETRO_ENVIRONMENT_GET_VARIABLE:
            var = ctypes.cast(data, ctypes.POINTER(RetroVariable)).contents
            key = ctypes.string_at(var.key).decode() if var.key else ""
            val = self.options.get(key)
            if val is not None:
                buf = ctypes.create_string_buffer(val.encode())
                self._keepalive.append(buf)
                var.value = ctypes.addressof(buf)
                return True
            var.value = 0
            return False
        if cmd == RETRO_ENVIRONMENT_SET_VARIABLES:
            p = ctypes.cast(data, ctypes.POINTER(RetroVariable))
            i = 0
            while p[i].key:
                key = ctypes.string_at(p[i].key).decode()
                self._option_keys.add(key)
                # legacy format: "Description;value1|value2|..."
                raw = ctypes.string_at(p[i].value).decode() if p[i].value else ""
                vals = raw.split(";", 1)[1] if ";" in raw else raw
                first = vals.split("|")[0].strip()
                self.options.setdefault(key, first)
                i += 1
            self._option_update = True
            return True
        if cmd == RETRO_ENVIRONMENT_GET_VARIABLE_UPDATE:
            ctypes.cast(data, ctypes.POINTER(ctypes.c_bool))[0] = self._option_update
            self._option_update = False
            return True
        if cmd == RETRO_ENVIRONMENT_GET_CORE_OPTIONS_VERSION:
            # Claim "no core options support" -> core falls back to the simple
            # SET_VARIABLES interface we implement above.
            ctypes.cast(data, ctypes.POINTER(ctypes.c_uint))[0] = 0
            return True
        if cmd == RETRO_ENVIRONMENT_GET_LOG_INTERFACE:
            ctypes.cast(data, ctypes.POINTER(RetroLogCallback)).contents.log = self._log_cb
            return True
        if cmd == RETRO_ENVIRONMENT_GET_INPUT_BITMASKS:
            self._input_bitmask_supported = True
            return True
        if cmd == RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME:
            return True
        # Everything else (memory maps, perf, vfs, messages, descriptors...):
        # not needed for headless capture.
        return False

    def _video(self, data, width, height, pitch):
        if not data:
            return
        w, h = int(width), int(height)
        self.width, self.height = w, h
        buf = (ctypes.c_ubyte * (pitch * h)).from_address(data)
        arr = np.ctypeslib.as_array(buf).reshape(h, pitch)
        frame = arr[:, : w * 4].reshape(h, w, 4).copy()
        self.frame = frame

    def _audio(self, left, right):
        self.audio.append(np.array([left, right], dtype=np.int16))

    def _audio_batch(self, data, frames):
        n = int(frames)
        if n and data:
            buf = (ctypes.c_int16 * (n * 2)).from_address(ctypes.addressof(data.contents))
            arr = np.ctypeslib.as_array(buf).copy()
            self.audio.append(arr)
        return n

    def _poll(self):
        pass

    def _input_state(self, port, device, index, id_):
        if device == RETRO_DEVICE_JOYPAD:
            mask = self.joypad[port] if port < len(self.joypad) else 0
            if id_ == RETRO_DEVICE_ID_JOYPAD_MASK and self._input_bitmask_supported:
                return mask & 0xFFFF
            if id_ < 16:
                return (mask >> id_) & 1
        return 0

    # -- driving -----------------------------------------------------------
    def load(self, rom_path: str, pal: str = "composite-direct-fbx"):
        self.options["nestopia_palette"] = pal
        self.options["nestopia_favored_system"] = "auto"
        self.options["nestopia_aspect"] = "ntsc"
        self.options["nestopia_nospritelimit"] = "disabled"
        self.options["nestopia_overclock"] = "1x"
        self.options["nestopia_blargg_ntsc_filter"] = "disabled"
        self.options["nestopia_audio_filter"] = "disabled"
        info = RetroGameInfo()
        info.path = os.path.abspath(rom_path).encode()
        # This core copies the ROM from memory (info->data / info->size);
        # passing only a path leaves it with an empty image.
        with open(rom_path, "rb") as f:
            rom_bytes = f.read()
        rom_buf = ctypes.create_string_buffer(rom_bytes)
        self._keepalive.append(rom_buf)
        info.data = ctypes.cast(rom_buf, ctypes.c_void_p)
        info.size = len(rom_bytes)
        info.meta = None
        if not self.lib.retro_load_game(ctypes.byref(info)):
            raise RuntimeError("retro_load_game failed for " + rom_path)
        for p in (0, 1):
            self.lib.retro_set_controller_port_device(p, RETRO_DEVICE_JOYPAD)
        av = RetroSystemAVInfo()
        self.lib.retro_get_system_av_info(ctypes.byref(av))
        self.fps = av.timing.fps
        self.sample_rate = int(av.timing.sample_rate)
        return self

    def set_buttons(self, *names, port=0):
        self.joypad[port] = joypad_mask(names)

    def release_all(self):
        self.joypad = [0] * 5

    def run(self, n: int = 1, inputs=None):
        """Run n frames. `inputs` maps frame offset -> button list."""
        for i in range(n):
            if inputs and i in inputs:
                btns = inputs[i]
                self.joypad[0] = joypad_mask(btns) if btns else 0
            self.lib.retro_run()
            self.frames_run += 1

    def audio_array(self) -> np.ndarray:
        """Concatenated int16 stereo audio since last clear_audio()."""
        if not self.audio:
            return np.zeros((0, 2), dtype=np.int16)
        return np.concatenate(self.audio).reshape(-1, 2)

    def clear_audio(self):
        self.audio = []

    def rgb_frame(self) -> np.ndarray:
        """(h, w, 3) uint8 RGB copy of the last video frame."""
        return self.frame[:, :, [2, 1, 0]].copy()   # XRGB -> RGB

    def screenshot(self, path: str):
        from PIL import Image
        Image.fromarray(self.rgb_frame(), "RGB").save(path)
        return path

    def savestate(self) -> bytes:
        n = self.lib.retro_serialize_size()
        buf = ctypes.create_string_buffer(n)
        if not self.lib.retro_serialize(buf, n):
            raise RuntimeError("retro_serialize failed")
        return buf.raw

    def loadstate(self, data: bytes):
        buf = ctypes.create_string_buffer(data)
        if not self.lib.retro_unserialize(buf, len(data)):
            raise RuntimeError("retro_unserialize failed")

    def ram(self) -> bytes:
        """CPU work RAM snapshot ($0000-$07FF)."""
        p = self.lib.retro_get_memory_data(RETRO_MEMORY_SYSTEM_RAM)
        n = self.lib.retro_get_memory_size(RETRO_MEMORY_SYSTEM_RAM)
        if not p or not n:
            return b""
        return ctypes.string_at(p, n)

    def sram(self) -> bytes:
        p = self.lib.retro_get_memory_data(RETRO_MEMORY_SAVE_RAM)
        n = self.lib.retro_get_memory_size(RETRO_MEMORY_SAVE_RAM)
        if not p or not n:
            return b""
        return ctypes.string_at(p, n)

    def close(self):
        try:
            self.lib.retro_unload_game()
            self.lib.retro_deinit()
        except Exception:
            pass


if __name__ == "__main__":
    # smoke test: boot the ROM headless, run 300 frames, dump title frame
    rom = sys.argv[1] if len(sys.argv) > 1 else "Chip 'n Dale - Rescue Rangers 2 (USA).nes"
    core = os.environ.get("NES_CORE", "/tmp/nestopia/libretro/nestopia_libretro.so")
    emu = NesEmu(core).load(rom)
    print("core:", emu.lib.retro_api_version(), "fps:", emu.fps, "rate:", emu.sample_rate)
    emu.run(300)
    emu.screenshot("tools/_smoke_title.png")
    print("wrote tools/_smoke_title.png ; ram[0x30..] =", emu.ram()[0x30:0x60].hex())
    emu.close()
