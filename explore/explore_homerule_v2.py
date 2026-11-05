#!/usr/bin/env python3
"""Read-only: home cell by "home nights" (evening end or morning start). Writes nothing to the dataset."""
import csv, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

root = Path(sys.argv[1]).expanduser()
out = sys.argv[2] if len(sys.argv) > 2 else "geolife_homerule_v2.csv"
data = root / "Data" if (root / "Data").is_dir() else root
BJ = timedelta(hours=8)
COLS = ["user_id", "nights", "home_lat", "home_lon", "home_nights", "home_end_nights", "home_start_nights",
        "runner_up_home_nights", "n_tie", "home_pts"]

rows = []
for udir in sorted(p for p in data.iterdir() if p.is_dir()):
    nights = defaultdict(list)
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
                if t.hour >= 21 or t.hour < 7:
                    nights[(t - timedelta(hours=7)).date()].append((t, (round(lat, 2), round(lon, 2))))

    pts = Counter()
    home, end, start = Counter(), Counter(), Counter()
    for ps in nights.values():
        ps.sort()
        ev = [c for t, c in ps if t.hour >= 21 or t.hour < 3]
        mo = [c for t, c in ps if 3 <= t.hour < 7]
        e = ev[-1] if ev else None
        s = mo[0] if mo else None
        for t, c in ps:
            pts[c] += 1
        if e: end[e] += 1
        if s: start[s] += 1
        for c in {e, s} - {None}:
            home[c] += 1

    r = dict.fromkeys(COLS, "")
    r.update(user_id=udir.name, nights=len(nights))
    if home:
        ranked = sorted(home, key=lambda c: (home[c], pts[c]), reverse=True)
        hc = ranked[0]
        r.update(home_lat=hc[0], home_lon=hc[1], home_nights=home[hc], home_end_nights=end[hc],
                 home_start_nights=start[hc],
                 runner_up_home_nights=home[ranked[1]] if len(ranked) > 1 else 0,
                 n_tie=sum(1 for c in ranked if home[c] == home[hc]), home_pts=pts[hc])
    rows.append(r)
    print(udir.name, flush=True, end=" ")

with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS)
    w.writeheader(); w.writerows(rows)
print("\nusers", len(rows))
