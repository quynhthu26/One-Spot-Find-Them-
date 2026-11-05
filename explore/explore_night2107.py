#!/usr/bin/env python3
"""Read-only: night 21:00-07:00 Beijing, 1 km cells, per-user top cells. Writes nothing to the dataset."""
import csv, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

root = Path(sys.argv[1]).expanduser()
out = sys.argv[2] if len(sys.argv) > 2 else "geolife_night2107.csv"
data = root / "Data" if (root / "Data").is_dir() else root
BJ = timedelta(hours=8)
COLS = ["user_id", "night_pts", "nights", "top_lat", "top_lon", "top_pts", "top_nights",
        "bn_lat", "bn_lon", "bn_nights", "bn_pts", "second_nights", "n_tie_nights"]

rows = []
all_pts = 0
for udir in sorted(p for p in data.iterdir() if p.is_dir()):
    pts = Counter()
    cn = defaultdict(set)
    nights = set()
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
                all_pts += 1
                if t.hour >= 21 or t.hour < 7:
                    k = (t - timedelta(hours=7)).date()
                    c = (round(lat, 2), round(lon, 2))
                    pts[c] += 1
                    cn[c].add(k)
                    nights.add(k)
    r = dict.fromkeys(COLS, "")
    r.update(user_id=udir.name, night_pts=sum(pts.values()), nights=len(nights))
    if pts:
        tc = max(pts, key=lambda c: pts[c])
        r.update(top_lat=tc[0], top_lon=tc[1], top_pts=pts[tc], top_nights=len(cn[tc]))
        bc = max(pts, key=lambda c: (len(cn[c]), pts[c]))
        r.update(bn_lat=bc[0], bn_lon=bc[1], bn_nights=len(cn[bc]), bn_pts=pts[bc])
        counts = sorted((len(s) for s in cn.values()), reverse=True)
        r["second_nights"] = counts[1] if len(counts) > 1 else 0
        r["n_tie_nights"] = counts.count(counts[0])
    rows.append(r)
    print(udir.name, flush=True, end=" ")

with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS)
    w.writeheader(); w.writerows(rows)
print("\nusers", len(rows), "points", all_pts, "night_points", sum(r["night_pts"] for r in rows))
