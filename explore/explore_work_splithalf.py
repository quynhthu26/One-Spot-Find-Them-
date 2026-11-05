#!/usr/bin/env python3
"""Read-only: split-half work stability (version B: Mon-Fri 08-19, split 13, OR rule)."""
import random, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

root = Path(sys.argv[1]).expanduser()
data = root / "Data" if (root / "Data").is_dir() else root
BJ = timedelta(hours=8)
KS = [3, 5, 8, 10, 12]

users = {}
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
                if t.weekday() < 5 and 8 <= t.hour < 19:
                    days[t.date()].append((t, (round(lat, 2), round(lon, 2))))
    recs = []
    for d, ps in sorted(days.items()):
        ps.sort()
        mo = [c for t, c in ps if t.hour < 13]
        af = [c for t, c in ps if t.hour >= 13]
        recs.append(({mo[-1] if mo else None, af[0] if af else None} - {None}, Counter(c for t, c in ps)))
    users[udir.name] = recs

def work_cell(recs):
    work, pts = Counter(), Counter()
    for marks, p in recs:
        work.update(marks); pts.update(p)
    if not work:
        return None, 0
    c = max(work, key=lambda c: (work[c], pts[c]))
    return c, work[c]

passing = {u for u, r in users.items() if r and work_cell(r)[1] * 2 >= len(r)}

random.seed(1)
print("(1) random disjoint halves")
print("k,users,same_rate,users_passing_50,same_rate_passing_50")
for k in KS:
    rates = {}
    for u, recs in users.items():
        if len(recs) < 2 * k:
            continue
        same = 0
        for _ in range(200):
            s = random.sample(recs, 2 * k)
            a, _ = work_cell(s[:k]); b, _ = work_cell(s[k:])
            same += a is not None and a == b
        rates[u] = same / 200
    allr = list(rates.values()); pr = [v for u, v in rates.items() if u in passing]
    print(f"{k},{len(allr)},{sum(allr)/len(allr):.3f},{len(pr)},{sum(pr)/len(pr):.3f}")

print("(2) chronological halves, users with >= 24 weekdays")
same, diff = 0, []
for u, recs in users.items():
    if len(recs) < 24:
        continue
    h = len(recs) // 2
    a, _ = work_cell(recs[:h]); b, _ = work_cell(recs[h:])
    if a == b:
        same += 1
    else:
        diff.append((u, a, b, u in passing))
print(f"users={same + len(diff)} same={same} differ={len(diff)}")
for u, a, b, p in diff:
    print(f"{u}: first half {a} -> second half {b}{' (passes 50% on full data)' if p else ''}")
