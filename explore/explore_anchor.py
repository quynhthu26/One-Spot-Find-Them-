#!/usr/bin/env python3
"""Read-only: per-night anchor signals (where the evening ends, the morning starts) for the most-nights cell."""
import csv, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

root = Path(sys.argv[1]).expanduser()
out = sys.argv[2] if len(sys.argv) > 2 else "geolife_anchor.csv"
data = root / "Data" if (root / "Data").is_dir() else root
BJ = timedelta(hours=8)
COLS = ["user_id", "nights", "bn_lat", "bn_lon", "bn_nights", "bn_end_nights", "bn_start_nights",
        "bn_anchor_nights", "bn_deep_nights", "bn_30min_nights", "bn_short_only_nights",
        "end_lat", "end_lon", "end_nights", "nights_with_end"]

def evening(t): return t.hour >= 21 or t.hour < 3

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
    cn = defaultdict(set)
    per_night = {}
    for k, ps in nights.items():
        ps.sort()
        ev = [c for t, c in ps if evening(t)]
        mo = [c for t, c in ps if 3 <= t.hour < 7]
        first, last = {}, {}
        for t, c in ps:
            pts[c] += 1
            cn[c].add(k)
            first.setdefault(c, t)
            last[c] = t
        per_night[k] = dict(end=ev[-1] if ev else None, start=mo[0] if mo else None,
                            deep={c for t, c in ps if t.hour < 5},
                            first=first, last=last, final=ps[-1][0], cells_after=ps)

    r = dict.fromkeys(COLS, "")
    r.update(user_id=udir.name, nights=len(nights))
    ends = Counter(n["end"] for n in per_night.values() if n["end"])
    r["nights_with_end"] = sum(ends.values())
    if pts:
        bn = max(pts, key=lambda c: (len(cn[c]), pts[c]))
        e = s = a = d = m30 = short = 0
        for n in per_night.values():
            ie, is_ = n["end"] == bn, n["start"] == bn
            e += ie; s += is_; a += ie or is_
            d += bn in n["deep"]
            if bn in n["first"]:
                mins = (n["last"][bn] - n["first"][bn]).total_seconds() / 60
                m30 += mins >= 30
                left = any(t > n["last"][bn] and c != bn for t, c in n["cells_after"])
                short += mins < 120 and left
        r.update(bn_lat=bn[0], bn_lon=bn[1], bn_nights=len(cn[bn]), bn_end_nights=e,
                 bn_start_nights=s, bn_anchor_nights=a, bn_deep_nights=d,
                 bn_30min_nights=m30, bn_short_only_nights=short)
    if ends:
        ec, en = max(ends.items(), key=lambda kv: (kv[1], pts[kv[0]]))
        r.update(end_lat=ec[0], end_lon=ec[1], end_nights=en)
    rows.append(r)
    print(udir.name, flush=True, end=" ")

with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS)
    w.writeheader(); w.writerows(rows)
print("\nusers", len(rows))
