#!/usr/bin/env python3
"""Step 16: the third section's crates and bonus boxes.
  work/s3_boxes.pkl        cells: (column, row, kind, donor column, donor row); kind 1 crate, 2 crate with a bonus box
                           inside, 3 bonus box.  The donor is a block of the section's picture that looks like what the
                           game puts where the box was.  box: a bonus box in the picture
  work/s3_box_tables.gml   the same as GML text (pasted into obj_stage1 Create)
What is behind a box comes from the ROM: the section's seven screens are also stored without the boxes.  The screen
list is at bank 3 $9E92 (screen pointers at bank 0 $8000 / $8100); each entry is checked against the map of the
recordings.
Needs build_sec3.py and the capture_sec3.py recordings."""
import os, pickle
import numpy as np
from emu import WORK
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROM = open(os.path.join(ROOT, "Chip 'n Dale - Rescue Rangers 2 (USA).nes"), 'rb').read()[16:]
BOX = {0xF4: 1, 0xF5: 2, 0xF9: 3}                       # no crate with the item in the third section

def rd(bank, a): return ROM[bank * 0x4000 + (a - 0x8000)]
def screen(s):
    lo = rd(0, 0x8000 + s); hi = rd(0, 0x8100 + s); b = hi >> 6; a = ((hi & 0x3F) | 0x80) << 8 | lo
    if b * 0x4000 + a - 0x8000 + 240 > len(ROM): return None
    return np.array([rd(b, a + i) for i in range(240)]).reshape(15, 16)

def boxes():
    S3B = pickle.load(open(os.path.join(WORK, 's3_blocks.pkl'), 'rb')); raw = np.array(S3B['raw']).astype(int)   # 15 x 112
    M = pickle.load(open(os.path.join(WORK, 's3_map.pkl'), 'rb'))
    look = lambda c, r: (M['pix'][r * 16:r * 16 + 16, c * 16:c * 16 + 16].tobytes(), M['grp'][r * 16:r * 16 + 16, c * 16:c * 16 + 16].tobytes())
    listed = [rd(3, 0x9E92 + i) - 1 for i in range(7)]  # the section's screen list (bank 3 $9E92)
    sc = {s: screen(s) for s in range(160)}; behind = np.full((15, 128), -1)
    for k, sx in enumerate(range(0, 112, 16)):
        m = raw[:, sx:sx + 16]
        d, s = min((int(((q != m) & ~np.isin(m, list(BOX))).sum()), s) for s, q in sc.items() if q is not None)
        assert d == 0, (sx, s, d)
        assert s == listed[k], (k, s, listed[k])         # (the same screens the list names)
        behind[:, sx:sx + 16] = sc[s]
    donors = {}
    for r in range(15):
        for c in range(112):
            v = int(raw[r, c])
            if v < 0 or v in BOX: continue
            if v not in donors: donors[v] = (c, r)
            elif look(c, r) != look(*donors[v]): print('block %02X does not look the same everywhere' % v, (c, r), donors[v])
    cells = []
    for r in range(15):
        for c in range(112):
            v = int(raw[r, c])
            if v in BOX:
                u = int(behind[r, c]); assert u in donors, (c, r, hex(u)); cells.append((c, r, BOX[v], donors[u][0], donors[u][1]))
    box = next((c, r) for r in range(15) for c in range(112) if raw[r, c] == 0xF9)
    return cells, box

if __name__ == '__main__':
    cells, box = boxes()
    print('%d crates, %d crates with a bonus box, %d bonus boxes' % tuple(sum(1 for q in cells if q[2] == k) for k in (1, 2, 3)))
    pickle.dump(dict(cells=cells, box=box), open(os.path.join(WORK, 's3_boxes.pkl'), 'wb'))
    g = ['// the third section\'s crates and bonus boxes: column, row (0-14), kind (1 crate, 2 crate with a bonus box inside,',
         '// 3 bonus box), and the column / row of a block of the section\'s picture that looks like what is behind it']
    g.append('lv_box3_n = %d;' % len(cells))
    for i, q in enumerate(cells): g.append('lv_bc3[%d] = %d; lv_br3[%d] = %d; lv_bk3[%d] = %d; lv_bdc3[%d] = %d; lv_bdr3[%d] = %d;' % (i, q[0], i, q[1], i, q[2], i, q[3], i, q[4]))
    g.append('lv_rbox3_c = %d; lv_rbox3_r = %d;    // a bonus box in the picture (shown where a crate had one inside)' % box)
    open(os.path.join(WORK, 's3_box_tables.gml'), 'w').write('\n'.join(g) + '\n')
