#!/usr/bin/env python3
"""Read-only: weekday work cell by "work days" (morning end OR afternoon start), plus a variant excluding home."""
import csv, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

root = Path(sys.argv[1]).expanduser()
out = sys.argv[2] if len(sys.argv) > 2 else "geolife_work_v2.csv"
data = root / "Data" if (root / "Data").is_dir() else root
BJ = timedelta(hours=8)
COLS = ["user_id", "weekdays", "work_lat", "work_lon", "work_days", "work_morning_end_days",
        "work_afternoon_start_days", "work_and_days", "work_share", "runner_up_days", "work_same_as_home",
        "nh_work_lat", "nh_work_lon", "nh_work_days", "nh_work_share"]

home = {}
for r in csv.DictReader(open("geolife_homerule_v4.csv")):
    if r["is_home"] == "yes":
        home[r["user_id"]] = (float(r["home_lat"]), float(r["home_lon"]))

rows = []
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

    pts = Counter()
    work, mend, astart, both = Counter(), Counter(), Counter(), Counter()
    for ps in days.values():
        ps.sort()
        mo = [c for t, c in ps if t.hour < 12]
        af = [c for t, c in ps if t.hour >= 12]
        m = mo[-1] if mo else None
        a = af[0] if af else None
        for t, c in ps:
            pts[c] += 1
        if m: mend[m] += 1
        if a: astart[a] += 1
        if m and m == a: both[m] += 1
        for c in {m, a} - {None}:
            work[c] += 1

    r = dict.fromkeys(COLS, "")
    r.update(user_id=udir.name, weekdays=len(days))
    if work:
        ranked = sorted(work, key=lambda c: (work[c], pts[c]), reverse=True)
        wc = ranked[0]
        r.update(work_lat=wc[0], work_lon=wc[1], work_days=work[wc], work_morning_end_days=mend[wc],
                 work_afternoon_start_days=astart[wc], work_and_days=both[wc],
                 work_share=round(work[wc] / len(days), 3),
                 runner_up_days=work[ranked[1]] if len(ranked) > 1 else 0)
        h = home.get(udir.name)
        if h:
            r["work_same_as_home"] = "yes" if h == wc else "no"
        nh = [c for c in ranked if c != h]
        if nh:
            c = nh[0]
            r.update(nh_work_lat=c[0], nh_work_lon=c[1], nh_work_days=work[c],
                     nh_work_share=round(work[c] / len(days), 3))
    rows.append(r)
    print(udir.name, flush=True, end=" ")

with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS)
    w.writeheader(); w.writerows(rows)
print("\nusers", len(rows), "home users", len(home))
