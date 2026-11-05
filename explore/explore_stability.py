#!/usr/bin/env python3
"""Read-only: how many nights are needed before the evening-end cell is stable? Writes nothing to the dataset."""
import csv, random, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

root = Path(sys.argv[1]).expanduser()
data = root / "Data" if (root / "Data").is_dir() else root
BJ = timedelta(hours=8)
KS = [2, 3, 4, 5, 6, 8, 10, 12, 15, 20]
DRAWS = 50
random.seed(1)

def end_cells(udir):
    last = {}
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
                if t.hour >= 21 or t.hour < 3:
                    k = (t - timedelta(hours=7)).date()
                    if k not in last or t >= last[k][0]:
                        last[k] = (t, (round(lat, 2), round(lon, 2)))
    return [c for _, (t, c) in sorted(last.items())]

def mode(cells):
    cnt = Counter(cells)
    top = max(cnt.values())
    return random.choice(sorted(c for c, n in cnt.items() if n == top)), top

users = {}
for udir in sorted(p for p in data.iterdir() if p.is_dir()):
    e = end_cells(udir)
    if len(e) >= 20:
        users[udir.name] = e

by_k = []
by_h = defaultdict(lambda: [0, 0])
for k in KS:
    rates = []
    for u, e in users.items():
        full = Counter(e).most_common(1)[0][0]
        hits = 0
        for _ in range(DRAWS):
            home, h = mode(random.sample(e, k))
            m = home == full
            hits += m
            b = by_h[min(h, 15)]
            b[0] += 1; b[1] += m
        rates.append(hits / DRAWS)
    by_k.append([k, len(users), round(sum(rates) / len(rates), 3)])

with open("stability_by_k.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["k", "users", "mean_match_rate"]); w.writerows(by_k)
with open("stability_by_h.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["h", "draws", "match_rate"])
    for h in sorted(by_h):
        d, m = by_h[h]
        w.writerow([h, d, round(m / d, 3)])
print("users", len(users))
