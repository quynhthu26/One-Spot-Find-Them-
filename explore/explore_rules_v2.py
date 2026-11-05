#!/usr/bin/env python3
"""Read-only: apply the proposed home rules (21-07 night, anchor nights, >=12 nights, >=8 home nights)."""
import csv, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

root = Path(sys.argv[1]).expanduser()
data = root / "Data" if (root / "Data").is_dir() else root
BJ = timedelta(hours=8)
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
    anchor = Counter()
    silent = 0
    for ps in nights.values():
        ps.sort()
        ev = [c for t, c in ps if t.hour >= 21 or t.hour < 3]
        mo = [c for t, c in ps if 3 <= t.hour < 7]
        silent += not any(t.hour < 5 for t, c in ps)
        for c in {ev[-1] if ev else None, mo[0] if mo else None} - {None}:
            anchor[c] += 1
    r = {"user_id": udir.name, "nights": len(nights), "silent_00_05_nights": silent,
         "home_lat": "", "home_lon": "", "home_nights": 0, "second_nights": 0, "home_share": "", "is_home": "no"}
    if anchor:
        ranked = anchor.most_common()
        (c, n) = ranked[0]
        r.update(home_lat=c[0], home_lon=c[1], home_nights=n,
                 second_nights=ranked[1][1] if len(ranked) > 1 else 0,
                 home_share=round(n / len(nights), 3))
        if len(nights) >= 12 and n >= 8:
            r["is_home"] = "yes"
    rows.append(r)
with open("geolife_rules_v2.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print("users", len(rows), "home yes", sum(r["is_home"] == "yes" for r in rows))
