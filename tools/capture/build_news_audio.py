#!/usr/bin/env python3
"""Deliverable 4 sounds: the cutscene music as two layers (square 2 apart, because the typing sound interrupts it) and the
six typing sounds.  Everything is retimed to 800 samples per frame @48 kHz (1 GMS step at room_speed 60 = 1 NES frame).
Also writes work/news_audio.pkl (note starts of the square-2 layer, voice of each page) for build_news.py / sim_news.py."""
import os, pickle, collections
import numpy as np, soxr, soundfile as sf
from scenario import load
from emu import WORK
from news_model import idle, run, T0
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'recreation', '04_newscaster', 'assets', 'sounds'); os.makedirs(OUT, exist_ok=True)
M0 = 2303; LOOP = 1920                       # first frame of the music, loop length in frames

def ogg(y, name):
    with sf.SoundFile('%s/%s.ogg' % (OUT, name), 'w', samplerate=48000, channels=1, format='OGG', subtype='VORBIS') as f:
        for i in range(0, len(y), 2048): f.write(y[i:i + 2048].astype(np.float32))
    print('%-22s %6.2f s  peak %.3f  %d bytes' % (name, len(y) / 48000, np.abs(y).max(), os.path.getsize('%s/%s.ogg' % (OUT, name))))
def retime(x, frames):
    y = soxr.resample(x, len(x) * 60.0 / frames, 48000, quality='VHQ'); N = frames * 800
    return y[:N] if len(y) >= N else np.concatenate([y, np.zeros(N - len(y))])
def cut(d, a, b):                            # samples of NES frames a .. b-1
    return d['aud'][d['cnt'][a - 1]:d['cnt'][b - 1]].astype(np.float64) / 32768

I = idle(); BM = run('news_bmash', 2); BS = run('news_bslow', 3)
def ticks(recs, a, b): return [f for f in range(a, b) if f in recs and recs[f]['apu'] and recs[f]['apu'][0] == (0x400C, 0xF0) and f > M0]
def busy(recs, a, b, n=4):                   # frames on which the typing sound owns square 2: 4 after each tick
    s = set()
    for T in ticks(recs, a, b): s |= set(range(T + 1, T + 1 + n))
    return s
# ---- note starts of the square-2 voice (frames of the loop on which the music writes the period registers; the driver
# also rewrites them on the frame after a typing sound, so look only at frames well away from one)
iters = [(I, M0 + LOOP * i) for i in range(4)] + [(BM, M0), (BS, M0)]
PER = [None] * LOOP                          # period registers of the music's square 2 at each frame of the loop
for recs, base in iters:
    bz = busy(recs, base - 20, base + LOOP + 10); cur = None
    for f in range(base - 12, base + LOOP):
        w = dict((a, v) for a, v in recs[f]['apu']) if f in recs else {}
        if f in bz or f < 2310: cur = None
        elif 0x4006 in w and 0x4007 in w: cur = (w[0x4006], w[0x4007] & 7)
        if f >= base and cur is not None:
            assert PER[f - base] in (None, cur), 'music is not the same in every loop'
            PER[f - base] = cur
for p in range(LOOP):                        # frames hidden by typing in every loop: notes start on multiples of 6
    if PER[p] is None: PER[p] = PER[p - 1] if p % 6 else next((PER[q] for q in range(p, p + 6) if PER[q] is not None), PER[p - 1])
starts = set()
for recs, base in iters:                     # real note starts (period written by the music itself, away from typing)
    bz = busy(recs, base - 20, base + LOOP + 10, 9)
    starts |= {f - base for f in range(max(base, 2310), base + LOOP) if f not in bz and any(a == 0x4007 for a, v in recs[f]['apu'])}
notes = sorted(starts | {0} | {p for p in range(1, LOOP) if PER[p] != PER[p - 1]})
print('square-2 note starts in the loop:', len(notes))

# ---- layer A: everything except square 2
a = load('news_aud_a'); ogg(retime(cut(a, M0, M0 + LOOP), LOOP), 'snd_news_music_a')
# ---- layer B: square 2, note by note from a loop in which the typing sound does not touch that note
b = load('news_aud_b'); bh = load('news_aud_bh'); BH = {bh['f0'] + i: dict(apu=w) for i, w in enumerate(bh['apu'])}
# (audio, APU log, frame of loop position 0, usable loop positions).  The first frames of the first loop still carry the
# end of the night scene's alarm
src = [(load('news_aud_bm'), BM, M0, (10, LOOP)), (load('news_aud_bs'), BS, M0, (10, LOOP)), (bh, BH, M0, (3066 - M0, 3316 - M0))] + \
      [(b, I, M0 + LOOP * i, (10 if i == 0 else 0, LOOP)) for i in range(4)]
parts = []; used = collections.Counter(); todo = []
def clean_copy(n0, n1):
    for si, (d, recs, base, (lo, hi)) in enumerate(src):
        bz = busy(recs, base + n0 - 20, base + n1 + 10)
        if lo <= n0 and n1 <= hi and not any(base + p in bz for p in range(n0, n1)): return si, cut(d, base + n0, base + n1)
    return None
def start_regs(n0): return PER[n0]
bounds = [(n0, notes[i + 1] if i + 1 < len(notes) else LOOP) for i, n0 in enumerate(notes)]
for n0, n1 in bounds:
    c = clean_copy(n0, n1)
    if c is None:                            # every loop has typing here: use another note with the same pitch and length
        for m0, m1 in bounds:
            if (m0, m1) != (n0, n1) and m1 - m0 == n1 - n0 and start_regs(m0) == start_regs(n0) and clean_copy(m0, m1):
                c = clean_copy(m0, m1); print('note at %d: copy of the identical note at %d' % (n0, m0)); break
        else: raise SystemExit('no clean copy of note %d' % n0)
    used[c[0]] += 1; parts.append(c[1])
print('notes taken from: B-mash run %d, slow B run %d, B-held run %d, idle loops %s' % (used[0], used[1], used[2], [used[i] for i in range(3, 7)]))
layer_b = retime(np.concatenate(parts), LOOP); ogg(layer_b, 'snd_news_music_b')
# ---- typing sounds: one per voice (square-2 period), 3 frames
voice = {}; page_voice = []
M = pickle.load(open(os.path.join(WORK, 'news_model.pkl'), 'rb'))
for k, p in enumerate(M['pages']):
    T = [t for t in ticks(I, p['first'], p['end'])][3]
    key = tuple(v for a, v in I[T + 1]['apu'] if 0x4004 <= a <= 0x4007)
    if key not in voice:
        voice[key] = len(voice); ogg(retime(cut(b, T + 1, T + 4), 3), 'snd_news_type_%d' % voice[key])
    page_voice.append(voice[key])
print('voice of each page:', page_voice)
# ---- check of the gate rule on the idle run: a typing sound takes square 2 away from the music for 4 frames, and the
# music's voice stays silent until its next note starts (a note that starts during those 4 frames sounds from the 5th)
def rms(x): x = x - x.mean(); return float(np.sqrt((x ** 2).mean()))
tk = set(ticks(I, M0, 10800)); bz = busy(I, M0, 10780); gate = 1; bad = 0; n = 0; pend = 0
for f in range(M0 + 10, 10780):
    p = (f - M0) % LOOP
    if f - 1 in tk: gate = 0; pend = 0
    if p in notes: pend = 1
    if f not in bz and pend: gate = 1
    if f not in bz: pend = 0
    if f in bz: continue                                     # the typing sound itself
    want = rms(layer_b[p * 800:(p + 1) * 800]) if gate else 0.0; got = rms(cut(b, f, f + 1)); n += 1
    if abs(want - got) > 0.25 * max(want, got) + 0.004: bad += 1
print('gate check: %d frames outside typing sounds, level differs on %d' % (n, bad))
pickle.dump(dict(notes=notes, page_voice=page_voice, loop=LOOP, m0=M0 - T0), open(os.path.join(WORK, 'news_audio.pkl'), 'wb'))
