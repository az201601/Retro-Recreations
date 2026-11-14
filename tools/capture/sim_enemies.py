#!/usr/bin/env python3
"""Python port of deliverable 9 (enemies): obj_stage1 (End Step, Draw), obj_player, obj_crate, obj_enemy and the
scr_* scripts of recreation/09_level1_enemies/gml/, compared with the capture_enemies.py recordings (and, with --old,
with the capture_player.py and capture_crates.py recordings of steps 6 to 8, except their exit runs, which start at
the end of the section among enemies the port has not seen arrive; sim_crates.py checks those).  Keep in sync with
that folder.

Per frame it compares
(a) with the NES memory: the player's state, position, speed, picture, direction, body height, the camera, lives,
    whether a crate is carried, the bonus count, the blocks that were crates or bonus boxes, and every place of the
    object list: a crate's position (and its picture while it breaks), an enemy's position with fractions, speeds,
    picture, direction, hit points, damage and body size;
(b) the sounds: every sound the port starts must start on the NES on that frame and no others; which of music and
    effect has the 2nd square channel; the bonus note; the far throw's and the hit's noise;
(c) the sprites: every sprite the port draws must be in the NES sprite list, every NES sprite except the hearts must
    be drawn by the port, in the same order;
(d) the whole picture, except the 8x8 boxes of the hearts and the picture lines on which the NES has more than 8
    sprites (it leaves the rest out there, the port does not).
A frame the NES leaves out when it is too busy (its frame counter $2D stands still) is skipped: the port waits.
A run is compared until the player is hurt.    usage: sim_enemies.py [--old] [--nopic] [job ...]"""
import os, pickle, sys
import numpy as np
from PIL import Image
from scenario import load
from emu import WORK, START, A, B, SELECT, UP, DOWN, LEFT, RIGHT
import build_player as BPL
CP_HUD = BPL.HUD
import capture_player as CP, capture_crates as CC, capture_enemies as CE
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'recreation', '09_level1_enemies', 'assets')
BG = [np.array(Image.open('%s/recreation/05_level1_map/assets/sprites/spr_lv1a_bg_%d.png' % (ROOT, i)).convert('RGB')) for i in range(56)]
BL = pickle.load(open(os.path.join(WORK, 'lv1_blocks.pkl'), 'rb'))
TABS = pickle.load(open(os.path.join(WORK, 'cr_tables.pkl'), 'rb')); ETAB = pickle.load(open(os.path.join(WORK, 'en_tables.pkl'), 'rb'))
OLD = os.path.join(ROOT, 'recreation', '08_level1_crates', 'assets')        # the player's and the crate's pictures are those of step 8
PADBIT = {START: 1, SELECT: 2, A: 4, UP: 8, DOWN: 16, B: 32, LEFT: 64, RIGHT: 128}
FX_LEN = {1: 14, 2: 25, 3: 53, 4: 73, 5: 6, 6: 4, 7: 10, 8: 17}     # frames a sound effect lasts
DUCK_H = [16, 12, 8, 4, 0, 1, 2, 4, 2, 0]      # body height while crouching under a carried crate, per frame

def character(c):
    global T, CHIP, CRATE, EYES, ENEMY
    T = TABS['dale'] if c else TABS['chip']
    def strip(p, n, w):
        st = Image.open(p).convert('RGBA'); return [np.array(st.crop((k * w, 0, k * w + w, w))) for k in range(n)]
    CHIP = strip('%s/sprites/spr_%s_strip%d.png' % (OLD, 'dale' if c else 'chip', T['n']), T['n'], 8)
    CRATE = strip('%s/sprites/spr_crate_strip14.png' % OLD, 14, 16); EYES = strip('%s/sprites/spr_crate_eyes_strip7.png' % OLD, 7, 8)
    ENEMY = strip('%s/sprites/spr_enemy_strip%d.png' % (OUT, ETAB['n']), ETAB['n'], 8)

class Crate:                                    # obj_crate
    def __init__(s, stage, wx, y):
        s.stage = stage; s.c_wx = wx; s.c_y = y; s.c_mode = 0; s.c_dir = 1; s.c_t = 0; s.c_gone = False; s.c_eyes = 0
        s.c_hot = False; s.c_pic = 0; s.c_snd = 0; s.c_slot = stage.take_slot(s)
        s.s_x = wx - stage.lv_cam_x; s.s_y = y; s.s_flash = 0; s.s_vis = False; s.s_eyes = 0; s.s_pic = 0
    def smash(s):                               # it has hit an enemy: it stops and breaks
        s.c_mode = 5; s.c_t = 0; s.c_hot = False
    def user0(s):                               # one frame of a thrown crate
        if s.c_mode == 5:                       # breaking: 1 frame whole, 5 frames of pieces
            s.c_t += 1
            s.c_pic = s.c_eyes if s.c_t == 1 else s.c_t + 1
            if s.stage.pl.p_carry is s: s.stage.pl.p_carry = None      # the player was hiding under it
            if s.c_t == 7: s.c_gone = True; s.stage.lv_slot[s.c_slot] = None
            return
        if s.c_mode == 1: s.c_wx += 4 * s.c_dir
        elif s.c_mode == 2: s.c_y -= 6
        elif s.c_mode == 4: s.c_wx += 4 * s.c_dir; s.c_y -= 4
        elif s.c_mode == 3:
            s.c_wx += 4 * s.c_dir
            s.c_y += -1 if (s.c_t // 8) % 2 == 0 else 1
        s.c_t += 1
        x = s.c_wx - s.stage.lv_cam_show         # (the camera position before this frame)
        if x < 0 or x > 255 or s.c_y < -72: s.c_gone = True; s.stage.lv_slot[s.c_slot] = None

# the objects of the section, in the order the camera reaches them: (column, row, kind); kind 1 flyer, 3 cook, 9 the exit.
# From the ROM: bank 3 $A3F1, 3 bytes each (column, row, type), up to the first column 255.
def level_objects():
    rom = open(os.path.join(ROOT, "Chip 'n Dale - Rescue Rangers 2 (USA).nes"), 'rb').read()[16:]
    a = 3 * 0x4000 + 0x23F1; out = []
    while rom[a] != 255: out.append((rom[a], rom[a + 1], {0x27: 1, 0x25: 3, 0x21: 9}[rom[a + 2]])); a += 3
    return out
OBJECTS = level_objects()
WALK = (8, 9, 10, 9)                            # the cook's walking pictures
HOVER = (24, 25, 24, 25, 26, 27, 26, 27, 22, 23, 22, 23)    # the flyer's pictures while it hovers and drops something

class Exit:                                     # the invisible exit takes a place in the object list like an enemy
    def __init__(s, stage): s.e_slot = stage.take_slot(s)

class Enemy:                                    # obj_enemy.  e_kind: 1 flyer, 2 what it drops, 3 cook, 4 the fork it throws
    def __init__(s, stage, kind, wx, y, face):
        s.stage = stage; s.e_kind = kind; s.e_wx = wx; s.e_xs = 0; s.e_y = y; s.e_ys = 0; s.e_xv = 0; s.e_yv = 0; s.e_face = face
        s.e_pic = 0; s.e_w = 0; s.e_h = 0; s.e_hp = 0; s.e_dmg = 0; s.e_state = -1; s.e_t = 0; s.e_n = 0
        s.e_ok = False; s.e_seen = False; s.e_t0 = True; s.e_hide = True; s.e_gone = False
        s.s_x = 0; s.s_y = 0; s.s_pic = 0; s.s_face = 0; s.s_vis = False
        s.e_slot = stage.take_slot(s)
    # scripts
    def move_x(s):
        t = s.e_wx * 16 + s.e_xs + s.e_xv; s.e_wx = t // 16; s.e_xs = t - s.e_wx * 16
    def move_y(s):
        t = s.e_y * 16 + s.e_ys + s.e_yv; s.e_y = t // 16; s.e_ys = t - s.e_y * 16
    def face_player(s):
        sx = s.e_wx - s.stage.lv_cam_show
        if sx < 0: s.e_face = 1
        elif sx > 255: s.e_face = 0
        else: s.e_face = 1 if s.stage.pl.p_x >= sx else 0
    def near_player(s):
        """the cook sees the player: on its level and less than 80 pixels away"""
        p = s.stage.pl; dy = s.e_y - p.p_y
        if dy >= s.e_h or dy < -p.p_h: return False
        d = s.e_wx - s.stage.lv_cam_show - p.p_x
        v = d & 255
        if d < 0: v = (-v) & 255
        return v < 80
    def row(s, y, kind):
        r = y // 16
        if r < 0 or r > 14: return False
        x = s.e_wx + s.stage.lv_cam_x - s.stage.lv_cam_show      # (the original looks one camera step too far right)
        for c in range((x - s.e_w) // 16, (x + s.e_w - 1) // 16 + 1):
            if s.stage.block(r, c) >= kind: return True
        return False
    def floor(s):
        if s.e_y < 0 or s.e_y > 255 or not s.row(s.e_y, 1): return False
        s.e_y = s.e_y // 16 * 16; s.e_ys = 0; return True
    def ceiling(s):
        if s.e_y < s.e_h or s.e_y > 255 or not s.row(s.e_y - s.e_h, 2): return False
        s.e_y = (s.e_y - s.e_h) // 16 * 16 + 16 + s.e_h; return True
    def wall(s):
        """a solid block in the way: the enemy is put next to it"""
        if s.e_xv == 0 or s.e_y < 1 or s.e_y > 255: return False
        x = s.e_wx + s.e_w if s.e_xv > 0 else s.e_wx - s.e_w
        sx = x - s.stage.lv_cam_show
        if sx < 0 or sx > 255: return False
        d = s.stage.lv_cam_x - s.stage.lv_cam_show          # (the original looks one camera step too far right)
        c = (x + d) // 16
        for r in range(max(s.e_y - s.e_h, 0) // 16, min((s.e_y + 15) // 16 - 1, 14) + 1):
            if s.stage.block(r, c) >= 2:
                s.e_wx = c * 16 - s.e_w - d if s.e_xv > 0 else (x + d - 1) // 16 * 16 + 16 + s.e_w - d
                return True
        return False
    def hit_by(s, c):
        """a thrown crate (or one the player hides under) touches the enemy"""
        g = s.stage
        cx = c.c_wx - (g.lv_cam_x if (c.c_mode != 0 and c.c_slot < s.e_slot) else g.lv_cam_show)
        dx = s.e_wx - g.lv_cam_show - cx; dy = s.e_y - c.c_y
        return abs(dx) <= s.e_w + 6 and -15 <= dy <= s.e_h
    def user0(s):                               # one frame
        g = s.stage; k = s.e_kind; cam0 = g.lv_cam_show
        # 1) hit by a crate?  (not what the flyer drops)
        sx = s.e_wx - cam0
        if k != 2 and s.e_hp != 0 and 0 <= sx <= 255 and 0 <= s.e_y <= 255:
            for j in range(11, 2, -1):
                c = g.lv_slot[j]
                if isinstance(c, Crate) and (c.c_hot or (c.c_mode == 0 and g.pl.p_state == 3 and g.pl.p_h == 0)) and s.hit_by(c):
                    d = -1 if (c.c_mode in (1, 3, 4) and c.c_dir < 0) else 1
                    if c.c_mode != 3: c.smash()             # (not measured: a crate of a far throw is assumed to fly on)
                    s.e_hp = 0; s.e_t = 0
                    if k == 4: s.e_state = 8; s.e_xv = 12 * d; s.e_yv = -32
                    else: s.e_state = 9; s.e_dmg = 0; s.e_xv = 67 * d; s.e_yv = -67; g.lv_snd = 8
                    break
        # 2) what it does
        st = s.e_state
        if st == 9: s.move_x(); s.move_y()                  # hit: flies away
        elif st == 8:                                       # the fork, hit: falls
            if s.e_t > 0 and s.e_yv < 80: s.e_yv += 3
            s.e_t = 1; s.move_x(); s.move_y()
        elif k == 1:
            if st == -1: s.e_pic = 22; s.e_hp = 1; s.e_dmg = 1; s.e_w = 8; s.e_h = 16; s.e_xv = 16; s.e_yv = 4; s.e_hide = False; s.e_state = 0; s.e_ok = s.e_seen
            elif st == 0:
                if s.e_ok: s.face_player(); s.e_xv = 16 if s.e_face else -16; s.e_state = 1; s.e_t = 0
                else: s.e_ok = s.e_seen
            if s.e_state == 1:
                if s.e_t == 96: s.e_t = 0; s.e_yv = -s.e_yv     # (down on one flight, up on the next)
                t = s.e_t
                if t < 48:                                  # 48 frames flying
                    if t % 3 == 0: s.e_pic = 22 + (t // 3) % 2; g.lv_snd = 6
                    s.move_x(); s.move_y()
                elif (t - 48) % 4 == 0:                     # 48 frames on the spot: after 32 it drops something
                    q = (t - 48) // 4
                    if q == 8: g.spawn(2, s)
                    s.e_pic = HOVER[q]; g.lv_snd = 6
                s.e_t += 1
        elif k == 2:
            if st == -1: s.e_seen = True; s.e_y += 8; s.e_hp = 1; s.e_dmg = 2; s.e_w = 2; s.e_h = 4; s.e_pic = 28; s.e_yv = 8; s.e_hide = False; s.e_state = 1
            elif s.e_yv < 80: s.e_yv += 3
            s.move_y()
        elif k == 4:
            if st == -1:
                s.e_hp = 1; s.e_dmg = 1; s.e_w = 8; s.e_h = 4; s.e_pic = 14; s.e_y -= 16; s.e_seen = True; s.e_hide = False; s.e_state = 1
                s.e_wx += 19 if s.e_face else -19; s.e_xv = 48 if s.e_face else -48
            s.move_x()
        elif k == 3:
            if st == -1: s.e_pic = 7; s.e_hp = 1; s.e_dmg = 1; s.e_w = 8; s.e_h = 24; s.e_hide = False; s.e_state = 0; s.e_ok = s.e_seen
            elif st == 0:
                if s.e_ok: s.face_player(); s.e_xv = 16 if s.e_face else -16; s.e_yv = 0; s.e_state = 1; s.e_t = 0
                else: s.e_ok = s.e_seen
            elif st == 1 and s.near_player():               # sees the player: stops and throws
                s.face_player(); s.e_xv = 16 if s.e_face else -16; s.e_state = 2; s.e_t = 0; s.e_pic = 7
            elif st == 2:
                s.e_t += 1
                if s.e_t == 17: s.e_pic = 12
                elif s.e_t == 34: s.e_pic = 13; g.lv_snd = 7; g.spawn(4, s)
                elif s.e_t == 51: s.e_pic = 7
                elif s.e_t == 68: s.e_pic = 8; s.e_state = 3; s.e_t = 0; s.e_n = 0
            elif st == 3:                                   # after the throw: walks on, jumps at walls and edges
                s.move_x()
                if s.wall() or not s.floor(): s.e_pic = 9; s.e_yv = -64; s.e_state = 4
                else:
                    s.e_t += 1
                    if s.e_t == 8: s.e_t = 0; s.e_n = (s.e_n + 1) % 4; s.e_pic = WALK[s.e_n]
            elif st == 4:                                   # in the air
                s.move_x(); s.wall()
                if s.e_yv < 80: s.e_yv += 3
                if s.e_yv < 0:
                    s.move_y()
                    if s.ceiling(): s.e_yv = 1
                else:
                    y0 = s.e_y; s.move_y()
                    if (s.e_y & 255) // 16 != (y0 & 255) // 16 and s.floor():
                        s.e_yv = 0; s.e_state = 3; s.e_t = 0; s.e_n = (s.e_n + 1) % 4; s.e_pic = WALK[s.e_n]
            if s.e_state == 1 and (st == 1 or st == 0):     # walks 32 pixels to and fro
                t = s.e_t
                if t % 8 == 0:
                    if t % 32 == 0 and t > 0: s.e_face = 1 - s.e_face; s.e_xv = -s.e_xv
                    s.e_pic = WALK[(t // 8) % 4]
                s.move_x(); s.e_t += 1
        # 3) seen on the screen once, it is removed when it leaves it  (the camera position before this frame)
        sx = s.e_wx - cam0
        if s.e_seen:
            if sx < 0 or sx > 255 or s.e_y < -72 or s.e_y >= 237: s.e_gone = True; g.lv_slot[s.e_slot] = None
        elif 0 <= sx <= 255 and 0 <= s.e_y <= 255: s.e_seen = True


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
        c = s.p_carry; s.p_carry = None; s.p_throw = 1; s.t_snd = 2; c.c_eyes = 0; c.c_hot = True
        c.c_wx = s.p_x + s.stage.lv_cam_x
        if s.p_h != 0: c.c_y = s.p_y - 16
        c.c_dir = 1 if s.p_face == 1 else -1; c.c_t = 0
        if s.p_run >= 30: c.c_mode = 3; s.t_snd = 4
        elif held & 8: c.c_mode = 4 if held & 192 else 2
        else: c.c_mode = 1
        c.c_snd = s.t_snd                           # the crate makes the sound when its turn comes
    def user0(s):
        held = s.p_pad; pressed = s.p_pressed
        if s.p_auto: held = 128; pressed = 0
        if (held & 24) == 24: held &= 231; pressed &= 231      # UP and DOWN together count as neither
        s.p_landed = False; s.p_snd = 0
        # the player's eyes look out of the crate (2 = to the right, 1 = to the left) after 11 frames of hiding under
        # it; they are open for 101 frames and shut for 16.  The crate follows what the player did one frame ago.
        if s.p_carry is not None:
            s.p_carry.c_eyes = 1 + s.p_face if s.p_state == 3 and 11 <= s.p_cnt <= 111 else 0
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
                lock = s.p_carry is not None and s.p_cnt < 4       # with a crate: nothing else while it is coming down
                if not lock and not held & 16: s.stand()
                elif not lock and pressed & 4 and not s.row(s.p_y, 2): s.fall()
                else:
                    s.p_cnt += 1
                    if s.p_cnt == 128: s.p_cnt = 11
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
            if s.p_carry is not None: s.p_run = 0; s.throw(8)       # a carried crate is thrown straight up (with the throw sound)
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
        s.lv_fx_k = 0; s.lv_fx_wait = 0; s.lv_fx_now = 0; s.lv_fx_end = -99
        s.pl = Player(s); s.ran = False; s.lv_ord = 0; s.started = []; s.follow = None
    def reset_map(s):
        s.lv_kind = [[int(v) for v in row] for row in BL['cls']]
        s.lv_box = [[{0xF4: 1, 0xF5: 2, 0xF9: 3}.get(int(v), 0) for v in row] for row in BL['raw']]
        s.lv_slot = [None] * 12; s.enemies = []; s.lv_sp_i = 0; s.lv_sp_col = 16; s.lv_snd = 0
        s.lv_open = []; s.crates = []                       # lv_open: (column, row, frame, 1 = a bonus box appeared / 0 = gone)
    def take_slot(s, o):
        """the lowest free place in the object list (0-2 are the players and the hearts); objects act in this order"""
        for j in range(3, 12):
            if s.lv_slot[j] is None: s.lv_slot[j] = o; return j
        raise Exception('object list full')
    def spawn(s, kind, by):
        e = Enemy(s, kind, by.e_wx, by.e_y, by.e_face); s.enemies.append(e)
        # in a place before its maker's it does not act on this frame, and misses this frame's camera step
        if e.e_slot < by.e_slot: e.e_wx += s.lv_cam_x - s.lv_cam_show
    def block(s, r, c):
        """the block an enemy finds in column c: the original only keeps 16 columns, up to the one 248 pixels right of
        the camera, so in the column at the left screen edge an enemy finds the blocks of the column 16 further right"""
        if c < ((s.lv_cam_x + 248) >> 4) - 15: c += 16
        if c < 0 or c > 127: return 0
        return s.lv_kind[r][c]
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
        s.lt += 1; s.started = []; s.lv_fc = (s.lv_fc + 1) % 8
        # which sprites are in front changes with every frame of the game (not while it stands still)
        if s.ran: s.lv_ord = s.lv_fc & 1
        s.ran = False
        pressed = pad & (s.pad_prev ^ 255); s.pad_prev = pad
        pl = s.pl
        if not s.lv_done:
            # sound effects: 1 pick up, 2 throw, 3 bonus, 4 far throw, 5 landing.  Only one plays at a time.  A new one
            # stops the one before it 1 frame after its cause and starts 2 frames after it.  The landing sound is the
            # exception: it stops nothing, and is left out while another effect is playing.
            # (1, 2, 3 and 5 use the music's 2nd square channel: the music's part is silent meanwhile.  4 is noise.)
            if s.lv_fx_wait > 0:
                s.lv_fx_wait -= 1
                if s.lv_fx_wait == 1:
                    if s.lv_fx_k != 5: s.lv_fx_now = 0
                else:
                    if s.lv_fx_k == 5 and s.lv_fx_now != 0 and s.lv_fx_now != 5 and s.lt < s.lv_fx_end: pass
                    else:
                        s.started.append(s.lv_fx_k); s.lv_fx_now = s.lv_fx_k
                        s.lv_fx_end = s.lt + FX_LEN[s.lv_fx_k]
            if s.lv_fx_now != 0 and s.lt == s.lv_fx_end: s.lv_fx_now = 0
            s.lv_cam_show = s.lv_cam_x
            pl.s_x = pl.p_x; pl.s_y = pl.p_y; pl.s_pic = pl.p_pic; pl.s_face = pl.p_face; pl.s_vis = pl.p_state != 23 and not pl.p_hide
            for c in s.crates:                              # a crate that will fly / flies far flashes: 4 frames normal, 4 frames bright
                c.s_x = c.c_wx - s.lv_cam_x; c.s_y = c.c_y; c.s_vis = True; c.s_eyes = c.c_eyes
                c.s_pic = c.c_pic if c.c_mode == 5 and c.c_t >= 2 else 0       # 3..7: flying apart
                far = c.c_mode == 3 or (c.c_mode == 0 and pl.p_run >= 30)
                c.s_flash = 1 if far and (s.lv_fc & 4) else 0
            s.crates = [c for c in s.crates if not c.c_gone]
            for e in s.enemies: e.s_x = e.e_wx - s.lv_cam_x; e.s_y = e.e_y; e.s_pic = e.e_pic; e.s_face = e.e_face; e.s_vis = not e.e_hide and not e.e_gone
            s.enemies = [e for e in s.enemies if not e.e_gone]
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
                if s.follow is not None: s.follow(s)
                # objects enter when the column 264 pixels right of the camera changes
                col = (s.lv_cam_x + 264) >> 4
                if col != s.lv_sp_col:
                    s.lv_sp_col = col
                    while s.lv_sp_i < len(OBJECTS) and OBJECTS[s.lv_sp_i][0] == col:
                        c_, r_, k_ = OBJECTS[s.lv_sp_i]; s.lv_sp_i += 1
                        if k_ == 9: Exit(s)
                        else: s.enemies.append(Enemy(s, k_, c_ * 16, r_ * 16 - 512, 0))
                # crates and enemies act in the order of their places in the object list
                s.lv_snd = 0
                for j in range(3, 12):
                    o = s.lv_slot[j]
                    if isinstance(o, Crate):
                        if o.c_snd: s.lv_snd = o.c_snd; o.c_snd = 0
                        if o.c_mode != 0: o.user0()
                    elif isinstance(o, Enemy): o.user0()
                if s.lv_trig_wait > 0:
                    s.lv_trig_wait -= 1
                    if s.lv_trig_wait == 0:
                        if pl.p_state == 5: pl.p_state = 20; pl.p_auto = True; pl.p_face = 1; pl.p_xv = 2
                        else: s.lv_trig_on = True
                if pl.p_landed and not (s.lv_fx_wait > 0 and s.lv_fx_k != 5): s.lv_fx_k = 5; s.lv_fx_wait = 2
                if pl.p_snd != 0: s.lv_fx_k = pl.p_snd; s.lv_fx_wait = 2
                if s.lv_snd != 0: s.lv_fx_k = s.lv_snd; s.lv_fx_wait = 2      # the objects ask after the player: the last one to ask is heard
                if pl.p_out: s.lv_exit_t = s.lt
                if pl.p_restart: s.lv_restart_t = s.lt
            if s.lv_exit_t >= 0 and s.lt == s.lv_exit_t + 22: s.lv_done = True
            if s.lv_restart_t >= 0 and s.lt == s.lv_restart_t + 21: s.lv_pad_keep = pad; s.lv_pressed_keep = pressed
            if s.lv_restart_t >= 0 and s.lt == s.lv_restart_t + 24:
                s.lv_restart_t = -1; s.lt = -7; s.lv_cam_x = 0; s.lv_trig_on = True; s.lv_trig_wait = 0; pl.create(); s.reset_map()
                s.lv_fx_now = 0; s.lv_fx_wait = 0
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
            # of the player, then of the crates and enemies in the order of their places in the object list
            tl = s.pl.tiles(); bb = s.lv_bright
            for o in sorted(s.crates + s.enemies, key=lambda o: o.c_slot if isinstance(o, Crate) else o.e_slot):
                if not o.s_vis: continue
                if isinstance(o, Enemy):
                    for dx, dy, u in ETAB['tab'][o.s_pic]:
                        tx = o.s_x - dx - 8 if o.s_face else o.s_x + dx; ty = o.s_y + dy
                        if ty >= 0 and 0 <= tx <= 255: tl.append((tx, ty, ('n', (u * 2 + o.s_face) * 7 + bb)))
                elif o.s_pic >= 3:
                    for dx, dy, q in ETAB['pieces'][o.s_pic]:
                        tx = o.s_x + dx; ty = o.s_y + dy
                        if ty >= 0 and 0 <= tx <= 255: tl.append((tx, ty, ('c', bb, q)))
                else:                                       # each crate is four 8x8 NES sprites
                    for q, (dx, dy) in enumerate(((-8, -17), (-8, -9), (0, -17), (0, -9))):
                        tx = o.s_x + dx; ty = o.s_y + dy
                        if ty >= 0 and 0 <= tx <= 255: tl.append((tx, ty, ('c', o.s_flash * 7 + bb, q)))
                    if o.s_eyes:                            # the eyes: a 5th sprite
                        tx = o.s_x - (2 if o.s_eyes == 2 else 6); ty = o.s_y - 12
                        if ty >= 0 and 0 <= tx <= 255: tl.append((tx, ty, ('e', bb)))
            if not s.lv_ord: tl.reverse()
        for tx, ty, k in tl:
            if isinstance(k, tuple) and k[0] == 'e': im = EYES[k[1]]
            elif isinstance(k, tuple) and k[0] == 'n': im = ENEMY[k[1]]
            elif isinstance(k, tuple): im = CRATE[k[1]][(k[2] % 2) * 8:(k[2] % 2) * 8 + 8, (k[2] // 2) * 8:(k[2] // 2) * 8 + 8]
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
    n = bad_ram = bad_tiles = bad_pic = hits = 0; seen = {}; lastfc = -1; dropped = []; crowded = 0; far_t = -9; note = ''; examples = []; ev = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}; sq2 = [0, 0]; notes = 0; eyed = 0
    cels = [0, 1, 2, 3, 4, 5, 23, 22, 6, 7, 8, 11, 9, 10]
    for f in range(first, f0 + len(st)):
        S = st[f - f0]; r = S['ram']
        if f > first and g.lt >= 18 and int(r[0x2D]) == lastfc and g.lv_restart_t < 0 and g.lv_exit_t < 0:
            dropped.append(f); continue                     # the NES was too busy and left a frame out: the port waits
        lastfc = int(r[0x2D])
        g.end_step(pad(f)); p = g.pl
        if g.lv_exit_t >= 0 and g.lt > g.lv_exit_t + 30: break
        if g.ran and (int(r[0xB8]) not in NES_OK or int(r[0xC8]) & 0x80):
            note = 'enemy contact on NES frame %d' % f; break
        n += 1
        # sounds: each one the port starts must start on the NES on the same frame, and no others
        w = [tuple(q) for q in d['apu'][f - f0]]; pw = [tuple(q) for q in d['apu'][f - 1 - f0]] if f > f0 else []
        nes_now = set()
        if (0x4005, 0x94) in w and (0x4006, 0x8E) in w: nes_now.add(1)
        if (0x4005, 0x93) in w and (0x4006, 0x52) in w and (0x4005, 0x93) not in pw: nes_now.add(2)
        if (0x4006, 0x6A) in w and (0x4004, 0xBF) in w: nes_now.add(3)
        if (0x400C, 0xBF) in w and (0x400C, 0xBF) not in pw: nes_now.add(4)
        if (0x4006, 0x70) in w and (0x4004, 0xBF) in w: nes_now.add(5)
        if (0x4006, 0x3A) in w and (0x4007, 0xFA) in w and (0x4004, 0x3F) in w: nes_now.add(6)
        if (0x4006, 0xFD) in w and (0x4004, 0xBF) in w: nes_now.add(7)
        if (0x4005, 0x9D) in w and (0x4004, 0x3C) in w: nes_now.add(8)
        for k in g.started:
            ev[k] += 1
            if k in nes_now: nes_now.discard(k)
            else:
                bad_ram += 1
                if len(examples) < verbose: examples.append((f, 'sound %d expected' % k, w[:6]))
        if nes_now:
            bad_ram += 1
            if len(examples) < verbose: examples.append((f, 'sounds on the NES only', nes_now))
        # the long note of the bonus sound (frames 4..43 of the sound) must be going on exactly when the port says so
        for q in w:
            if q[0] == 0x4004: sq2[0] = q[1]
            if q[0] == 0x4006: sq2[1] = q[1]
        nes_note = sq2[1] == 0x36 and sq2[0] in (0x7F, 0x7C, 0x79, 0x76, 0x73)
        port_note = g.lv_fx_now == 3 and 4 <= g.lt - (g.lv_fx_end - 53) < 44
        nes_far = (0x400C, 0xBF) in w; port_far = g.lv_fx_now == 4 and g.lt - (g.lv_fx_end - 73) < 72
        if nes_far != port_far:
            bad_ram += 1
            if len(examples) < verbose: examples.append((f, 'far throw noise: NES %s, port %s' % (nes_far, port_far)))
        if nes_note: notes += 1
        # who has the 2nd square channel, frame by frame: the music writes volumes $Fx to $4004, the effects other values;
        # and whether an effect has the noise channel (bit 5 of $F1; the port: the far throw and the first 9 frames of the hit)
        if g.lt >= 19:
            nes_busy = (0 if sq2[0] >> 4 == 15 else 1) + ((int(r[0xF1]) >> 4) & 2)
            port_busy = (1 if g.lv_fx_now not in (0, 4) else 0) + (2 if g.lv_fx_now == 4 or (g.lv_fx_now == 8 and g.lt < g.lv_fx_end - 8) or (g.lv_fx_wait == 1 and g.lv_fx_k in (4, 8)) else 0)
            if g.lv_fx_now == 4: far_t = f
            if g.lv_fx_k == 4 or f - far_t <= 2: nes_busy &= 1; port_busy &= 1      # (the far throw's noise is compared above)
            if nes_busy != port_busy:
                bad_ram += 1
                if len(examples) < verbose: examples.append((f, 'channels taken by an effect: NES %d, port %d' % (nes_busy, port_busy), g.lv_fx_now, g.lv_fx_k, g.lv_fx_wait))
        if g.ran:
            cam = int(r[0x10]) + 256 * int(r[0x13])
            x = int(r[0x314]) + 256 * int(r[0x320]); y = int(r[0x2FC]) + 256 * int(r[0x308]); y = y - 65536 if y > 32767 else y
            v = int(r[0x35C]); v = v - 256 if v > 127 else v
            cel = int(r[0x338])
            nes = [int(r[0xB8]), x, cel if cel < 128 else -1, (int(r[0x344]) >> 6) & 1, int(r[0x3BC]), cam, int(r[0xA7]), (int(r[0x2E4]) >> 6) & 1, int(r[0xA3])]
            sim = [p.p_state, p.p_x, -1 if p.p_hide else cels[p.p_pic], p.p_face, p.p_h, g.lv_cam_x, g.lv_lives, int(p.p_carry is not None), g.lv_bonus]
            if p.p_state != 23: nes += [y, v, int(r[0x374]) >> 4]; sim += [p.p_y, p.p_yv, p.p_ysub]
            nsl = {}; ssl = {}; sg = lambda v: int(v) - 256 if v > 127 else int(v)
            for j in range(3, 12):
                fl = int(r[0x2F0 + j]); kd = fl & 15; ty = int(r[0x32C + j])
                ox = int(r[0x314 + j]) + 256 * int(r[0x320 + j]); ox = ox - 65536 if ox > 32767 else ox
                oy = int(r[0x2FC + j]) + 256 * int(r[0x308 + j]); oy = oy - 65536 if oy > 32767 else oy
                if ty == 3 and kd in (3, 9) and not fl & 0x80: nsl[j] = ('crate', ox + cam, oy)
                elif ty == 3 and kd == 1 and not fl & 0x80: nsl[j] = ('pieces', ox + cam, oy, int(r[0x338 + j]))
                elif kd in (6, 8) and fl & 0x80: nsl[j] = ('new', ox + cam, oy)
                elif kd in (6, 8) and ty == 7:
                    nsl[j] = (ox + cam, oy, int(r[0x368 + j]) >> 4, int(r[0x374 + j]) >> 4, sg(r[0x350 + j]), sg(r[0x35C + j]), int(r[0x338 + j]),
                              (int(r[0x344 + j]) >> 6) & 1, int(r[0x3D4 + j]), int(r[0x3C8 + j]), int(r[0x3B0 + j]), int(r[0x3BC + j]))
                o = g.lv_slot[j]
                if isinstance(o, Crate):
                    if o.c_mode == 5 and o.c_t > 0: ssl[j] = ('pieces', o.c_wx, o.c_y, o.c_pic)
                    else: ssl[j] = ('crate', o.c_wx, o.c_y)
                elif isinstance(o, Enemy):
                    if o.e_hide: ssl[j] = ('new', o.e_wx, o.e_y)
                    else: ssl[j] = (o.e_wx, o.e_y, o.e_xs, o.e_ys, o.e_xv, o.e_yv, o.e_pic, o.e_face, o.e_hp, o.e_dmg, o.e_w, o.e_h)
                    seen[o.e_kind] = seen.get(o.e_kind, 0) + 1
                    if o.e_state in (8, 9) and o.e_t0: o.e_t0 = False; hits += 1
            nes.append(nsl); sim.append(ssl)
            ce = int(r[0x338 + (int(r[0x2E4]) & 7)])            # the carried crate: 0 plain, 1 / 2 with eyes (8: for one frame after the pick-up, looks plain)
            if int(r[0x2E4]) & 0x40 and p.p_carry is not None and ce < 3:
                nes.append(ce); sim.append(p.p_carry.c_eyes); eyed += ce > 0
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
        if pictures:
            scr, tl = g.draw()
            o = S['oam'].reshape(64, 4).astype(int); vis = [(int(q[3]), int(q[0])) for q in o if q[0] < 0xEF]
            mine = set((tx, ty) for tx, ty, k in tl)
            if S['mask'] & 0x10 and not mine <= set(vis):
                bad_tiles += 1
                if len(examples) < verbose: examples.append((f, 'tiles missing on the NES', sorted(mine - set(vis))))
            # every NES sprite must be drawn by the port, except the hearts in the top left corner (a later step)
            need = set((int(q[3]), int(q[0])) for q in o if q[0] < 0xEF and int(q[1]) not in CP_HUD)
            if S['mask'] & 0x10 and g.lv_bright >= 0 and not need <= mine:
                bad_tiles += 1
                if len(examples) < verbose: examples.append((f, 'sprites missing in the port', sorted(need - mine)))
            # ... and in the order of the NES sprite list (the first one is in front: the port draws it last)
            pos = {}
            for k_, q in enumerate(o):
                if q[0] < 0xEF: pos.setdefault((int(q[3]), int(q[0])), []).append(k_)
            seq = [pos[(tx, ty)] for tx, ty, k in tl if (tx, ty) in pos]
            if S['mask'] & 0x10 and len(set(mine)) == len(tl) and all(len(v) == 1 for v in seq) and [v[0] for v in seq] != sorted([v[0] for v in seq], reverse=True):
                bad_tiles += 1
                if len(examples) < verbose: examples.append((f, 'sprite order', [v[0] for v in seq]))
            ok = np.ones((240, 256), bool)
            for x, y in vis:
                if (x, y) not in mine: ok[y + 1:y + 9, x:x + 8] = False
            # the NES shows at most 8 sprites on a picture line and leaves the others out; the port shows them all.
            # Lines with more than 8 are left out of the comparison (counted)
            per = np.zeros(260, int)
            for q in o:
                if q[0] < 0xEF: per[int(q[0]) + 1:int(q[0]) + 9] += 1
            if S['mask'] & 0x10: ok[per[:240] > 8, :] = False; crowded += int((per[:240] > 8).sum())
            diff = (scr != d['frames'][f - f0]).any(axis=2) & ok
            if diff.any():
                bad_pic += 1
                if len(examples) < verbose: ys, xs = np.nonzero(diff); examples.append((f, 'picture', int(diff.sum()), 'pixels, box', int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())))
                global PICS; PICS = PICS or (name, f, scr, d['frames'][f - f0])
    print('%-14s frames %4d  memory+sound %d  tiles %d  picture %d   sounds: pick %d, throw %d, far throw %d, bonus %d, landing %d, buzz %d, cook %d, hit %d  %s%s' % (
        name, n, bad_ram, bad_tiles, bad_pic, ev[1], ev[2], ev[4], ev[3], ev[5], ev[6], ev[7], ev[8], note + ('  eyes on %d frames' % eyed if eyed else ''), '  enemies hit: %d' % hits if hits else '') + '  enemy frames %s' % sorted(seen.items()) + ('  frames the NES left out: %s' % dropped if dropped else '') + ('  crowded lines %d' % crowded if crowded else ''))
    for e in examples: print('     ', e)
    return n, bad_ram + bad_tiles + bad_pic

if __name__ == '__main__':
    args = sys.argv[1:]; old = '--old' in args; nopic = '--nopic' in args; only = [a for a in args if not a.startswith('--')]; tot = [0, 0]
    for j in (CP.JOBS + CC.JOBS if old else CE.JOBS):
        if only and j[0] not in only: continue
        if 'exit' in j[0]: continue                         # (they start at the end of the section, among enemies: see sim_crates.py)
        r = compare(j[0], j[1], 3632 if 'exit' in j[0] else None, pictures=not nopic)
        tot[0] += r[0]; tot[1] += r[1]
    print('frames compared %d, frames with a difference %d' % tuple(tot))
