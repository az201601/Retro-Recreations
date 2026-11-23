#!/usr/bin/env python3
"""Extract character animation frames using OAM dumps + screenshots.

Pipeline per frame:
  1. parse OAM page $0600 -> character sprites (flipH set, tile<0x40) vs HUD
  2. priority mask: pixels covered by a lower-index (higher priority) sprite
  3. for each sprite: match its 8x8 screenshot cell against ALL CHR tiles with:
       - background colors (from neighbouring bg cells) must map to index 0
       - other colors map consistently to indices 1..3
       - pixels covered by higher-priority sprites are wildcards
  4. compose the frame from matched tiles (exact screen replica, idx0 transparent)
Verification: every matched tile is an exact CHR hit (same standard as bg verify).
"""
import sys, os, glob, itertools, numpy as np
from PIL import Image
sys.path.insert(0, 'tools')
from verify_chr2 import load_ppm, match_cell_bg, ALL_TILES

# precompute all tiles as (8192,64) int array
TILES = np.stack([t[2].flatten() for t in ALL_TILES])  # (8192,64)
TILE_KEYS = {tuple(t[2].flatten()): (t[0], t[1]) for t in ALL_TILES}
PREFER = {(t[0], t[1]): i for i, t in enumerate(ALL_TILES)}  # (bank,tile)->row

def parse_oam(path, page=0x600):
    d = open(path, 'rb').read()
    out = []
    for i in range(64):
        y, t, a, x = d[page + i*4: page + i*4 + 4]
        if y >= 0xEF:
            continue
        out.append(dict(idx=i, y=y + 1, tile=t, attr=a, x=x,
                        fh=bool(a & 0x40), fv=bool(a & 0x80),
                        size16=bool(a & 0x20), pal=a & 3))
    return out

def is_character(s):
    # HUD sprites: no flip, tiles 0x87/0x88 at fixed spot
    return s['fh'] and s['tile'] < 0x40 and not s['size16']

def bg_colors_near(frame, x, y, yrad=8, bgm=None):
    """Background colors for a sprite cell: bg-matched cells in the SAME
    horizontal band (avoids pulling colors from shelf/window rows)."""
    if bgm is None:
        bgm = {}
        H, W, _ = frame.shape
        for gy in range(0, H, 8):
            for gx in range(0, W, 8):
                m = match_cell_bg(frame[gy:gy+8, gx:gx+8])
                if m:
                    bgm[(gx, gy)] = set(m[2])
    from collections import Counter
    cnt = Counter()
    ncells = 0
    for (ngx, ngy), p in bgm.items():
        if abs(ngx - x) <= 40 and (ngy + 8 > y - yrad) and (ngy < y + yrad + 8):
            ncells += 1
            for c in p:
                cnt[c] += 1
    if not ncells:
        return set()
    return {c for c, n in cnt.items() if n >= 2}

def match_sprite_cell(cell, bg_cols, wild=None, prefer_idx=None):
    """cell 8x8x3; bg_cols: candidate background colors; wild: 8x8 ignore mask.
    prefer_idx: TILES row to try first (bank7 + OAM tile number) — wins ties.

    Sprite rules (idx0 = transparent hole showing background):
      - strict colors (not in bg_cols) must map to a single index > 0
      - background colors may sit at index 0, or claim an unowned index
        (handles outline-black == shadow-black collisions)
      - each index > 0 owns exactly one color
    Returns (bank, tile, color_to_idx, tile8x8) or None (best-scored)."""
    if wild is None:
        wild = np.zeros((8, 8), dtype=bool)
    flat = cell.reshape(-1, 3)
    wf = wild.reshape(-1)
    vis = [i for i in range(64) if not wf[i]]
    if not vis:
        return None
    def col(i):
        return (int(flat[i, 0]), int(flat[i, 1]), int(flat[i, 2]))
    strict = [i for i in vis if col(i) not in bg_cols]
    soft = [i for i in vis if col(i) in bg_cols]
    if not strict and not soft:
        return None
    # note: strict may be empty (sprite cell entirely bg-coloured, e.g. a
    # lowest-priority sprite transparent over the floor). Soft-only match is
    # still exact for composition (colors come from the screen) — proceed.
    # candidate filter: strict px must be idx > 0
    cand = np.where((TILES[:, strict] > 0).all(axis=1))[0]
    if prefer_idx is not None and prefer_idx not in cand:
        cand = np.concatenate(([prefer_idx], cand))
    elif prefer_idx is not None:
        cand = np.concatenate(([prefer_idx], cand[cand != prefer_idx]))
    best = None
    for c in cand:
        tile = TILES[c]
        c2i, i2c = {}, {}
        ok = True
        for i in strict:
            cc, idx = col(i), int(tile[i])
            if cc in c2i and c2i[cc] != idx:
                ok = False; break
            if idx in i2c and i2c[idx] != cc:
                ok = False; break
            c2i[cc] = idx; i2c[idx] = cc
        if not ok:
            continue
        # soft px: idx0 free; unowned idx may be claimed (single color);
        # owned idx must match owner color (else contradiction)
        score = 0
        for i in soft:
            idx = int(tile[i])
            if idx == 0:
                score += 1
                continue
            cc = col(i)
            if idx in i2c:
                # already owned: must be the same color (owner may be a strict
                # color or an earlier soft claim of this very color)
                if i2c[idx] != cc:
                    ok = False; break
                continue
            # unowned index: claim it, requiring all its pixels to agree
            for j in vis:
                if int(tile[j]) == idx and col(j) != cc:
                    ok = False; break
            if not ok:
                break
            i2c[idx] = cc; c2i[cc] = idx
        if not ok:
            continue
        if best is None or score > best[0]:
            b, t = TILE_KEYS[tuple(tile)]
            best = (score, b, t, dict(c2i), tile.reshape(8, 8))
        if not strict and prefer_idx is not None and c == prefer_idx:
            break  # soft-only: trust the OAM-indicated tile's structure
    if best:
        return (best[1], best[2], best[3], best[4])
    return None

def render_tile(tile_idx, c2i, fh, fv):
    """tile 8x8 indices -> RGB or None for transparent(0)."""
    out = np.zeros((8, 8, 3), dtype=np.uint8)
    vis = np.zeros((8, 8), dtype=bool)
    inv = {v: k for k, v in c2i.items()}
    for r in range(8):
        for c in range(8):
            v = int(tile_idx[r, c])
            if v == 0 or v not in inv:
                continue
            col = inv[v]
            out[r, c] = col
            vis[r, c] = True
    if fh:
        out = out[:, ::-1]; vis = vis[:, ::-1]
    if fv:
        out = out[::-1, :]; vis = vis[::-1, :]
    return out, vis

def extract_frame(shot_path, ram_path):
    frame = load_ppm(shot_path)
    oam = parse_oam(ram_path)
    chars = [s for s in oam if is_character(s)]
    if not chars:
        return None, dict(error='no character sprites')
    # priority: lower idx = higher priority -> drawn last (on top)
    chars.sort(key=lambda s: -s['idx'])  # paste order: high idx first
    # bbox
    xs0 = min(s['x'] for s in chars); ys0 = min(s['y'] for s in chars)
    xs1 = max(s['x'] + 8 for s in chars); ys1 = max(s['y'] + 8 for s in chars)
    W, H = xs1 - xs0, ys1 - ys0
    canvas = np.zeros((H, W, 3), dtype=np.uint8)
    canvas_vis = np.zeros((H, W), dtype=bool)
    stats = dict(total=len(chars), matched=0, failed=0, skipped=0, banks=set())
    # bg cache for whole frame (once)
    bgm = {}
    for gy in range(0, frame.shape[0], 8):
        for gx in range(0, frame.shape[1], 8):
            m = match_cell_bg(frame[gy:gy+8, gx:gx+8])
            if m:
                bgm[(gx, gy)] = set(m[2])
    from collections import Counter
    gcnt = Counter()
    for p in bgm.values():
        for c in p:
            gcnt[c] += 1
    global_bgc = {c for c, n in gcnt.items() if n >= 2}
    # compute wildcards per sprite (pixels covered by higher-prio = lower idx)
    # chars currently sorted descending idx (paste order). For sprite s:
    # wild = covered by any sprite with idx < s.idx, PLUS px where a lower-prio
    # sprite (already processed) paints that exact color — NES fall-through:
    # a transparent px reveals the NEXT lower-prio sprite (not the background),
    # so such colors cannot be attributed to s.
    renders = {}  # idx -> (rgb, vis) painted by that sprite
    for s in chars:  # high idx -> low idx (painter: low idx painted last/on top)
        wild = np.zeros((8, 8), dtype=bool)
        for o in chars:
            if o['idx'] >= s['idx']:
                continue
            ox0, oy0 = max(o['x'], s['x']), max(o['y'], s['y'])
            ox1, oy1 = min(o['x']+8, s['x']+8), min(o['y']+8, s['y']+8)
            if ox0 < ox1 and oy0 < oy1:
                wild[oy0-s['y']:oy1-s['y'], ox0-s['x']:ox1-s['x']] = True
        for o in chars:  # lower-prio (higher idx) — already rendered above
            if o['idx'] <= s['idx'] or o['idx'] not in renders:
                continue
            ox0, oy0 = max(o['x'], s['x']), max(o['y'], s['y'])
            ox1, oy1 = min(o['x']+8, s['x']+8), min(o['y']+8, s['y']+8)
            if not (ox0 < ox1 and oy0 < oy1):
                continue
            orgb, ovis = renders[o['idx']]
            for yy in range(oy0, oy1):
                for xx in range(ox0, ox1):
                    if ovis[yy - o['y'], xx - o['x']] and \
                       tuple(orgb[yy - o['y'], xx - o['x']]) == tuple(frame[yy, xx]):
                        wild[yy - s['y'], xx - s['x']] = True
        cell = frame[s['y']:s['y']+8, s['x']:s['x']+8]
        # screen shows the tile mirrored (fh/fv); match against stored orientation
        mcell, mwild = cell, wild
        if s['fh']:
            mcell = mcell[:, ::-1]; mwild = mwild[:, ::-1]
        if s['fv']:
            mcell = mcell[::-1, :]; mwild = mwild[::-1, :]
        if int((~mwild).sum()) == 0:
            stats['skipped'] += 1   # fully covered by higher-priority sprites
            continue
        bgc_tries = []
        for yrad in (8, 16, 32):
            bs = bg_colors_near(frame, s['x'], s['y'], yrad=yrad, bgm=bgm)
            if bs and bs not in bgc_tries:
                bgc_tries.append(bs)
        if global_bgc and global_bgc not in bgc_tries:
            bgc_tries.append(global_bgc)
        m = None
        prefer = PREFER.get((7, s['tile']))  # sprite pattern bank = 7
        for bgc in bgc_tries:
            m = match_sprite_cell(mcell, bgc, mwild, prefer_idx=prefer)
            if m:
                break
        if m is None:
            m = match_sprite_cell(mcell, set(), mwild, prefer_idx=prefer)
        if m is None:
            stats['failed'] += 1
            # raw paste with colorkey using the widest available bg set
            bgc = bgc_tries[-1] if bgc_tries else set()
            rgb, vis = cell.copy(), ~wild
            for r in range(8):
                for c in range(8):
                    px = (int(cell[r,c,0]), int(cell[r,c,1]), int(cell[r,c,2]))
                    if px in bgc:
                        vis[r, c] = False
        else:
            b, t, c2i, tile_idx = m
            stats['matched'] += 1
            stats['banks'].add(b)
            rgb, vis = render_tile(tile_idx, c2i, s['fh'], s['fv'])
            # full render (ignoring higher-prio masks): what this sprite would
            # show if every sprite above it were transparent — needed for the
            # fall-through test of sprites drawn ON TOP of this one later
            renders[s['idx']] = (rgb, vis.copy())
            vis &= ~wild
        oy, ox = s['y'] - ys0, s['x'] - xs0
        # paste where visible and not already covered by higher priority
        for r in range(8):
            for c in range(8):
                if vis[r, c]:
                    canvas[oy+r, ox+c] = rgb[r, c]
                    canvas_vis[oy+r, ox+c] = True
    return (canvas, canvas_vis, (xs0, ys0)), stats

def save_rgba(path, rgb, vis):
    h, w, _ = rgb.shape
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[..., :3] = rgb
    arr[..., 3] = np.where(vis, 255, 0)
    Image.fromarray(arr, 'RGBA').save(path)

def make_strip(frames, path, scale=3, pad=2):
    """frames: list of (rgb,vis); horizontal strip on checker bg for preview"""
    h = max(f[0].shape[0] for f in frames)
    w = sum(f[0].shape[1] for f in frames) + pad * (len(frames) - 1)
    strip = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    x = 0
    for rgb, vis in frames:
        arr = np.zeros((rgb.shape[0], rgb.shape[1], 4), dtype=np.uint8)
        arr[..., :3] = rgb; arr[..., 3] = np.where(vis, 255, 0)
        strip.paste(Image.fromarray(arr, 'RGBA'), (x, 0))
        x += rgb.shape[1] + pad
    strip = strip.resize((strip.width * scale, strip.height * scale), Image.NEAREST)
    # checkerboard backdrop
    bg = Image.new('RGB', strip.size, (40, 40, 40))
    for yy in range(0, strip.height, 16):
        for xx in range(0, strip.width, 16):
            if (xx // 16 + yy // 16) % 2 == 0:
                for dy in range(16):
                    for dx in range(16):
                        if xx+dx < strip.width and yy+dy < strip.height:
                            bg.putpixel((xx+dx, yy+dy), (56, 56, 56))
    bg.paste(strip, (0, 0), strip)
    bg.save(path)

if __name__ == '__main__':
    groups = {
        'idle': [(f'tools/out/anim/a{f}.ppm', f'tools/out/anim/pa{f}.bin')
                 for f in (4260, 4276, 4292)],
        'walk': [(f'tools/out/wj/w{f}.ppm', f'tools/out/wj/w{f}.bin')
                 for f in range(4330, 4430, 2)],
        'jump': [(f'tools/out/wj/j{f}.ppm', f'tools/out/wj/j{f}.bin')
                 for f in range(4470, 4570, 2)],
        'crouch': [(f'tools/out/crouch/c{f}.ppm', f'tools/out/crouch/c{f}.bin')
                   for f in list(range(4324, 4362, 2)) + list(range(4364, 4404, 4))],
        'cwalk': [(f'tools/out/crouch/q{f}.ppm', f'tools/out/crouch/q{f}.bin')
                  for f in range(4416, 4468, 4)],
    }
    os.makedirs('extracted/sprites/frames', exist_ok=True)
    results = {}
    for gname, flist in groups.items():
        frames_rgb = []      # (rgb, vis, failed)
        for shot, ram in flist:
            f = int(''.join(c for c in os.path.basename(shot) if c.isdigit()))
            if not (os.path.exists(shot) and os.path.exists(ram)):
                continue
            res, stats = extract_frame(shot, ram)
            if res is None:
                print(f'{gname} f{f}: {stats}')
                continue
            rgb, vis, org = res
            frames_rgb.append((rgb, vis, stats['failed']))
            save_rgba(f'extracted/sprites/frames/f{f}.png', rgb, vis)
            results[f] = stats
            print(f'{gname} f{f}: bbox_origin={org} sprites={stats["total"]} '
                  f'matched={stats["matched"]} failed={stats["failed"]} skipped={stats.get("skipped",0)} '
                  f'banks={sorted(stats["banks"])}')
        if frames_rgb:
            # GMS poses: only frames where EVERY sprite cell was an exact CHR hit
            poses, seen = [], set()
            for rgb, vis, nfail in frames_rgb:
                if nfail > 0:
                    continue
                key = (rgb.tobytes(), vis.tobytes())
                if key in seen:
                    continue
                seen.add(key)
                poses.append((rgb, vis))
            # uniform canvas per group: horizontal center + bottom align
            # (GMS requires all frames of one sprite to share the size)
            if poses:
                W = max(p[0].shape[1] for p in poses)
                H = max(p[0].shape[0] for p in poses)
            for i, (rgb, vis) in enumerate(poses):
                h, w = rgb.shape[:2]
                if (h, w) != (H, W):
                    pr = np.zeros((H, W, 3), np.uint8)
                    pv = np.zeros((H, W), dtype=bool)
                    ox0, oy0 = (W - w) // 2, H - h
                    pr[oy0:oy0+h, ox0:ox0+w] = rgb
                    pv[oy0:oy0+h, ox0:ox0+w] = vis
                    rgb, vis = pr, pv
                save_rgba(f'extracted/sprites/chip_{gname}_{i}.png', rgb, vis)
            uniq = [(r, v) for r, v, _ in frames_rgb]
            seen2, uniq2 = set(), []
            for rgb, vis in uniq:
                key = (rgb.tobytes(), vis.tobytes())
                if key not in seen2:
                    seen2.add(key); uniq2.append((rgb, vis))
            make_strip(uniq2, f'extracted/sprites/strip_{gname}.png')
            print(f'{gname}: {len(frames_rgb)} frames, {len(uniq2)} unique, '
                  f'{len(poses)} exact poses -> chip_{gname}_*.png')
    tot_m = sum(s['matched'] for s in results.values())
    tot_f = sum(s['failed'] for s in results.values())
    print(f'\nTOTAL sprite cells matched={tot_m} failed={tot_f} '
          f'({100*tot_m/max(tot_m+tot_f,1):.1f}% exact CHR hits)')
