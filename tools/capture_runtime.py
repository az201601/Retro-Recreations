#!/usr/bin/env python3
"""Capture deterministic emulator reference frames and mixed audio via a libretro core."""
import argparse
import ctypes as c
import hashlib
import json
import struct
import wave
import zlib
from pathlib import Path


def png_chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)


def write_png(path, width, height, rgb):
    rows = b''.join(b'\0' + rgb[y*width*3:(y+1)*width*3] for y in range(height))
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + png_chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) + png_chunk(b'IDAT', zlib.compress(rows, 9)) + png_chunk(b'IEND', b''))


class GameInfo(c.Structure):
    _fields_ = [('path', c.c_char_p), ('data', c.c_void_p), ('size', c.c_size_t), ('meta', c.c_char_p)]


class Geometry(c.Structure):
    _fields_ = [('base_width', c.c_uint), ('base_height', c.c_uint), ('max_width', c.c_uint), ('max_height', c.c_uint), ('aspect_ratio', c.c_float)]


class Timing(c.Structure):
    _fields_ = [('fps', c.c_double), ('sample_rate', c.c_double)]


class AVInfo(c.Structure):
    _fields_ = [('geometry', Geometry), ('timing', Timing)]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('core', type=Path, help='libretro core shared library')
    p.add_argument('rom', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--frames', type=int, default=600)
    p.add_argument('--capture', default='120,300,600', help='comma-separated 1-based frames')
    p.add_argument('--start', default='', help='comma-separated 1-based frames to press START')
    p.add_argument('--press', default='', help='comma-separated FRAME:BUTTON, e.g. 800:A,900:RIGHT')
    p.add_argument('--save-state', action='store_true', help='save a core state at each captured frame')
    args = p.parse_args()
    captures = {int(x) for x in args.capture.split(',') if x}
    starts = {int(x) for x in args.start.split(',') if x}
    buttons = {'B': 0, 'SELECT': 2, 'START': 3, 'UP': 4, 'DOWN': 5, 'LEFT': 6, 'RIGHT': 7, 'A': 8}
    presses = {(n, buttons['START']) for n in starts}
    try:
        for item in filter(None, args.press.split(',')):
            number, button = item.split(':')
            presses.add((int(number), buttons[button.upper()]))
    except (ValueError, KeyError):
        p.error('invalid --press; use comma-separated FRAME:BUTTON (A, B, START, SELECT, UP, DOWN, LEFT, RIGHT)')
    if args.frames < 1 or any(n < 1 or n > args.frames for n in captures | {n for n, _ in presses}):
        p.error('frame numbers must be between 1 and --frames')
    args.output.mkdir(parents=True, exist_ok=True)
    core = c.CDLL(str(args.core.resolve()))
    ENV = c.CFUNCTYPE(c.c_bool, c.c_uint, c.c_void_p)
    VIDEO = c.CFUNCTYPE(None, c.c_void_p, c.c_uint, c.c_uint, c.c_size_t)
    AUDIO = c.CFUNCTYPE(None, c.c_int16, c.c_int16)
    BATCH = c.CFUNCTYPE(c.c_size_t, c.POINTER(c.c_int16), c.c_size_t)
    POLL = c.CFUNCTYPE(None)
    INPUT = c.CFUNCTYPE(c.c_int16, c.c_uint, c.c_uint, c.c_uint, c.c_uint)
    frame = 0
    latest = None
    audio = bytearray()
    pixel_format = 0

    @ENV
    def environment(cmd, data):
        nonlocal pixel_format
        if cmd == 10:  # SET_PIXEL_FORMAT
            pixel_format = c.cast(data, c.POINTER(c.c_uint))[0]
            return pixel_format in (0, 1, 2)
        if cmd == 3:  # GET_CAN_DUPE
            c.cast(data, c.POINTER(c.c_bool))[0] = True
            return True
        return False

    @VIDEO
    def video(data, width, height, pitch):
        nonlocal latest
        if not data:
            return
        raw = c.string_at(data, pitch * height)
        rgb = bytearray(width * height * 3)
        for y in range(height):
            for x in range(width):
                if pixel_format == 1:  # XRGB8888
                    value = struct.unpack_from('=I', raw, y*pitch+x*4)[0]
                    r, g, b = (value >> 16) & 255, (value >> 8) & 255, value & 255
                else:
                    value = struct.unpack_from('=H', raw, y*pitch+x*2)[0]
                    if pixel_format == 2:  # RGB565
                        r, g, b = ((value >> 11) & 31)*255//31, ((value >> 5) & 63)*255//63, (value & 31)*255//31
                    else:  # 0RGB1555
                        r, g, b = ((value >> 10) & 31)*255//31, ((value >> 5) & 31)*255//31, (value & 31)*255//31
                i = (y*width+x)*3
                rgb[i:i+3] = bytes((r, g, b))
        latest = (width, height, bytes(rgb))

    @AUDIO
    def sample(left, right):
        audio.extend(struct.pack('<hh', left, right))

    @BATCH
    def batch(data, count):
        audio.extend(c.string_at(data, count * 4))
        return count

    @POLL
    def poll():
        pass

    @INPUT
    def input_state(port, device, index, button):
        return int(port == 0 and device == 1 and index == 0 and (frame, button) in presses)

    for name, callback, typ in [('retro_set_environment', environment, ENV), ('retro_set_video_refresh', video, VIDEO), ('retro_set_audio_sample', sample, AUDIO), ('retro_set_audio_sample_batch', batch, BATCH), ('retro_set_input_poll', poll, POLL), ('retro_set_input_state', input_state, INPUT)]:
        fn = getattr(core, name)
        fn.argtypes = [typ]
        fn(callback)
    core.retro_init()
    content = args.rom.read_bytes()
    buf = c.create_string_buffer(content)
    path = str(args.rom.resolve()).encode()
    info = GameInfo(path, c.cast(buf, c.c_void_p), len(content), None)
    core.retro_load_game.argtypes = [c.POINTER(GameInfo)]
    core.retro_load_game.restype = c.c_bool
    if not core.retro_load_game(c.byref(info)):
        raise RuntimeError('core could not load ROM')
    av = AVInfo()
    core.retro_get_system_av_info(c.byref(av))
    saved = []
    states = []
    core.retro_serialize_size.restype = c.c_size_t
    core.retro_serialize.argtypes = [c.c_void_p, c.c_size_t]
    core.retro_serialize.restype = c.c_bool
    for frame in range(1, args.frames + 1):
        core.retro_run()
        if frame in captures and latest:
            name = 'frame_%06d.png' % frame
            write_png(args.output / name, *latest)
            saved.append(name)
            if args.save_state:
                size = core.retro_serialize_size()
                if not size:
                    raise RuntimeError('core does not support save states')
                state = c.create_string_buffer(size)
                if not core.retro_serialize(state, size):
                    raise RuntimeError('core could not serialize state')
                state_name = 'state_%06d.fcs' % frame
                (args.output / state_name).write_bytes(state.raw)
                states.append(state_name)
    with wave.open(str(args.output / 'mixed_audio.wav'), 'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(round(av.timing.sample_rate))
        wav.writeframes(audio)
    manifest = {'rom': args.rom.name, 'rom_sha256': hashlib.sha256(content).hexdigest(),
                'core': args.core.name, 'core_sha256': hashlib.sha256(args.core.read_bytes()).hexdigest(),
                'fps': av.timing.fps, 'sample_rate': av.timing.sample_rate,
                'frames': args.frames, 'start_pressed_frames': sorted(starts),
                'presses': [{'frame': n, 'button': next(k for k, v in buttons.items() if v == b)} for n, b in sorted(presses)],
                'screenshots': saved, 'states': states,
                'audio': 'mixed_audio.wav', 'note': 'Runtime reference only; mixed audio and composited frames are not isolated assets.'}
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    core.retro_unload_game()
    core.retro_deinit()
    print('Captured %d screenshots and %d audio bytes' % (len(saved), len(audio)))


if __name__ == '__main__':
    main()
