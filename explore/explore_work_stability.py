#!/usr/bin/env python3
"""Read-only: how many weekdays are needed before the work square is stable (versions A and B)."""
import random, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

root = Path(sys.argv[1]).expanduser()
data = root / "Data" if (root / "Data").is_dir() else root
BJ = timedelta(hours=8)
KS = [3, 5, 8, 10, 12, 15, 20]
VERS = {"A": (7, 12), "B": (8, 13)}

users = {v: {} for v in VERS}
for udir in sorted(p for p in data.iterdir() if p.is_dir()):
    days = defaultdict(list)
    for f in sorted((udir / "Trajectory").glob("*.plt")):
        with open(f, encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                if i < 6:
                    continue
                p = line.strip().split(",")
                if len(p) < 7:
                    continue
                try:
                    lat, lon = float(p[0]), float(p[1])
                    t = datetime.strptime(p[5] + " " + p[6], "%Y-%m-%d %H:%M:%S") + BJ
                except ValueError:
                    continue
                if t.weekday() < 5 and 7 <= t.hour < 19:
                    days[t.date()].append((t, (round(lat, 2), round(lon, 2))))
    for v, (start, split) in VERS.items():
        recs = []
        for ps in days.values():
            ps.sort()
            win = [tc for tc in ps if start <= tc[0].hour < 19]
            if not win:
                continue
            mo = [c for t, c in win if t.hour < split]
            af = [c for t, c in win if t.hour >= split]
            marks = {mo[-1] if mo else None, af[0] if af else None} - {None}
            recs.append((marks, Counter(c for t, c in win)))
        users[v][udir.name] = recs

def work_cell(recs):
    work, pts = Counter(), Counter()
    for marks, p in recs:
        work.update(marks); pts.update(p)
    if not work:
        return None, 0
    c = max(work, key=lambda c: (work[c], pts[c]))
    return c, work[c]

for v in VERS:
    random.seed(1)
    ref = {}
    for u, recs in users[v].items():
        if len(recs) >= 30:
            c, n = work_cell(recs)
            if c and n * 2 >= len(recs):
                ref[u] = c
    print(f"Version {v}: reference users {len(ref)}")
    byh = defaultdict(lambda: [0, 0])
    print("k,match_rate")
    for k in KS:
        rates = []
        for u, c in ref.items():
            hits = 0
            for _ in range(200):
                s = random.sample(users[v][u], k)
                g, _n = work_cell(s)
                h = sum(1 for marks, _p in s if c in marks)
                b = byh[min(h, 12) if h in (1, 3, 5, 8) or h >= 12 else None]
                b[0] += 1; b[1] += g == c
                hits += g == c
            rates.append(hits / 200)
        print(f"{k},{sum(rates) / len(rates):.3f}")
    print("h,samples,match_rate")
    for h in (1, 3, 5, 8, 12):
        d, m = byh[h]
        print(f"{h if h < 12 else '12+'},{d},{m / d:.3f}" if d else f"{h},0,")
