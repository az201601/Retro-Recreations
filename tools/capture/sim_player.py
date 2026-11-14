#!/usr/bin/env python3
"""Python port of deliverable 6: obj_stage1 (End Step, Draw), obj_player (Create, User Defined 0, Draw) and the four
scr_pl_* scripts, compared with the capture_player.py recordings.  Keep in sync with recreation/06_level1_player/gml/
and recreation/07_level1_dale/gml/ (the dl_ runs are Dale: other sprite tables and strip, same movement).

Per frame it compares (a) the player's state with the NES memory: state, position, speed, picture, direction, body
height, camera, lives; (b) the player's sprite tiles with the NES sprite list; (c) the whole picture.  Left out of the
picture comparison: the 8x8 boxes of all other NES sprites (hearts, enemies) and the bonus items the player has touched
(they disappear in the original; that is a later step).  A run is compared until the player touches an enemy.
The exit runs use B before the last screen (the recorded route), so there the port is started from the NES memory
on frame 3632.    usage: sim_player.py [job ...]"""
import os, pickle, sys
import numpy as np
from PIL import Image
from scenario import load
from emu import WORK, START, A, B, SELECT, UP, DOWN, LEFT, RIGHT
import capture_player as CP
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BG = [np.array(Image.open('%s/recreation/05_level1_map/assets/sprites/spr_lv1a_bg_%d.png' % (ROOT, i)).convert('RGB')) for i in range(56)]
TABS = pickle.load(open(os.path.join(WORK, 'pl_tables.pkl'), 'rb'))
def character(c):
    """global.p1_char: 0 Chip, 1 Dale. Sets the sprite tables and the sprite strip the port uses."""
    global T, CHIP
    T = TABS['dale'] if c else TABS
    st = Image.open('%s/recreation/%s/assets/sprites/spr_%s_strip%d.png' % (ROOT, '07_level1_dale' if c else '06_level1_player', 'dale' if c else 'chip', T['n'])).convert('RGBA')
    CHIP = [np.array(st.crop((k * 8, 0, k * 8 + 8, 8))) for k in range(T['n'])]
BL = pickle.load(open(os.path.join(WORK, 'lv1_blocks.pkl'), 'rb'))
MAP = [''.join(str(int(v)) for v in row) for row in BL['cls']]
PADBIT = {START: 1, SELECT: 2, A: 4, UP: 8, DOWN: 16, B: 32, LEFT: 64, RIGHT: 128}

class Player:                                   # obj_player
    def __init__(s, stage): s.stage = stage; s.create()
    def create(s):
        s.p_x = 24; s.p_y = 192; s.p_ysub = 0; s.p_xv = 0; s.p_yv = 0; s.p_face = 1; s.p_h = 22; s.p_state = 5; s.p_cnt = 0
        s.p_pose = 2; s.p_walk = 0; s.p_blink = 0; s.p_pic = 5; s.p_auto = False; s.p_pad = 0; s.p_pressed = 0
        s.p_landed = False; s.p_out = False; s.p_restart = False
        s.s_x = s.p_x; s.s_y = s.p_y; s.s_pic = 0; s.s_face = 1; s.s_vis = True
    # scripts
    def row(s, y, kind):
        r = y // 16
        if r < 0 or r > 14: return False
        wx = s.p_x + s.stage.lv_cam_x
        for c in range((wx - 6) // 16, (wx + 5) // 16 + 1):
            if 0 <= c < 128 and int(MAP[r][c]) >= kind: return True
        return False
    def floor(s):
        if s.p_y < 0 or s.p_y > 255: return False
        if s.p_y % 16: return False
        if not s.row(s.p_y, 1): return False
        s.p_ysub = 0; s.p_yv = 0; return True
    def wall(s, x):
        if s.p_y < 1 or s.p_y > 255: return False
        c = (x + s.stage.lv_cam_x) // 16
        if c < 0 or c > 127: return False
        for r in range(max(s.p_y - s.p_h, 0) // 16, min((s.p_y + 15) // 16 - 1, 14) + 1):
            if int(MAP[r][c]) >= 2: return True
        return False
    def move_y(s):
        t = s.p_y * 16 + s.p_ysub + s.p_yv; s.p_y = t // 16; s.p_ysub = t - s.p_y * 16
    def fall(s): s.p_pose = 2; s.p_yv = 0; s.p_state = 1
    def stand(s): s.p_state = 5; s.p_pose = 0; s.p_cnt = 0
    def jump(s): s.p_yv = -110; s.p_state = 8; s.p_pose = 2
    def user0(s):
        held = s.p_pad; pressed = s.p_pressed
        if s.p_auto: held = 128; pressed = 0
        s.p_landed = False
        st = s.p_state
        if st in (5, 20):
            if st == 5 and not s.floor(): s.fall()
            elif held & 16: s.p_state = 3; s.p_cnt = 0
            elif pressed & 4: s.jump()
            elif not held & 192: s.stand()
            else: s.p_pose = 1; s.p_walk = (s.p_cnt // 8) % 4; s.p_cnt = (s.p_cnt + 1) % 256
        elif st == 3:
            if not s.floor(): s.fall()
            else:
                s.p_pose = 4
                if not held & 16: s.stand()
                elif pressed & 4 and not s.row(s.p_y, 2): s.fall()
        elif st == 8:
            over = True; s.move_y()
            if s.p_h <= s.p_y <= 255 and s.row(s.p_y - s.p_h, 2): s.p_y = ((s.p_y - s.p_h) // 16 + 1) * 16 + s.p_h
            else:
                s.p_yv += 6
                if s.p_yv < 0: over = False
            if over: s.p_yv = 0
            if over or not held & 4:
                if s.floor(): s.stand()
                else: s.fall()
        elif st == 1:
            y0 = s.p_y; s.p_yv = min(s.p_yv + 6, 110); s.move_y()
            if 0 <= s.p_y <= 255 and s.p_y // 16 != y0 // 16 and s.row(s.p_y, 1):
                s.p_y = s.p_y // 16 * 16; s.p_ysub = 0; s.p_landed = True; s.p_cnt = 0; s.p_state = 2; s.p_pose = 3
        elif st == 2:
            if not s.floor(): s.fall()
            elif pressed & 4: s.jump()
            else:
                go = True
                if not held & 192:
                    s.p_cnt += 1
                    if s.p_cnt < 5: go = False
                if go:
                    if held & 16: s.p_state = 3; s.p_cnt = 0
                    else: s.stand()
        elif st == 23:
            s.p_cnt -= 1
            if s.p_cnt == 0: s.p_restart = True
        if s.p_state < 20 and s.p_y >= 232:
            s.p_state = 23; s.p_cnt = 60; s.stage.lv_lives -= 1
        if s.p_state != 23:
            if not s.p_auto:
                s.p_xv = 0
                if held & 128: s.p_face = 1; s.p_xv = 2
                elif held & 64: s.p_face = 0; s.p_xv = -2
                if s.p_state == 3: s.p_xv = 0
            cam = s.stage.lv_cam_x
            if s.p_xv > 0:
                s.p_x += s.p_xv
                if not s.p_auto and s.p_x + 6 >= 244: s.p_x = 238
                if s.p_x + 6 < 256 and s.wall(s.p_x + 6): s.p_x = (s.p_x + 6 + cam) // 16 * 16 - 6 - cam
            elif s.p_xv < 0:
                s.p_x += s.p_xv
                if s.p_x - 6 < 12: s.p_x = 18
                if s.wall(s.p_x - 6): s.p_x = (s.p_x + 9 + cam) // 16 * 16 + 6 - cam
            if s.p_auto and s.p_x >= 256: s.p_out = True
        if s.p_pose == 0:
            s.p_blink = (s.p_blink + 255) % 256; s.p_pic = 6 if (s.p_blink & 112) == 0 else 0
        else:
            s.p_blink = 0
            if s.p_pose == 1: s.p_pic = 1 if s.p_walk == 0 else (3 if s.p_walk == 2 else 2)
            elif s.p_pose == 2: s.p_pic = 5
            else: s.p_pic = 4
        s.p_h = 16 if s.p_pose == 4 else 22
    def tiles(s):                               # Draw: list of (x, NES sprite y, sub-image)
        out = []
        b = s.stage.lv_bright
        if b >= 0 and s.s_vis:
            for dx, dy, u in T['tab'][T['frames'][s.s_pic]]:
                tx = s.s_x + dx if s.s_face == 1 else s.s_x - dx - 8; ty = s.s_y + dy
                if ty >= 0 and 0 <= tx <= 255: out.append((tx, ty, (u * 2 + (1 - s.s_face)) * 7 + b))
        return out

class Stage:                                    # obj_stage1
    def __init__(s):
        s.lt = -8; s.pad_prev = 255; s.lv_done = False; s.lv_cam_x = 0; s.lv_cam_show = 0; s.lv_bright = -1; s.lv_exit_t = -1
        s.lv_restart_t = -1; s.lv_lives = 3; s.lv_land_n = 0; s.lv_trig_on = True; s.lv_trig_wait = 0; s.lv_pad_keep = 0; s.lv_pressed_keep = 0
        s.pl = Player(s); s.ran = False; s.sound = False
    def end_step(s, pad):
        s.lt += 1; s.ran = False; s.sound = False
        pressed = pad & (s.pad_prev ^ 255); s.pad_prev = pad
        pl = s.pl
        if not s.lv_done:
            if s.lv_land_n > 0:
                s.lv_land_n += 1
                if s.lv_land_n == 3: s.sound = True
                if s.lv_land_n == 9: s.lv_land_n = 0
            s.lv_cam_show = s.lv_cam_x
            pl.s_x = pl.p_x; pl.s_y = pl.p_y; pl.s_pic = pl.p_pic; pl.s_face = pl.p_face; pl.s_vis = pl.p_state != 23
            if (s.lt == -1 or s.lt >= 18) and s.lv_exit_t < 0 and s.lv_restart_t < 0:
                s.ran = True
                if s.lv_trig_on and pl.p_state != 23:
                    if abs(s.lv_cam_x + pl.p_x - 2016) <= 12 and 144 <= pl.p_y <= 160 + pl.p_h:
                        s.lv_trig_on = False; s.lv_trig_wait = 2
                if s.lt == -1: pl.p_pad = s.lv_pad_keep; pl.p_pressed = s.lv_pressed_keep
                else: pl.p_pad = pad; pl.p_pressed = pressed
                x0 = pl.p_x; pl.user0()
                d = pl.p_x - x0
                if pl.p_x >= 128 and 0 < d < 5:
                    d = min(d, 1792 - s.lv_cam_x); s.lv_cam_x += d; pl.p_x -= d
                if s.lv_trig_wait > 0:
                    s.lv_trig_wait -= 1
                    if s.lv_trig_wait == 0:
                        if pl.p_state == 5: pl.p_state = 20; pl.p_auto = True; pl.p_face = 1; pl.p_xv = 2
                        else: s.lv_trig_on = True
                if pl.p_landed: s.lv_land_n = 1
                if pl.p_out: s.lv_exit_t = s.lt
                if pl.p_restart: s.lv_restart_t = s.lt
            if s.lv_exit_t >= 0 and s.lt == s.lv_exit_t + 22: s.lv_done = True
            if s.lv_restart_t >= 0 and s.lt == s.lv_restart_t + 21: s.lv_pad_keep = pad; s.lv_pressed_keep = pressed
            if s.lv_restart_t >= 0 and s.lt == s.lv_restart_t + 24:
                s.lv_restart_t = -1; s.lt = -7; s.lv_cam_x = 0; s.lv_trig_on = True; s.lv_trig_wait = 0; pl.create()
        s.lv_bright = -1
        if not s.lv_done:
            if s.lt >= 5: s.lv_bright = min((s.lt - 5) // 4, 3)
            o = max(s.lv_exit_t, s.lv_restart_t)
            if o >= 0 and s.lt >= o + 5:
                s.lv_bright = 4 + (s.lt - o - 5) // 4
                if s.lv_bright > 6: s.lv_bright = -1
    def draw(s):
        scr = np.zeros((240, 256, 3), np.uint8)
        if s.lv_bright < 0: return scr, []
        n = s.lv_cam_show // 256; x = n * 256 - s.lv_cam_show
        scr[:, :256 + x] = BG[n * 7 + s.lv_bright][:, -x:]
        if x < 0: scr[:, 256 + x:] = BG[(n + 1) * 7 + s.lv_bright][:, :-x]
        scr[:, :8] = 0
        tl = s.pl.tiles() if not s.lv_done else []
        for tx, ty, k in tl:
            im = CHIP[k]; h = min(8, 240 - (ty + 1)); w = min(8, 256 - tx)
            if h > 0:
                a = im[:h, :w, 3] > 0; scr[ty + 1:ty + 1 + h, tx:tx + w][a] = im[:h, :w, :3][a]
        scr[:, :8] = 0
        return scr, tl

NES_OK = (1, 2, 3, 5, 8, 20, 23)

def from_ram(g, r, f):
    """start the port from the NES memory after frame f"""
    p = g.pl; g.lt = f - 1364; g.pad_prev = 0
    g.lv_cam_x = int(r[0x10]) + 256 * int(r[0x13]); g.lv_lives = int(r[0xA7])
    p.p_state = int(r[0xB8]); p.p_x = int(r[0x314]); p.p_y = int(r[0x2FC]); p.p_ysub = int(r[0x374]) >> 4
    v = int(r[0x35C]); p.p_yv = v - 256 if v > 127 else v; p.p_face = (int(r[0x344]) >> 6) & 1; p.p_h = int(r[0x3BC])
    p.p_cnt = int(r[0xD0]); p.p_blink = int(r[0x3F8]); p.p_pic = T['frames'].index(int(r[0x338]))
    c = int(r[0xC6]); p.p_pose = {0: 0, 0x14: 2, 0x1E: 3, 0x32: 4}.get(c, 1); p.p_walk = (c - 4) // 2 if p.p_pose == 1 else 0

def compare(name, sched, start_from=None):
    character(1 if name.startswith('dl_') else 0)
    d = load(name); f0 = d['f0']; st = d['st']; g = Stage()
    pad = lambda f: sum(PADBIT[k] for k in sched.get(f, []))
    first = f0
    if start_from is None:
        for f in range(1357, f0): g.end_step(pad(f))
        first = max(f0, 1357)
    else:
        from_ram(g, st[start_from - f0]['ram'], start_from); first = start_from + 1
    n = bad_ram = bad_tiles = bad_pic = lands = nes_lands = heard = masked = restarts = 0; last_mark = -99; note = ''; examples = []
    gone = set()
    for f in range(first, f0 + len(st)):
        g.end_step(pad(f)); S = st[f - f0]; r = S['ram']; p = g.pl
        if g.lt == -7: restarts += 1
        if g.lv_exit_t >= 0 and g.lt > g.lv_exit_t + 30: break               # the kitchen appears
        if g.ran and (int(r[0xB8]) not in NES_OK or int(r[0xC8]) & 0x80):
            note = 'enemy contact on NES frame %d' % f; break
        n += 1
        # (a) memory
        if g.ran:
            x = int(r[0x314]) + 256 * int(r[0x320]); y = int(r[0x2FC]) + 256 * int(r[0x308]); y = y - 65536 if y > 32767 else y
            v = int(r[0x35C]); v = v - 256 if v > 127 else v
            nes = [int(r[0xB8]), x, int(r[0x338]), (int(r[0x344]) >> 6) & 1, int(r[0x3BC]), int(r[0x10]) + 256 * int(r[0x13]), int(r[0xA7])]
            sim = [p.p_state, p.p_x, T['frames'][p.p_pic], p.p_face, p.p_h, g.lv_cam_x, g.lv_lives]
            if p.p_state != 23: nes += [y, v, int(r[0x374]) >> 4]; sim += [p.p_y, p.p_yv, p.p_ysub]
            if nes != sim:
                bad_ram += 1
                if len(examples) < 3: examples.append((f, 'nes', nes, 'port', sim))
        # sounds
        w = [tuple(x) for x in d['apu'][f - f0]]
        if (0x4006, 0x70) in w and (0x4004, 0xBF) in w: nes_lands += 1
        if w and w[0] == (0x400C, 0xF0): last_mark = f                      # the NES starts some sound
        if g.sound:
            lands += 1
            if (0x4006, 0x70) in w and (0x4004, 0xBF) in w: heard += 1
            elif not any((0x4004, 0x3F) in [tuple(x) for x in q] for q in d['apu'][max(f - 4 - f0, 0):f + 4 - f0]): bad_ram += 1; examples.append((f, 'landing sound expected'))
            else: masked += 1                                               # a repeating sound of the level ($4004=$3F, not part of this step) has the channel
        # (b) sprite tiles, (c) picture
        scr, tl = g.draw()
        o = S['oam'].reshape(64, 4).astype(int); vis = [(int(q[3]), int(q[0])) for q in o if q[0] < 0xEF]
        mine = set((tx, ty) for tx, ty, k in tl)
        if S['mask'] & 0x10 and not mine <= set(vis):
            bad_tiles += 1
            if len(examples) < 3: examples.append((f, 'tiles missing on the NES', sorted(mine - set(vis))))
        ok = np.ones((240, 256), bool)
        for x, y in vis:
            if (x, y) not in mine: ok[y + 1:y + 9, x:x + 8] = False
        cam = int(r[0xAC]) + 256 * int(r[0xAE]); m = r[0x43A:0x43A + 240].reshape(15, 16).astype(int)
        lo = (cam >> 4) + (1 if cam % 16 >= 8 else 0)
        for c in range(lo, min(lo + 16, 128)):
            for rw in np.nonzero(m[:, c % 16] != BL['raw'][:, c])[0]: gone.add((c, int(rw)))
        for c, rw in gone:
            x = c * 16 - g.lv_cam_show
            if -16 < x < 256: ok[rw * 16:rw * 16 + 16, max(x, 0):x + 16] = False
        diff = (scr != d['frames'][f - f0]).any(axis=2) & ok
        if diff.any():
            bad_pic += 1
            if len(examples) < 3: examples.append((f, 'picture', int(diff.sum()), 'pixels'))
    if nes_lands != heard: bad_ram += 1; examples.append(('landing sounds: NES %d, port %d of %d' % (nes_lands, heard, lands),))
    print('%-10s frames %4d  memory %d  tiles %d  picture %d   landings %d (%d drowned by another sound)  restarts %d  exit %s  %s' % (
        name, n, bad_ram, bad_tiles, bad_pic, lands, masked, restarts, 'yes' if g.lv_exit_t >= 0 or g.lv_done else 'no', note))
    for e in examples: print('     ', e)
    return n, bad_ram + bad_tiles + bad_pic

if __name__ == '__main__':
    only = sys.argv[1:]; tot = [0, 0]
    for j in CP.JOBS:
        if only and j[0] not in only: continue
        r = compare(j[0], j[1], 3632 if 'exit' in j[0] else None)
        tot[0] += r[0]; tot[1] += r[1]
    print('frames compared %d, frames with a difference %d' % tuple(tot))
