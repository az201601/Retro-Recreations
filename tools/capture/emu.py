"""Minimal headless libretro frontend (ctypes) for the Mesen core."""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, "tools", "capture", "work")
os.makedirs(WORK, exist_ok=True)
import ctypes as C, numpy as np, os

CORE = os.environ.get('MESEN_CORE', os.path.join(WORK, 'mesen_libretro.so'))
ROM = os.path.join(ROOT, "Chip 'n Dale - Rescue Rangers 2 (USA).nes")

class GameInfo(C.Structure):
    _fields_ = [('path', C.c_char_p), ('data', C.c_void_p), ('size', C.c_size_t), ('meta', C.c_char_p)]
class Variable(C.Structure):
    _fields_ = [('key', C.c_char_p), ('value', C.c_char_p)]
class Geometry(C.Structure):
    _fields_ = [('base_width', C.c_uint), ('base_height', C.c_uint), ('max_width', C.c_uint), ('max_height', C.c_uint), ('aspect', C.c_float)]
class Timing(C.Structure):
    _fields_ = [('fps', C.c_double), ('sample_rate', C.c_double)]
class AVInfo(C.Structure):
    _fields_ = [('geometry', Geometry), ('timing', Timing)]

ENV_T = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
VID_T = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUD_T = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
AUDB_T = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLL_T = C.CFUNCTYPE(None)
INP_T = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)
LOG_T = C.CFUNCTYPE(None, C.c_int, C.c_char_p)

# joypad ids
B, Y, SELECT, START, UP, DOWN, LEFT, RIGHT, A = 0, 1, 2, 3, 4, 5, 6, 7, 8

KEYS = set()

class Emu:
    def __init__(self, options=None):
        self.opts = {k.encode(): v.encode() for k, v in (options or {}).items()}
        self.frame = None
        self.audio = []
        self.keys = set()
        self.pixfmt = 0
        self.seen_vars = set()
        self.lib = C.CDLL(CORE)
        self._sysdir = C.create_string_buffer(os.path.join(WORK, 'sys').encode())
        os.makedirs(os.path.join(WORK, 'sys'), exist_ok=True)
        self._env = ENV_T(self.env); self._vid = VID_T(self.vid); self._aud = AUD_T(self.aud)
        self._audb = AUDB_T(self.audb); self._poll = POLL_T(lambda: None); self._inp = INP_T(self.inp)
        self._log = LOG_T(lambda lvl, msg: None)
        L = self.lib
        L.retro_get_memory_data.restype = C.c_void_p
        L.retro_get_memory_size.restype = C.c_size_t
        L.retro_load_game.restype = C.c_bool
        L.retro_serialize_size.restype = C.c_size_t
        L.retro_set_environment(self._env)
        L.retro_init()
        L.retro_set_video_refresh(self._vid)
        L.retro_set_audio_sample(self._aud)
        L.retro_set_audio_sample_batch(self._audb)
        L.retro_set_input_poll(self._poll)
        L.retro_set_input_state(self._inp)
        self.rom = open(ROM, 'rb').read()
        gi = GameInfo(ROM.encode(), C.cast(C.c_char_p(self.rom), C.c_void_p), len(self.rom), None)
        assert L.retro_load_game(C.byref(gi))
        self.av = AVInfo(); L.retro_get_system_av_info(C.byref(self.av))
        self.n = 0

    def env(self, cmd, data):
        cmd &= 0xFFFF
        if cmd == 10:  # SET_PIXEL_FORMAT
            self.pixfmt = C.cast(data, C.POINTER(C.c_int))[0]; return True
        if cmd == 9 or cmd == 31:  # system / save dir
            C.cast(data, C.POINTER(C.c_char_p))[0] = C.cast(self._sysdir, C.c_char_p); return True
        if cmd == 15:  # GET_VARIABLE
            v = C.cast(data, C.POINTER(Variable))
            self.seen_vars.add(v[0].key)
            if v[0].key in self.opts:
                v[0].value = self.opts[v[0].key]; return True
            v[0].value = None; return False
        if cmd == 17:  # variable update
            C.cast(data, C.POINTER(C.c_bool))[0] = False; return True
        if cmd == 27:  # log interface
            return False
        return False

    def vid(self, data, w, h, pitch):
        if not data: return
        buf = C.string_at(data, pitch * h)
        a = np.frombuffer(buf, np.uint8).reshape(h, pitch)[:, :w * 4].reshape(h, w, 4)
        self.frame = a[:, :, [2, 1, 0]].copy()

    def aud(self, l, r): self.audio.append(np.array([[l, r]], np.int16))
    def audb(self, data, frames):
        self.audio.append(np.frombuffer(C.string_at(data, frames * 4), np.int16).reshape(-1, 2).copy()); return frames
    def inp(self, port, dev, idx, id_):
        if port == 0 and dev == 1 and id_ in KEYS: return 1
        return 0

    def step(self, keys=()):
        KEYS.clear(); KEYS.update(keys)
        self.lib.retro_run(); self.n += 1
        return self.frame

    def ram(self):
        p = self.lib.retro_get_memory_data(2)
        return np.frombuffer(C.string_at(p, 0x800), np.uint8)

    def ppu(self):
        p = self.lib.retro_get_memory_data(100)
        d = np.frombuffer(C.string_at(p, 0x3200), np.uint8)
        m=np.frombuffer(C.string_at(self.lib.retro_get_memory_data(101), 0x2000), np.uint8)
        ln=np.frombuffer(C.string_at(self.lib.retro_get_memory_data(102), 1920), np.uint8).reshape(240,8)
        return dict(chrmid=m, lines=ln, vram=d[:0x3000], pal=d[0x3000:0x3020], oam=d[0x3020:0x3120], ctrl=int(d[0x3121]),
                    mask=int(d[0x3122]), x=int(d[0x3123]), t=int(d[0x3124]) | int(d[0x3125]) << 8,
                    v=int(d[0x3126]) | int(d[0x3127]) << 8)
