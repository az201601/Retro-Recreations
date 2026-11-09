#!/usr/bin/env python3
"""Sanity check the generated GMS 1.4 project: XML parses, referenced PNG/WAV exist."""
import glob, os, sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P    = os.path.join(ROOT,'ChipNRangers2.project')
errs = []
for f in glob.glob(os.path.join(P,'**','*.gmx'), recursive=True):
    try:
        ET.parse(f)
    except Exception as e:
        errs.append(f'{os.path.relpath(f,ROOT)}: {e}')

missing = []
for f in glob.glob(os.path.join(P,'**','*.gmx'), recursive=True):
    root = ET.parse(f).getroot()
    base = os.path.dirname(f)
    for tag in ('frame','data'):
        for n in root.iter(tag):
            name = (n.text or '').strip()
            if name and name.lower().endswith(('.png','.wav')):
                if not os.path.exists(os.path.join(base, name.replace('\\', os.sep))):
                    missing.append(os.path.join(os.path.relpath(base,ROOT), name))

print(f'.gmx files : {len(glob.glob(os.path.join(P,"**","*.gmx"), recursive=True))}')
print(f'XML errors : {errs or "none"}')
print(f'missing    : {missing or "none"}')
sys.exit(1 if (errs or missing) else 0)
