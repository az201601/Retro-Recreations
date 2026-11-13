#!/usr/bin/env python3
"""Deliverable 4: pack the cutscene model into the plain tables that the GML code uses (work/news_data.pkl).
sim_news.py runs on exactly these tables; gen_news_gml.py writes them into the Create event."""
import os, pickle
from emu import WORK
from news_model import ACTORS, T0, CLEAR_AT

def pack():
    M = pickle.load(open(os.path.join(WORK, 'news_model.pkl'), 'rb'))
    G = pickle.load(open(os.path.join(WORK, 'news_gfx.pkl'), 'rb'))
    A = pickle.load(open(os.path.join(WORK, 'news_audio.pkl'), 'rb'))
    keys = G['keys']; tiles = G['tiles']
    def cel(o):                                   # 0 = not shown, else cel number + 1
        k = (o[0], o[1], o[2], o[5])
        assert o[5] != 1 or k in keys, o
        return keys.index(k) + 1 if o[5] == 1 else 0
    D = dict(cels=G['cels'], ncel=len(keys), nglyph=len(tiles), notes=A['notes'], loop=A['loop'], m0=A['m0'], clear_at=CLEAR_AT)
    D['pages'] = [dict(pre=M['pre'][k], speaker=p['speaker'], voice=A['page_voice'][k],
                       ticks=[(kd, r, c, tiles.index(t) + 1 if kd == 0 else 0, tiles.index(b) + 1 if kd == 0 and b >= 0 else 0) for kd, r, c, t, b in p['ticks']])
                  for k, p in enumerate(M['pages'])]
    opn = [0] * (len(keys) + 1)                   # cel + 1 -> cel + 1 with the mouth open
    for p in M['pages']:
        for c, o in p['open'].items(): opn[keys.index(c + (1,)) + 1] = keys.index(o + (1,)) + 1
    D['open'] = opn
    trk = []; segs = []
    for ai, a in enumerate(M['actors']):
        for sg in a['segs']:
            segs.append(dict(actor=ai, gap=sg['gap'], off=sg['off'], p0=len(trk), n=len(sg['track'])))
            trk += [(cel(o), o[3], o[4]) for o in sg['track']]
    b = M['ball']
    D['ball'] = dict(actor=b['actor'], hover=b['hover'], hy=b['hy'], x=b['x'], cel=keys.index((23, 0, 0, 1)) + 1, cel2=keys.index((52, 0, 0, 1)) + 1,
                     rel_gap=b['release'][0], rel_off=b['release'][1], p0=len(trk), n=len(b['leave']))
    assert keys.index((24, 0, 0, 1)) == keys.index((23, 0, 0, 1)) + 1 and keys.index((53, 0, 0, 1)) == keys.index((52, 0, 0, 1)) + 1
    trk += [(cel(o), o[3], o[4] + 128) for o in b['leave']]              # y relative to where the hover stopped, + 128
    D['spin'] = M['spin']; D['segs'] = segs; D['trk'] = trk; D['names'] = [a[0] for a in ACTORS]
    pickle.dump(D, open(os.path.join(WORK, 'news_data.pkl'), 'wb'))
    return D
if __name__ == '__main__':
    D = pack()
    print('pages %d, ticks %d, cels %d, track segments %d, track frames %d, note starts %d' % (
        len(D['pages']), sum(len(p['ticks']) for p in D['pages']), D['ncel'], len(D['segs']), len(D['trk']), len(D['notes'])))
