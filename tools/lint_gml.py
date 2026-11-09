#!/usr/bin/env python3
"""Check that every sprite/object/sound/room/script identifier used in GML exists."""
import glob, os, re, xml.etree.ElementTree as ET
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'ChipNRangers2.project')

known = set()
for f in glob.glob(os.path.join(P,'sprites','*.sprite.gmx')):
    known.add(os.path.basename(f).split('.')[0])
for f in glob.glob(os.path.join(P,'background','*.background.gmx')):
    known.add(os.path.basename(f).split('.')[0])
for f in glob.glob(os.path.join(P,'sound','*.sound.gmx')):
    known.add(os.path.basename(f).split('.')[0])
for f in glob.glob(os.path.join(P,'objects','*.object.gmx')):
    known.add(os.path.basename(f).split('.')[0])
for f in glob.glob(os.path.join(P,'rooms','*.room.gmx')):
    known.add(os.path.basename(f).split('.')[0])
for f in glob.glob(os.path.join(P,'scripts','*.gml')):
    known.add(os.path.basename(f)[:-4])

pat = re.compile(r'\b((?:spr|obj|snd|rm|bgm)[A-Za-z0-9_]+)\b')
bad = set()
files = glob.glob(os.path.join(P,'objects','*.object.gmx')) + glob.glob(os.path.join(P,'scripts','*.gml'))
for f in files:
    if f.endswith('.gml'):
        texts = [open(f, encoding='utf-8').read()]
    else:
        r = ET.parse(f).getroot()
        texts = [s.text or '' for s in r.iter('string')]
        texts += [c.text or '' for c in r.findall('.//codestring')]
    for t in texts:
        for ident in pat.findall(t):
            if ident in ('sprite_index','sprite_width','sprite_height','sprite_get_width'):
                continue
            if ident not in known:
                bad.add((os.path.basename(f), ident))
print('resources known:', len(known))
print('unknown identifiers:', sorted(bad) or 'none')
