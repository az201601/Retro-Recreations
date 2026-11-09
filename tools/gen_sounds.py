#!/usr/bin/env python3
"""Create NES-flavoured SFX (square/noise) as 22.05kHz 16-bit mono WAVs."""
import os, wave, struct, math, random
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT,'ChipNRangers2.project','sound')
os.makedirs(OUT, exist_ok=True)
SR = 22050

def write(name, data, sr=SR):
    data = np.clip(data, -1, 1)
    ints = (data*32000).astype('<i2')
    with wave.open(os.path.join(OUT,name),'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(ints.tobytes())

def env(n, a=0.01, d=0.1):
    t = np.arange(n)/SR
    e = np.ones(n)
    na = max(1,int(a*SR)); nd = max(1,int(d*SR))
    e[:na] = np.linspace(0,1,na)
    if nd < n: e[-nd:] = np.linspace(1,0,nd)
    return e

def square(freq, dur, duty=0.5):
    n = int(SR*dur)
    if np.isscalar(freq):
        ph = np.arange(n)*freq/SR
    else:
        ph = np.cumsum(np.interp(np.arange(n), np.linspace(0,n-1,len(freq)), freq))/SR
    return np.where((ph % 1.0) < duty, 0.35, -0.35)

def sweep(f0,f1,dur,duty=0.5):
    n=int(SR*dur)
    f = np.linspace(f0,f1,n)
    return square(f, dur, duty)

def noise(dur, decay=8.0):
    n=int(SR*dur)
    rng = np.random.default_rng(1234)
    x = rng.uniform(-0.4,0.4,n)
    return x*np.exp(-decay*np.arange(n)/SR)

# jump: rising blip
j = sweep(260, 720, 0.13, 0.25)*env(int(SR*0.13),0.002,0.02)
write('sndJump.wav', j)
# throw: quick whoosh
t = sweep(700, 180, 0.10, 0.125)*env(int(SR*0.10),0.002,0.03)
write('sndThrow.wav', t)
# pickup
p = sweep(520, 880, 0.07, 0.5)*env(int(SR*0.07),0.002,0.02)
write('sndPickup.wav', p)
# break: noise burst
b = noise(0.22, 14)*env(int(SR*0.22),0.002,0.05)
write('sndBreak.wav', b)
# hurt: falling
h = sweep(420, 90, 0.30, 0.25)*env(int(SR*0.30),0.002,0.05)
write('sndHurt.wav', h)
# enemy hit
e = sweep(900, 300, 0.10, 0.5)*env(int(SR*0.10),0.002,0.04)
write('sndEnemyHit.wav', e)
# clear jingle
seq = []
for f in [523,659,784,1046]:
    seq.append(sweep(f,f,0.09,0.5)*env(int(SR*0.09),0.003,0.03))
c = np.concatenate(seq)
write('sndClear.wav', c)
# copy ripped bgm
import shutil
src = os.path.join(ROOT,'assets_src','audio','bgm_stage1.wav')
if os.path.exists(src):
    shutil.copy(src, os.path.join(OUT,'bgmStage1.wav'))
    print('music copied')
print('sfx written')
