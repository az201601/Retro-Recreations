#!/usr/bin/env python3
"""Python port of deliverable 8 (crates and bonus boxes): obj_stage1 (End Step, Draw), obj_player (Create, User Defined 0, 1),
obj_crate and the scr_pl_* scripts of recreation/08_level1_crates/gml/, compared with the capture_crates.py
recordings (and, with --old, with the capture_player.py recordings of steps 6 and 7; their exit runs are started from
the NES memory on frame 3632, as in sim_player.py).  Keep in sync with that folder.

Per frame it compares (a) with the NES memory: the player's state, position, speed, picture, direction, body height,
the camera, lives, whether a crate is carried, the position of every crate object, the blocks that were crates or bonus
boxes, the bonus count; (b) the player's and the crates' sprite tiles with the NES sprite list; (c) the whole picture.
Left out of the picture comparison: the 8x8 boxes of all other NES sprites (hearts, enemies).  A run is compared until
the player touches an enemy.    usage: sim_crates.py [--old] [job ...]"""
import os, pickle, sys
import numpy as np
from PIL import Image
from scenario import load
from emu import WORK, START, A, B, SELECT, UP, DOWN, LEFT, RIGHT
import capture_player as CP, capture_crates as CC
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'recreation', '08_level1_crates', 'assets')
BG = [np.array(Image.open('%s/recreation/05_level1_map/assets/sprites/spr_lv1a_bg_%d.png' % (ROOT, i)).convert('RGB')) for i in range(56)]
BL = pickle.load(open(os.path.join(WORK, 'lv1_blocks.pkl'), 'rb'))
try: TABS = pickle.load(open(os.path.join(WORK, 'cr_tables.pkl'), 'rb'))
except OSError: TABS = None
PADBIT = {START: 1, SELECT: 2, A: 4, UP: 8, DOWN: 16, B: 32, LEFT: 64, RIGHT: 128}
DUCK_H = [16, 12, 8, 4, 0, 1, 2, 4, 2, 0]      # body height while crouching under a carried crate, per frame

def character(c):
    global T, CHIP, CRATE
    if TABS is None: T = None; return
    T = TABS['dale'] if c else TABS['chip']
    st = Image.open('%s/sprites/spr_%s_strip%d.png' % (OUT, 'dale' if c else 'chip', T['n'])).convert('RGBA')
    CHIP = [np.array(st.crop((k * 8, 0, k * 8 + 8, 8))) for k in range(T['n'])]
    st = Image.open('%s/sprites/spr_crate_strip14.png' % OUT).convert('RGBA')
    CRATE = [np.array(st.crop((k * 16, 0, k * 16 + 16, 16))) for k in range(14)]

class Crate:                                    # obj_crate
    def __init__(s, stage, wx, y):
        s.stage = stage; s.c_wx = wx; s.c_y = y; s.c_mode = 0; s.c_dir = 1; s.c_t = 0; s.c_gone = False
        s.s_x = wx - stage.lv_cam_x; s.s_y = y; s.s_flash = 0; s.s_vis = False
    def user0(s):                               # one frame of a thrown crate
        if s.c_mode == 1: s.c_wx += 4 * s.c_dir
        elif s.c_mode == 2: s.c_y -= 6
        elif s.c_mode == 4: s.c_wx += 4 * s.c_dir; s.c_y -= 4
        elif s.c_mode == 3:
            s.c_wx += 4 * s.c_dir
            s.c_y += -1 if (s.c_t // 8) % 2 == 0 else 1
        s.c_t += 1
        x = s.c_wx - s.stage.lv_cam_show         # (the camera position before this frame)
        if x < 0 or x > 255 or s.c_y < -72: s.c_gone = True

class Player:                                   # obj_player
    def __init__(s, stage): s.stage = stage; s.create()
    def create(s):
        s.p_x = 24; s.p_y = 192; s.p_ysub = 0; s.p_xv = 0; s.p_yv = 0; s.p_face = 1; s.p_h = 22; s.p_state = 5; s.p_cnt = 0
        s.p_pose = 2; s.p_walk = 0; s.p_blink = 0; s.p_pic = 5; s.p_auto = False; s.p_pad = 0; s.p_pressed = 0
        s.p_landed = False; s.p_out = False; s.p_restart = False
        s.p_carry = None; s.p_throw = 0; s.p_run = 0; s.p_moved = 0; s.p_hide = False; s.p_snd = 0
        s.s_x = s.p_x; s.s_y = s.p_y; s.s_pic = 0; s.s_face = 1; s.s_vis = True
    # scripts
    def row(s, y, kind):
        r = y // 16
        if r < 0 or r > 14: return False
        wx = s.p_x + s.stage.lv_cam_x
        for c in range((wx - 6) // 16, (wx + 5) // 16 + 1):
            if 0 <= c < 128 and s.stage.lv_kind[r][c] >= kind: return True
        return False
    def floor(s):
        if s.p_y < 0 or s.p_y > 255: return False
        if s.p_y % 16: return False
        if not s.row(s.p_y, 1): return False
        s.p_ysub = 0; s.p_yv = 0; return True
    def wall(s, x):
        """sets w_c, w_r: the topmost solid block the edge is in"""
        if s.p_y < 1 or s.p_y > 255: return False
        c = (x + s.stage.lv_cam_x) // 16
        if c < 0 or c > 127: return False
        for r in range(max(s.p_y - s.p_h, 0) // 16, min((s.p_y + 15) // 16 - 1, 14) + 1):
            if s.stage.lv_kind[r][c] >= 2: s.w_c = c; s.w_r = r; return True
        return False
    def move_y(s):
        t = s.p_y * 16 + s.p_ysub + s.p_yv; s.p_y = t // 16; s.p_ysub = t - s.p_y * 16
    def fall(s): s.p_pose = 2; s.p_yv = 0; s.p_state = 1
    def stand(s): s.p_state = 5; s.p_pose = 0; s.p_cnt = 0
    def jump(s): s.p_yv = -110; s.p_state = 8; s.p_pose = 2
    def pick(s, pressed):
        """the player walked into the solid block (w_c, w_r) with B newly pressed"""
        g = s.stage
        if not (pressed & 32) or s.p_carry is not None or s.p_throw != 0 or s.p_h == 16: return
        k = g.lv_box[s.w_r][s.w_c]
        if k != 1 and k != 2: return
        g.open_box(s.w_c, s.w_r, 3 if k == 2 else 0)        # a crate with a bonus leaves the bonus box behind
        s.p_carry = Crate(g, s.p_x + g.lv_cam_x, s.p_y - 23); g.crates.append(s.p_carry)
        s.p_snd = 1
    def throw(s, held):
        c = s.p_carry; s.p_carry = None; s.p_throw = 1; s.p_snd = 2
        c.c_wx = s.p_x + s.stage.lv_cam_x
        if s.p_h != 0: c.c_y = s.p_y - 16
        c.c_dir = 1 if s.p_face == 1 else -1; c.c_t = 0
        if s.p_run >= 30: c.c_mode = 3; s.p_snd = 4
        elif held & 8: c.c_mode = 4 if held & 192 else 2
        else: c.c_mode = 1
    def user0(s):
        held = s.p_pad; pressed = s.p_pressed
        if s.p_auto: held = 128; pressed = 0
        if (held & 24) == 24: held &= 231; pressed &= 231      # UP and DOWN together count as neither
        s.p_landed = False; s.p_snd = 0
        if s.p_state != 23: s.stage.touch(s)
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
                else: s.p_cnt = min(s.p_cnt + 1, 11)
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
            if s.p_carry is not None: s.p_run = 0; s.throw(8); s.p_snd = 0       # a carried crate is thrown straight up, without a sound
        # carrying: the run-up count, the throw
        if s.p_state == 5 and s.p_carry is not None and s.p_moved != 0 and held & 192: s.p_run = min(s.p_run + 1, 255)
        else: s.p_run = 0
        if s.p_carry is not None and pressed & 32 and s.p_state != 23: s.throw(held)
        if s.p_state != 23:
            x0 = s.p_x
            if s.p_throw >= 2: s.p_xv = 0
            else:
                if not s.p_auto:
                    s.p_xv = 0
                    if held & 128: s.p_face = 1; s.p_xv = 2
                    elif held & 64: s.p_face = 0; s.p_xv = -2
                    if s.p_state == 3: s.p_xv = 0
                cam = s.stage.lv_cam_x
                if s.p_xv > 0:
                    s.p_x += s.p_xv
                    if not s.p_auto and s.p_x + 6 >= 244: s.p_x = 238
                    if s.p_x + 6 < 256 and s.wall(s.p_x + 6): s.p_x = (s.p_x + 6 + cam) // 16 * 16 - 6 - cam; s.pick(pressed)
                elif s.p_xv < 0:
                    s.p_x += s.p_xv
                    if s.p_x - 6 < 12: s.p_x = 18
                    if s.wall(s.p_x - 6): s.p_x = (s.p_x + 9 + cam) // 16 * 16 + 6 - cam; s.pick(pressed)
                if s.p_auto and s.p_x >= 256: s.p_out = True
            s.p_moved = s.p_x - x0
        # picture and body height
        s.p_hide = False; s.p_h = 22
        if s.p_throw > 0:
            s.p_blink = 0
            s.p_pic = 12 if s.p_throw < 4 else 13
            s.p_throw = (s.p_throw + 1) % 16
        elif s.p_pose == 0:
            s.p_blink = (s.p_blink + 255) % 256; s.p_pic = 6 if (s.p_blink & 112) == 0 else 0
            if s.p_carry is not None: s.p_pic = 7
        else:
            s.p_blink = 0
            if s.p_pose == 1:
                s.p_pic = 1 if s.p_walk == 0 else (3 if s.p_walk == 2 else 2)
                if s.p_carry is not None: s.p_pic += 7
            elif s.p_pose == 2: s.p_pic = 11 if s.p_carry is not None else 5
            else:
                s.p_pic = 4
                if s.p_pose == 4: s.p_h = 16
                if s.p_pose == 4 and s.p_carry is not None and s.p_state == 3:
                    s.p_h = DUCK_H[min(s.p_cnt - 1, 9)]
                    if s.p_cnt > 1: s.p_hide = True
        # the carried crate sits on the head
        if s.p_carry is not None:
            s.p_carry.c_wx = s.p_x + s.stage.lv_cam_x
            s.p_carry.c_y = s.p_y if s.p_h == 0 else s.p_y - s.p_h - 1
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
        s.lv_restart_t = -1; s.lv_lives = 3; s.lv_trig_on = True; s.lv_trig_wait = 0; s.lv_pad_keep = 0; s.lv_pressed_keep = 0
        s.lv_bonus = 0; s.lv_fc = 4
        s.reset_map()
        s.lv_sq_k = 0; s.lv_sq_wait = 0; s.lv_sq_now = 0; s.lv_sq_end = -99; s.lv_far_wait = 0
        s.pl = Player(s); s.ran = False; s.started = []
    def reset_map(s):
        s.lv_kind = [[int(v) for v in row] for row in BL['cls']]
        s.lv_box = [[{0xF4: 1, 0xF5: 2, 0xF9: 3}.get(int(v), 0) for v in row] for row in BL['raw']]
        s.lv_open = []; s.crates = []                       # lv_open: (column, row, frame, 1 = a bonus box appeared / 0 = gone)
    def open_box(s, c, r, new):
        s.lv_box[r][c] = new; s.lv_kind[r][c] = 0
        s.lv_open.append((c, r, s.lt, 1 if new == 3 else 0))
    def touch(s, p):
        """the player's body (where it was after the previous frame) touches a bonus box: one box per frame"""
        if p.p_y < 0 or p.p_y > 255: return
        wx = p.p_x + s.lv_cam_x
        for r in range((p.p_y - p.p_h) // 16, p.p_y // 16 + 1):
            for c in range((wx + 5) // 16, (wx - 6) // 16 - 1, -1):
                if 0 <= r <= 14 and 0 <= c < 128 and s.lv_box[r][c] == 3:
                    s.open_box(c, r, 0); s.lv_bonus = min(s.lv_bonus + 1, 99); p.p_snd = 3; return
    def end_step(s, pad):
        s.lt += 1; s.ran = False; s.started = []; s.lv_fc = (s.lv_fc + 1) % 8
        pressed = pad & (s.pad_prev ^ 255); s.pad_prev = pad
        pl = s.pl
        if not s.lv_done:
            # sounds start 2 frames after their cause.  Kinds: 1 pick up, 2 throw, 3 bonus, 5 landing: they use the
            # music's 2nd square channel (the music's part is silent meanwhile); 4 far throw (noise channel)
            if s.lv_sq_wait > 0:
                s.lv_sq_wait -= 1
                if s.lv_sq_wait == 0:
                    if s.lv_sq_k == 5 and (s.lv_sq_now == 1 or s.lv_sq_now == 2) and s.lt < s.lv_sq_end: pass   # no landing sound during those
                    else:
                        s.started.append(s.lv_sq_k); s.lv_sq_now = s.lv_sq_k
                        s.lv_sq_end = s.lt + {1: 14, 2: 25, 3: 4, 5: 6}[s.lv_sq_k]
            if s.lv_sq_now != 0 and s.lt == s.lv_sq_end: s.lv_sq_now = 0
            if s.lv_far_wait > 0:
                s.lv_far_wait -= 1
                if s.lv_far_wait == 0: s.started.append(4)
            s.lv_cam_show = s.lv_cam_x
            pl.s_x = pl.p_x; pl.s_y = pl.p_y; pl.s_pic = pl.p_pic; pl.s_face = pl.p_face; pl.s_vis = pl.p_state != 23 and not pl.p_hide
            for c in s.crates:                              # a crate that will fly / flies far flashes: 4 frames normal, 4 frames bright
                c.s_x = c.c_wx - s.lv_cam_x; c.s_y = c.c_y; c.s_vis = True
                far = c.c_mode == 3 or (c.c_mode == 0 and pl.p_run >= 30)
                c.s_flash = 1 if far and (s.lv_fc & 4) else 0
            s.crates = [c for c in s.crates if not c.c_gone]
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
                for c in s.crates:
                    if c.c_mode != 0: c.user0()
                if s.lv_trig_wait > 0:
                    s.lv_trig_wait -= 1
                    if s.lv_trig_wait == 0:
                        if pl.p_state == 5: pl.p_state = 20; pl.p_auto = True; pl.p_face = 1; pl.p_xv = 2
                        else: s.lv_trig_on = True
                if pl.p_landed: s.lv_sq_k = 5; s.lv_sq_wait = 2
                if pl.p_snd == 4: s.lv_far_wait = 2
                elif pl.p_snd != 0: s.lv_sq_k = pl.p_snd; s.lv_sq_wait = 2
                if pl.p_out: s.lv_exit_t = s.lt
                if pl.p_restart: s.lv_restart_t = s.lt
            if s.lv_exit_t >= 0 and s.lt == s.lv_exit_t + 22: s.lv_done = True
            if s.lv_restart_t >= 0 and s.lt == s.lv_restart_t + 21: s.lv_pad_keep = pad; s.lv_pressed_keep = pressed
            if s.lv_restart_t >= 0 and s.lt == s.lv_restart_t + 24:
                s.lv_restart_t = -1; s.lt = -7; s.lv_cam_x = 0; s.lv_trig_on = True; s.lv_trig_wait = 0; pl.create(); s.reset_map()
                s.lv_sq_now = 0; s.lv_sq_wait = 0; s.lv_far_wait = 0
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
        for c, r, t, k in s.lv_open:                        # the wallpaper (or whatever is behind) where a box was
            if s.lt - t < TABS['patch_delay']: continue
            dc, dr = TABS['box'] if k else TABS['patch'][(c, r)]; x = c * 16 - s.lv_cam_show
            src = BG[(dc // 16) * 7 + s.lv_bright][dr * 16:dr * 16 + 16, (dc % 16) * 16:(dc % 16) * 16 + 16]
            x0 = max(x, 0); x1 = min(x + 16, 256)
            if x1 > x0: scr[r * 16:r * 16 + 16, x0:x1] = src[:, x0 - x:x1 - x]
        scr[:, :8] = 0
        tl = []
        if not s.lv_done:
            # the NES lists its sprites forwards on one frame and backwards on the next: the player is in front of
            # the crates on one frame and behind them on the next (it only shows in the one pixel row they share)
            ct = []
            for c in s.crates:                              # each crate is four 8x8 NES sprites
                if not c.s_vis: continue
                for q, (dx, dy) in enumerate(((-8, -17), (-8, -9), (0, -17), (0, -9))):
                    tx = c.s_x + dx; ty = c.s_y + dy
                    if ty >= 0 and 0 <= tx <= 255: ct.append((tx, ty, ('c', c.s_flash * 7 + s.lv_bright, q)))
            tl = s.pl.tiles() + ct if (s.lv_fc & 1) else ct + s.pl.tiles()[::-1]
        for tx, ty, k in tl:
            if isinstance(k, tuple): im = CRATE[k[1]][(k[2] % 2) * 8:(k[2] % 2) * 8 + 8, (k[2] // 2) * 8:(k[2] // 2) * 8 + 8]
            else: im = CHIP[k]
            h = min(8, 240 - (ty + 1)); w = min(8, 256 - tx)
            if h > 0:
                a = im[:h, :w, 3] > 0; scr[ty + 1:ty + 1 + h, tx:tx + w][a] = im[:h, :w, :3][a]
        scr[:, :8] = 0
        return scr, tl

NES_OK = (1, 2, 3, 5, 8, 20, 23)

def from_ram(g, r, f):
    """start the port from the NES memory after frame f (for the exit runs, whose way to the last screen is not compared)"""
    p = g.pl; g.lt = f - 1364; g.pad_prev = 0; g.lv_fc = f % 8
    g.lv_cam_x = int(r[0x10]) + 256 * int(r[0x13]); g.lv_lives = int(r[0xA7]); g.lv_bonus = int(r[0xA3])
    p.p_state = int(r[0xB8]); p.p_x = int(r[0x314]); p.p_y = int(r[0x2FC]); p.p_ysub = int(r[0x374]) >> 4
    v = int(r[0x35C]); p.p_yv = v - 256 if v > 127 else v; p.p_face = (int(r[0x344]) >> 6) & 1; p.p_h = int(r[0x3BC])
    p.p_cnt = int(r[0xD0]); p.p_blink = int(r[0x3F8]); p.p_pic = [0, 1, 2, 3, 4, 5, 23].index(int(r[0x338]))
    c = int(r[0xC6]); p.p_pose = {0: 0, 0x14: 2, 0x1E: 3, 0x32: 4}.get(c, 1); p.p_walk = (c - 4) // 2 if p.p_pose == 1 else 0
    m = r[0x43A:0x43A + 240].reshape(15, 16).astype(int); lo = (g.lv_cam_x >> 4) + 1
    for c in range(lo, min(lo + 14, 128)):                  # boxes that are already gone on the screen
        for rw in range(15):
            k = {0xF4: 1, 0xF5: 2, 0xF9: 3}.get(int(m[rw, c % 16]), 0)
            if k != g.lv_box[rw][c]: g.open_box(c, rw, k); g.lv_open[-1] = (c, rw, -99, 0)
PICS = None

def compare(name, sched, start_from=None, pictures=True, verbose=1):
    character(1 if name.startswith('dl_') else 0)
    d = load(name); f0 = d['f0']; st = d['st']; g = Stage()
    pad = lambda f: sum(PADBIT[k] for k in sched.get(f, []))
    if start_from is None:
        for f in range(1357, f0): g.end_step(pad(f))
        first = max(f0, 1357)
    else: from_ram(g, st[start_from - f0]['ram'], start_from); first = start_from + 1
    n = bad_ram = bad_tiles = bad_pic = hits = 0; note = ''; examples = []; ev = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}; drowned = {3: 0, 5: 0}
    cels = [0, 1, 2, 3, 4, 5, 23, 22, 6, 7, 8, 11, 9, 10]
    for f in range(first, f0 + len(st)):
        g.end_step(pad(f)); S = st[f - f0]; r = S['ram']; p = g.pl
        if g.lv_exit_t >= 0 and g.lt > g.lv_exit_t + 30: break
        if g.ran and (int(r[0xB8]) not in NES_OK or int(r[0xC8]) & 0x80):
            note = 'enemy contact on NES frame %d' % f; break
        n += 1
        # sounds: each one the port starts must start on the NES on the same frame, and no others
        w = [tuple(q) for q in d['apu'][f - f0]]; pw = [tuple(q) for q in d['apu'][f - 1 - f0]] if f > f0 else []
        near = [tuple(x) for q in d['apu'][max(f - 4 - f0, 0):f + 4 - f0] for x in q]
        nes_now = set()
        if (0x4005, 0x94) in w and (0x4006, 0x8E) in w: nes_now.add(1)
        if (0x4005, 0x93) in w and (0x4006, 0x52) in w and (0x4005, 0x93) not in pw: nes_now.add(2)
        if (0x4006, 0x6A) in w and (0x4004, 0xBF) in w: nes_now.add(3)
        if (0x400C, 0xBF) in w and (0x400C, 0xBF) not in pw: nes_now.add(4)
        if (0x4006, 0x70) in w and (0x4004, 0xBF) in w: nes_now.add(5)
        for k in g.started:
            ev[k] += 1
            if k in nes_now: nes_now.discard(k)
            elif k in (3, 5) and (0x4004, 0x3F) in near: drowned[k] += 1          # a repeating sound of the level (it starts with the first enemy, a later step) keeps the channel
            else:
                bad_ram += 1
                if len(examples) < verbose: examples.append((f, 'sound %d expected' % k, w[:6]))
        if nes_now:
            bad_ram += 1
            if len(examples) < verbose: examples.append((f, 'sounds on the NES only', nes_now))
        if g.ran:
            cam = int(r[0x10]) + 256 * int(r[0x13])
            x = int(r[0x314]) + 256 * int(r[0x320]); y = int(r[0x2FC]) + 256 * int(r[0x308]); y = y - 65536 if y > 32767 else y
            v = int(r[0x35C]); v = v - 256 if v > 127 else v
            cel = int(r[0x338])
            nes = [int(r[0xB8]), x, cel if cel < 128 else -1, (int(r[0x344]) >> 6) & 1, int(r[0x3BC]), cam, int(r[0xA7]), (int(r[0x2E4]) >> 6) & 1, int(r[0xA3])]
            sim = [p.p_state, p.p_x, -1 if p.p_hide else cels[p.p_pic], p.p_face, p.p_h, g.lv_cam_x, g.lv_lives, int(p.p_carry is not None), g.lv_bonus]
            if p.p_state != 23: nes += [y, v, int(r[0x374]) >> 4]; sim += [p.p_y, p.p_yv, p.p_ysub]
            nc = []
            for j in range(1, 8):
                if r[0x32C + j] == 3 and (int(r[0x2F0 + j]) & 0x8F) == 1:     # this crate has hit an enemy (a later step): take the port's crate away
                    cx = int(r[0x314 + j]) + 256 * int(r[0x320 + j]) + cam
                    for c in g.crates:
                        if not c.c_gone and abs(c.c_wx - cx) <= 4 and abs(c.c_y - int(r[0x2FC + j])) <= 6: c.c_gone = True; hits += 1
                if r[0x32C + j] == 3 and (int(r[0x2F0 + j]) & 0x8F) in (3, 9):
                    cy = int(r[0x2FC + j]) + 256 * int(r[0x308 + j]); cy = cy - 65536 if cy > 32767 else cy
                    cx = int(r[0x314 + j]) + 256 * int(r[0x320 + j]); cx = cx - 65536 if cx > 32767 else cx
                    nc.append((cx + cam, cy))
            sc = [(c.c_wx, c.c_y) for c in g.crates if not c.c_gone]
            nes.append(sorted(nc)); sim.append(sorted(sc))
            # blocks: the columns the NES has in its buffer
            m = r[0x43A:0x43A + 240].reshape(15, 16).astype(int); lo = (cam >> 4) + 1; bb = []
            for c in range(lo, min(lo + 14, 128)):
                for rw in range(15):
                    k = {0xF4: 1, 0xF5: 2, 0xF9: 3}.get(int(m[rw, c % 16]), 0)
                    if k != g.lv_box[rw][c]: bb.append((c, rw, k, g.lv_box[rw][c]))
            nes.append([]); sim.append(bb)
            if nes != sim:
                bad_ram += 1
                if len(examples) < verbose: examples.append((f, 'nes', nes, 'port', sim))
        if pictures and T is not None:
            scr, tl = g.draw()
            o = S['oam'].reshape(64, 4).astype(int); vis = [(int(q[3]), int(q[0])) for q in o if q[0] < 0xEF]
            mine = set((tx, ty) for tx, ty, k in tl)
            if S['mask'] & 0x10 and not mine <= set(vis):
                bad_tiles += 1
                if len(examples) < verbose: examples.append((f, 'tiles missing on the NES', sorted(mine - set(vis))))
            ok = np.ones((240, 256), bool)
            for x, y in vis:
                if (x, y) not in mine: ok[y + 1:y + 9, x:x + 8] = False
            diff = (scr != d['frames'][f - f0]).any(axis=2) & ok
            if diff.any():
                bad_pic += 1
                if len(examples) < verbose: ys, xs = np.nonzero(diff); examples.append((f, 'picture', int(diff.sum()), 'pixels, box', int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())))
                global PICS; PICS = PICS or (name, f, scr, d['frames'][f - f0])
    print('%-14s frames %4d  memory+sound %d  tiles %d  picture %d   sounds: pick %d, throw %d, far throw %d, bonus %d (+%d drowned), landing %d (+%d drowned)  %s%s' % (
        name, n, bad_ram, bad_tiles, bad_pic, ev[1], ev[2], ev[4], ev[3] - drowned[3], drowned[3], ev[5] - drowned[5], drowned[5], note, '  crates that hit an enemy: %d' % hits if hits else ''))
    for e in examples: print('     ', e)
    return n, bad_ram + bad_tiles + bad_pic

if __name__ == '__main__':
    args = sys.argv[1:]; old = '--old' in args; nopic = '--nopic' in args; only = [a for a in args if not a.startswith('--')]; tot = [0, 0]
    for j in (CP.JOBS if old else CC.JOBS):
        if only and j[0] not in only: continue
        r = compare(j[0], j[1], 3632 if 'exit' in j[0] else None, pictures=not nopic)
        tot[0] += r[0]; tot[1] += r[1]
    print('frames compared %d, frames with a difference %d' % tuple(tot))
