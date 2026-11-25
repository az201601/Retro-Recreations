#!/usr/bin/env python3
import os, subprocess, hashlib, shutil, sys, random
from pathlib import Path
try:
    from PIL import Image, ImageStat, ImageChops
except Exception:
    Image=None

ROOT = Path('/home/user/Retro-Recreations')
EMU = ROOT/'tools/out/emu/fceumm_headless'
CORE = ROOT/'tools/out/emu/fceumm_libretro.so'
ROM = ROOT/"Chip 'n Dale - Rescue Rangers 2 (USA).nes"
BASE_INPUT = ROOT/'tools/emu/inputs/stage_01_restaurant_to_gameplay.txt'
OUT = Path('/tmp/s1drive')
OUT.mkdir(exist_ok=True)

def load_base():
    lines = BASE_INPUT.read_text().strip().splitlines()
    # strip trailing RIGHT if any
    if lines and lines[-1].endswith(',RIGHT') and 'down' in lines[-1]:
        lines = lines[:-1]
    return lines

def run_emu(input_path, total, shots, outdir):
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True)
    cmd = [str(EMU),'--core',str(CORE),'--rom',str(ROM),
           '--frames',str(total),'--shots',','.join(map(str,shots)),
           '--inputs',str(input_path),'--out',str(outdir),
           '--cheat','OUXLLEVS','--cheat','NXKZKTVI','--cheat','OXUNGIVK']
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-500:], r.stderr[-500:])
    return r.returncode == 0

def ppm_hash(p):
    if Image is None:
        b = Path(p).read_bytes()
        parts = b.split(b'\n',3)
        return hashlib.md5(parts[3] if len(parts)>3 else b).hexdigest()
    im = Image.open(p).convert('RGB').crop((0,24,256,232))
    # quantize to reduce sprite/animation noise
    small = im.resize((64,52), Image.NEAREST).convert('P', palette=Image.ADAPTIVE, colors=32)
    return hashlib.md5(small.tobytes()).hexdigest()

def ppm_dark(p):
    if Image is None:
        b = Path(p).read_bytes()
        parts = b.split(b'\n',3)
        data = parts[3] if len(parts)>3 else b
        sample = data[:3000]
        return (sum(sample)/len(sample)) < 20
    im = Image.open(p).convert('L')
    return ImageStat.Stat(im).mean[0] < 20

def main():
    base = load_base()
    # start with known good pattern
    extra = []
    extra.append('11100,down,RIGHT')
    t = 11120
    end = 11120
    seen = set()
    stuck = 0
    strategy = 0
    # strategies: 0=R+jump,1=R+jump+UP,2=R+jump+DOWN,3=R+fastjump,4=LEFT then RIGHT
    def add_chunk(start_t, strat, nframes=1800):
        lines = []
        t = start_t
        lines.append(f'{t},up,LEFT')
        lines.append(f'{t},up,UP')
        lines.append(f'{t},up,DOWN')
        lines.append(f'{t},down,RIGHT')
        for i in range(0, nframes, 15):
            tt = t+i
            if strat == 0:
                if i%30==0: lines.append(f'{tt},down,A'); lines.append(f'{tt+6},up,A')
                if i%90==0: lines.append(f'{tt+10},down,B'); lines.append(f'{tt+15},up,B')
            elif strat == 1:
                if i%30==0: lines.append(f'{tt},down,A'); lines.append(f'{tt+6},up,A')
                if i%90==0: lines.append(f'{tt+10},down,B'); lines.append(f'{tt+15},up,B')
                if i%300==0: lines.append(f'{tt+12},down,UP'); lines.append(f'{tt+25},up,UP')
            elif strat == 2:
                if i%20==0: lines.append(f'{tt},down,A'); lines.append(f'{tt+5},up,A')
                if i%60==0: lines.append(f'{tt+8},down,B'); lines.append(f'{tt+13},up,B')
            elif strat == 3:
                if i%30==0: lines.append(f'{tt},down,A'); lines.append(f'{tt+6},up,A')
                if i%120==0: lines.append(f'{tt},up,RIGHT'); lines.append(f'{tt},down,DOWN')
                if i%120==15: lines.append(f'{tt},up,DOWN'); lines.append(f'{tt},down,RIGHT')
            elif strat == 4:
                if i<60:
                    lines.append(f'{tt},up,RIGHT'); lines.append(f'{tt},down,LEFT')
                elif i==60:
                    lines.append(f'{tt},up,LEFT'); lines.append(f'{tt},down,RIGHT')
                if i%30==0: lines.append(f'{tt},down,A'); lines.append(f'{tt+6},up,A')
            lines.append(f'{tt+15},up,B') if False else None
        return lines, t+nframes

    cur_t = 11120
    input_lines = list(base) + ['11100,down,RIGHT']
    last_new_hash = None
    no_progress = 0
    best_t = cur_t
    for chunk_idx in range(60):
        chunk_lines, next_t = add_chunk(cur_t, strategy, 2400)
        trial = input_lines + chunk_lines
        shot = next_t - 60
        inp = OUT/'input.txt'
        inp.write_text('\n'.join(trial)+'\n')
        outdir = OUT/f'c{chunk_idx:02d}'
        ok = run_emu(inp, next_t, [shot, next_t-300, next_t-600], outdir)
        if not ok:
            print('emu failed'); break
        # check shots
        shot_files = sorted(outdir.glob('frame_*.ppm'))
        if not shot_files:
            print('no shots'); break
        h = ppm_hash(shot_files[-1])
        dark = ppm_dark(shot_files[-1])
        is_new = h not in seen
        seen.add(h)
        print(f'chunk {chunk_idx} t={next_t} strat={strategy} dark={dark} new={is_new} hash={h[:8]}')
        if dark:
            # respawn/death screen - don't commit, try different strategy
            strategy = (strategy+1)%5
            no_progress += 1
            # do not advance input_lines/cur_t
        elif is_new:
            input_lines = trial
            cur_t = next_t
            best_t = cur_t
            no_progress = 0
        else:
            # loop/repeat - don't commit, try different strategy
            no_progress += 1
            strategy = (strategy+1)%5
        if no_progress > 8:
            print('stuck, stopping')
            break
        if cur_t > 90000:
            print('reached time limit')
            break
    # save best input
    shutil.copy(OUT/'input.txt', OUT/'best_input.txt')
    print('best_t', best_t)

if __name__ == '__main__':
    main()
