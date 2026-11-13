#!/usr/bin/env python3
"""Python port of obj_prison (Create / End Step / Draw) checked pixel for pixel against the capture_prison.py runs.
Keep in sync with recreation/03_night_scene/gml/obj_prison_*.gml"""
import os, sys
import numpy as np
from PIL import Image
from scenario import load
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = os.path.join(ROOT, 'recreation', '03_night_scene', 'assets', 'sprites') + '/'
def ld(name, n): return [np.array(Image.open('%s%s_%d.png' % (A, name, i)).convert('RGBA')) for i in range(n)]
FAR = ld('spr_prison_far', 6); FENCE = ld('spr_prison_fence', 6); BEAM = [ld('spr_prison_beam_a', 5), ld('spr_prison_beam_b', 5)]
BLIMP = ld('spr_prison_blimp', 16)

GAIN = [0] + [round((95.88 / (8128.0 / v + 100)) / (95.88 / (8128.0 / 15 + 100)), 3) for v in range(1, 16)]   # NES pulse DAC, volume 1..15

class Prison:
    def __init__(s, pad_prev=0):          # the ns_* part of Create
        s.t = -2; s.pad_prev = pad_prev
        s.blimp_x = 0; s.blimp_y = 24 * 256; s.blimp_lit = 0
        s.beam_mode = 0; s.beam = 0                      # 0 off, 1 running, 2 frozen (fades with the rest)
        s.exit_t = -1; s.fade_t0 = -1; s.fade_at1 = -1; s.fade_at2 = -1; s.skipped = False
        s.lv_bg = 0; s.lv_blimp = 0; s.lv_beam = 0       # fade-out levels 0..4 (4 = black)
        s.vol = 15; s.done = False; s.alarm_skip = -1
        s.alarm = []                                     # frames on which the alarm sound is (re)started
    def step(s, pad):                     # section 5 of Step; pad bit 1 = START
        s.t += 1; t = s.t
        pressed = pad & (s.pad_prev ^ 31); s.pad_prev = pad
        if s.done: return
        # blimp
        if (44 <= t <= 331) or t >= 524: s.blimp_x += 128
        if 396 <= t <= 427: s.blimp_y += 128
        if 492 <= t <= 523: s.blimp_y -= 128
        # leaving: START (accepted from t = 13) and the end of the script on t = 1003.  Each of the two (re)starts the
        # 4-frame fade clock 34 frames later; the first one decides when the scene ends
        if (pressed & 1) and t >= 13 and not s.skipped and (s.exit_t < 0 or t < s.exit_t + 55):
            s.skipped = True; s.fade_at1 = t + 34
            s.alarm_skip = t + 2                         # START swallows an alarm restart that is due right now
            if s.exit_t < 0: s.exit_t = t
        if t == 1003:
            s.fade_at2 = t + 34
            if s.exit_t < 0: s.exit_t = t
        if s.fade_t0 >= 0 and t > s.fade_t0 and (t - s.fade_t0) % 4 == 0:      # one fade step
            s.lv_bg = min(s.lv_bg + 1, 4); s.lv_blimp = min(s.lv_blimp + 1, 4)
            if s.beam_mode == 2: s.lv_beam = min(s.lv_beam + 1, 4)
        if s.exit_t >= 0 and t > s.exit_t and (t - s.exit_t) % 4 == 0 and s.vol > 1: s.vol -= 1
        # the lights come on, even when the picture is already fading or black
        if t == 525: s.blimp_lit = 1; s.lv_blimp = 0; s.beam_mode = 1
        if s.beam_mode == 1 and t > 526 and (t - 526) % 64 == 0: s.beam = 1 - s.beam
        if t == s.fade_at1 or t == s.fade_at2:
            s.fade_t0 = t
            if s.beam_mode == 1: s.beam_mode = 2 if t > 525 else 0
        if s.exit_t >= 0 and t == s.exit_t + 57: s.done = True; return
        if t >= 526 and (t - 526) % 49 == 0 and t != s.alarm_skip: s.alarm.append(t)                 # 49-frame alarm, restarted for ever
    def draw(s):
        scr = np.zeros((240, 256, 3), np.uint8); t = s.t
        def blit(img, dx, dy, clip_left=0):
            h, w = img.shape[:2]
            x0 = max(dx, clip_left); y0 = max(dy, 0); x1 = min(dx + w, 256); y1 = min(dy + h, 240)
            if x1 <= x0 or y1 <= y0: return
            src = img[y0 - dy:y1 - dy, x0 - dx:x1 - dx]; m = src[..., 3] > 0
            scr[y0:y1, x0:x1][m] = src[..., :3][m]
        if t < 0 or s.done or (s.exit_t >= 0 and t >= s.exit_t + 55): return scr
        top = min(max(t - 43, 0), 256); bot = (2 * min(max(t - 42, 0), 256)) % 512
        if s.lv_bg < 3:
            sub = min(t // 4, 3) if s.lv_bg == 0 else 3 + s.lv_bg
            blit(FAR[sub], -top, 0)
            blit(FENCE[sub], -bot, 179); blit(FENCE[sub], 512 - bot, 179)
        if s.beam_mode > 0 and t >= 526:
            if s.beam_mode == 1: blit(BEAM[1 - s.beam][4], 0, 0)          # the unlit beam has the sky colour: shows on a black screen
            if s.lv_beam < 4: blit(BEAM[s.beam][s.lv_beam], 0, 0)
        if t >= 44 and s.lv_blimp < 4:
            prop = ((t + 12) >> 3) & 1
            blit(BLIMP[s.blimp_lit * 8 + s.lv_blimp * 2 + prop], (s.blimp_x >> 8) - 32, (s.blimp_y >> 8) + 1, clip_left=8)
        return scr

if __name__ == '__main__':
    from capture_prison import RUNS
    total = frames = sbad = 0
    for name, (sched, nfr, f0) in RUNS.items():
        d = load('prison_' + name); R = max(f for f in sched if f <= 1210) + 1; t0 = R + 41
        g = Prison(); bad = []; vbad = []; n = 0
        g.t = (f0 - t0) - 1
        for f in range(f0, nfr):
            g.step(1 if 3 in sched.get(f, ()) else 0)
            if g.done: break
            n += 1
            if not np.array_equal(g.draw(), d['frames'][f - f0]): bad.append(f)
            w = [v for a, v in d['apu'][f - f0] if a == 0x4004 and v != 0x70]      # square 2 volume written by the game
            playing = g.alarm and g.t - g.alarm[-1] < 49
            if g.t >= 527 and w and (w[-1] & 15) != (g.vol if playing else 0): vbad.append(f)
        # the game's sound driver starts a sound on a frame whose first register write is $400C=$F0; it is audible one frame later
        mk = [i + f0 - t0 + 1 for i, w in enumerate(d['apu'][:n]) if w and w[0] == (0x400C, 0xF0) and i + f0 - t0 >= 0]
        ok = mk == g.alarm
        total += len(bad); frames += n; sbad += len(vbad) + (not ok)
        print('%-7s frames %4d picture mismatches %d %s | START %-5s end t=%s | alarm starts %d %s, volume mismatches %d' % (
            name, n, len(bad), bad[:8], g.skipped, g.exit_t + 57 if g.exit_t >= 0 else None, len(g.alarm), 'ok' if ok else 'DIFFER %s %s' % (mk[-3:], g.alarm[-3:]), len(vbad)))
    print('frames compared %d, mismatching frames %d, sound check failures %d' % (frames, total, sbad))
