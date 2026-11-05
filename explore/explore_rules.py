#!/usr/bin/env python3
"""Read-only exploration of GeoLife 1.3 to judge the One Spot rules. Writes nothing to the dataset."""
import csv, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

root = Path(sys.argv[1]).expanduser()
prefix = sys.argv[2]
data = root / "Data" if (root / "Data").is_dir() else root
BJ = timedelta(hours=8)

def n2206(t): return t.hour >= 22 or t.hour < 6
def n0006(t): return t.hour < 6
def wk0917(t): return t.weekday() < 5 and 9 <= t.hour < 17
WINDOWS = {"n2206": (n2206, lambda t: (t - timedelta(hours=6)).date()),
           "n0006": (n0006, lambda t: t.date()),
           "w0917": (wk0917, lambda t: t.date())}
SIZES = {"c01": 2, "c005": None}

def cell(lat, lon, size):
    if size == "c01":
        return (round(lat, 2), round(lon, 2))
    return (round(lat * 200) / 200, round(lon * 200) / 200)

hours = Counter()
rows = []
for udir in sorted(p for p in data.iterdir() if p.is_dir()):
    pts = Counter()
    days = defaultdict(set)
    alldays = defaultdict(set)
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
                hours[t.hour] += 1
                for w, (test, key) in WINDOWS.items():
                    if test(t):
                        k = key(t)
                        alldays[w].add(k)
                        for s in SIZES:
                            c = cell(lat, lon, s)
                            pts[(w, s, c)] += 1
                            days[(w, s, c)].add(k)
    r = {"user_id": udir.name}
    for w in WINDOWS:
        for s in SIZES:
            tag = f"{w}_{s}"
            cells = {k[2]: v for k, v in pts.items() if k[0] == w and k[1] == s}
            total = sum(cells.values())
            r[f"{tag}_pts"] = total
            r[f"{tag}_days"] = len(alldays[w])
            if not cells:
                for x in ("top_lat", "top_lon", "top_pts", "top_days", "second_pts", "ntie", "topdays_lat", "topdays_lon", "topdays_days"):
                    r[f"{tag}_{x}"] = ""
                continue
            ranked = sorted(cells.items(), key=lambda kv: -kv[1])
            (tc, tp) = ranked[0]
            r[f"{tag}_top_lat"], r[f"{tag}_top_lon"] = tc
            r[f"{tag}_top_pts"] = tp
            r[f"{tag}_top_days"] = len(days[(w, s, tc)])
            r[f"{tag}_second_pts"] = ranked[1][1] if len(ranked) > 1 else 0
            r[f"{tag}_ntie"] = sum(1 for _, v in ranked if v == tp)
            dc = max(cells, key=lambda c: (len(days[(w, s, c)]), cells[c]))
            r[f"{tag}_topdays_lat"], r[f"{tag}_topdays_lon"] = dc
            r[f"{tag}_topdays_days"] = len(days[(w, s, dc)])
    rows.append(r)
    print(udir.name, flush=True, end=" ")

with open(f"{prefix}_users.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
with open(f"{prefix}_hours.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["hour_beijing", "points"])
    for h in range(24):
        w.writerow([h, hours[h]])
print("\nusers", len(rows), "points", sum(hours.values()))
