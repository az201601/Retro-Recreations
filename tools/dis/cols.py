#!/usr/bin/env python3
"""dis6502 output in columns (less scrolling):  cols.py BANK START END [COLUMNS]"""
import subprocess, sys, os
out = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dis6502.py')] + sys.argv[1:4], capture_output=True, text=True).stdout
L = [l.rstrip() for l in out.split('\n') if l.strip()]
L = [(l[:4] + ' ' + l[16:]).strip() if len(l) > 16 else l for l in L]
w = int(sys.argv[4]) if len(sys.argv) > 4 else 4; n = (len(L) + w - 1) // w
for i in range(n): print(' | '.join((L[i + j * n] if i + j * n < len(L) else '').ljust(22) for j in range(w)).rstrip())
