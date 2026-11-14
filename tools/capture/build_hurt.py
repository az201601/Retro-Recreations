#!/usr/bin/env python3
"""Deliverable 10 (level 1, section 1: hearts, getting hurt, lives, the status screen, game over, continue): builds
  recreation/10_level1_hurt/assets/sprites/
    spr_chip_hurt_strip<N>.png, spr_dale_hurt_strip<N>.png   the 8x8 tiles of the two new pictures (hurt, stunned);
                                 sub-image = (tile * 2 + (0 mirrored = facing right, 1 as stored)) * 7 + brightness
    spr_hud_strip21.png          Chip's face, a heart, Dale's face: sub-image = which * 7 + brightness
    spr_star_strip7.png          the star over a stunned character, 7 brightness steps
    spr_status_strip4.png        the status screen (SELECT) without its numbers: who * 2 + lv_ord (which way the sprite list ran when SELECT was pressed)
    spr_status_digit_strip10.png the digits of the status screen
    spr_gameover_bg_strip7.png   the GAME OVER screen without the words, 7 brightness steps (0-2 fading in, 3 full, 4-6 fading out)
    spr_gameover_text_strip7.png the words
    spr_continue_bg_strip7.png   the continue screen without arrow, number and character; the picture's background colour
                                 is transparent (the character is drawn behind it)
    spr_continue_arrow_strip7.png, spr_continue_digit_strip28.png (digit * 7 + brightness)
    spr_continue_wake_strip6.png the dizzy character with its star while the screen fades in: who * 3 + brightness
    spr_continue_star.png
  recreation/10_level1_hurt/assets/sounds/snd_hurt.ogg, snd_stun.ogg, snd_gameover.ogg, snd_cursor.ogg, snd_confirm.ogg
  work/hu_tables.pkl      the tables (used by sim_hurt.py)
  work/hurt_tables.gml    the same as GML text (pasted into obj_player Create and obj_stage1 Create)
The two new pictures come from the ROM (bank 5, the picture lists of object types 1 = Chip and 2 = Dale, see
build_enemies.py); everything else from the capture_hurt.py recordings.  sim_hurt.py checks every frame against them.
usage: build_hurt.py"""
import os, pickle, zlib
import numpy as np
from PIL import Image
from scenario import load
from emu import WORK
import ppu, build_player as BP, build_crates as BC, build_enemies as BE
ROOT = BP.ROOT
OUT = os.path.join(ROOT, 'recreation', '10_level1_hurt', 'assets')
T0 = 2667                 # NES frame of the 3rd fall in the gover runs
HUD = (0x87, 0x88, 0x89)

def pic(d, f): return np.frombuffer(zlib.decompress(d['zframes'][f - d['f0']]), np.uint8).reshape(240, 256, 3).copy()
def save(im, name): Image.fromarray(im).save('%s/sprites/%s.png' % (OUT, name)); print('%-34s %d x %d' % (name, im.shape[1], im.shape[0]))
def rgba(im, clear=None):
    """RGB -> RGBA; clear: mask of the transparent pixels (default: the black ones)"""
    a = np.zeros(im.shape[:2] + (4,), np.uint8); a[:, :, :3] = im
    a[:, :, 3] = np.where((im == 0).all(axis=2) if clear is None else clear, 0, 255); return a
def vram_at(d, f):
    while d['st'][f - d['f0']]['vram'] is None: f += 1
    return d['st'][f - d['f0']]['vram'], f

def player_and_hud(g, tabs):
    pal = BP.palettes()
    def paint(px, k, m, a):
        for b in range(7):
            for yy in range(8):
                for xx in range(8):
                    if m[yy, xx]: px[(k + b) * 8 + xx, yy] = tuple(int(v) for v in ppu.RGB[pal[b][a * 4 + m[yy, xx]] & 63]) + (255,)
    old = pickle.load(open(os.path.join(WORK, 'cr_tables.pkl'), 'rb'))
    for who, typ, run in (('chip', 1, 'hu_route'), ('dale', 2, 'dl_hu_route')):
        d = load(run); chr_ = vram_at(d, 2160)[0][0x1000:0x2000].copy()
        lay = {c: [(-dx - 8, dy, t, a) for dx, dy, t, a in BE.cel(typ, c)] for c in (12, 13)}
        uniq = []
        for c in (12, 13):
            for dx, dy, t, a in lay[c]:
                assert a & 0xFC == 0, hex(a)
                if (t, a) not in uniq: uniq.append((t, a))
        n = len(uniq) * 14; strip = Image.new('RGBA', (n * 8, 8), (0, 0, 0, 0)); px = strip.load()
        for u, (t, a) in enumerate(uniq):
            im = ppu.tile(chr_, t * 16)
            for left in (0, 1): paint(px, (u * 2 + left) * 7, im if left else im[:, ::-1], a)
        strip.save('%s/sprites/spr_%s_hurt_strip%d.png' % (OUT, who, n)); print('spr_%s_hurt_strip%d: %d tiles' % (who, n, len(uniq)))
        base = old[who]['n'] // 14
        tab = {c: [(dx, dy, base + uniq.index((t, a))) for dx, dy, t, a in lay[c]] for c in (12, 13)}
        tabs[who] = dict(tab=tab, n=n, base=base)
        g.append('// %s: the pictures 14 (hurt) and 15 (stunned), as in the tables above.  Tiles from %d on are in' % (who, base))
        g.append('// spr_%s_hurt: sub-image ((tile - %d) * 2 + (1 - facing)) * 7 + brightness' % (who, base))
        for i, c in ((14, 12), (15, 13)):
            g.append('p_tn[%d] = %d;' % (i, len(tab[c])))
            g.append(' '.join('p_tdx[%d,%d] = %d; p_tdy[%d,%d] = %d; p_tim[%d,%d] = %d;' % (i, j, dx, i, j, dy, i, j, u) for j, (dx, dy, u) in enumerate(tab[c])))
        g.append('')
        if who == 'chip':
            # the hearts: the three tiles and where the NES shows them
            o = d['st'][1500 - d['f0']]['oam'].reshape(64, 4); at = {int(q[1]): int(q[2]) for q in o if int(q[1]) in HUD}
            hud = Image.new('RGBA', (21 * 8, 8), (0, 0, 0, 0)); px = hud.load()
            for k, t in enumerate(HUD):
                a = at.get(t, at[0x87]); assert a & 0xFC == 0
                paint(px, k * 7, ppu.tile(chr_, t * 16), a)
            hud.save('%s/sprites/spr_hud_strip21.png' % OUT); print('spr_hud_strip21')
            # the star over a stunned character (tile $5E, sprite palette 1)
            star = Image.new('RGBA', (7 * 8, 8), (0, 0, 0, 0)); paint(star.load(), 0, ppu.tile(chr_, 0x5E * 16), 1)
            star.save('%s/sprites/spr_star_strip7.png' % OUT); print('spr_star_strip7')
            tabs['hud_chip'] = sorted((int(q[3]), int(q[0]), int(q[1])) for q in o if int(q[1]) in HUD and q[0] < 0xEF)
        else:
            o = d['st'][1500 - d['f0']]['oam'].reshape(64, 4)
            tabs['hud_dale'] = sorted((int(q[3]), int(q[0]), int(q[1])) for q in o if int(q[1]) in HUD and q[0] < 0xEF)
        del d
    print('hearts: Chip', tabs['hud_chip'], ' Dale', tabs['hud_dale'])

def sounds():
    import soxr
    def part(run, first, n, total):
        s = load(run); x = s['aud'][s['cnt'][first - 1]:s['cnt'][first - 1 + n]].astype(np.float64) / 32768
        y = soxr.resample(x, len(x) * 60.0 / n, 48000, quality='VHQ'); y = y[:n * 800]
        return np.concatenate([y, np.zeros(total * 800 - len(y))])
    def W(d, f): return [tuple(q) for q in d['apu'][f - d['f0']]]
    # hurt: the 2nd square channel for 16 frames, the noise channel for 24 (asked for on frame 1500, starts on 1501)
    d = load('hu_fx_hurt_sq2')
    assert (0x4006, 0x3F) in W(d, 1501) and (0x4005, 0x93) in W(d, 1501) and (0x4004, 0x30) in W(d, 1516) and (0x4004, 0xF0) in W(d, 1517), 'hurt sound not where expected'
    assert (0x400C, 0x3F) in W(d, 1501) and (0x400E, 0x00) in W(d, 1524) and (0x400E, 0x00) in W(d, 1525) and (0x400E, 0x0B) in W(d, 1526)
    BC.ogg(part('hu_fx_hurt_sq2', 1501, 16, 24) + part('hu_fx_hurt_noi', 1501, 24, 24), 'snd_hurt')
    # stunned: the 2nd square channel for 97 frames
    d = load('hu_fx_stun_sq2')
    assert (0x4006, 0x46) in W(d, 1501) and (0x4004, 0xBF) in W(d, 1596) and (0x4004, 0xB0) in W(d, 1597) and (0x4004, 0xF0) in W(d, 1598), 'stun sound not where expected'
    BC.sound('hu_fx_stun_sq2', 1501, 97, 'snd_stun')
    # game over: the level music stops 85 frames after the fall (with the picture), the tune plays from frame 86 on (all channels)
    d = load('hu_gover_b')
    assert (0x400C, 0xF0) in W(d, T0 + 85) and (0x4000, 0xFF) in W(d, T0 + 86) and (0x4002, 0xD5) in W(d, T0 + 86) and (0x400A, 0xD5) in W(d, T0 + 86), 'game over tune not where expected'
    cnt = d['cnt']; rms = lambda f: float(np.sqrt((d['aud'][cnt[f - 1]:cnt[f]].astype(float) ** 2).mean()))
    end = next(f for f in range(T0 + 200, T0 + 300) if rms(f) < 1 and rms(f + 1) < 1 and rms(f + 2) < 1)
    print('game over tune: frames %d .. %d after the fall' % (86, end - T0 - 1))
    BC.sound('hu_gover_b', T0 + 86, end - T0 - 86, 'snd_gameover')
    # the continue screen is silent but for its two effects (2nd square channel); taken from the run itself
    def effect(first, name):
        assert any(a == 0x4004 and v != 0xF0 for a, v in W(d, first)) and all(not (a == 0x4004 and v != 0xF0) for a, v in W(d, first - 1)), name
        n = next(k for k in range(1, 60) if rms(first + k) < 1 and rms(first + k + 1) < 1)
        BC.sound('hu_gover_b', first, n, name); return n
    n1 = effect(T0 + 415, 'snd_cursor'); n2 = effect(T0 + 484, 'snd_confirm')
    print('arrow sound %d frames, choice sound %d frames' % (n1, n2))
    return dict(gameover=end - T0 - 86, cursor=n1, confirm=n2)

if __name__ == '__main__':
    BC.OUT = OUT
    os.makedirs(OUT + '/sprites', exist_ok=True); os.makedirs(OUT + '/sounds', exist_ok=True)
    for old in os.listdir(OUT + '/sprites'): os.remove(os.path.join(OUT, 'sprites', old))
    g = []; tabs = {}
    player_and_hud(g, tabs)
    import build_hurt_screens as BS
    BS.screens(g, tabs, OUT)
    tabs['snd'] = sounds()
    pickle.dump(tabs, open(os.path.join(WORK, 'hu_tables.pkl'), 'wb'))
    open(os.path.join(WORK, 'hurt_tables.gml'), 'w').write('\n'.join(g) + '\n')
