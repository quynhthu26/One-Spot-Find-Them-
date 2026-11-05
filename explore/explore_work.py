#!/usr/bin/env python3
"""Read-only: weekday daytime work cell per user, two windows, stay-day rules. Writes nothing to the dataset."""
import csv, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

root = Path(sys.argv[1]).expanduser()
out = sys.argv[2] if len(sys.argv) > 2 else "geolife_work.csv"
data = root / "Data" if (root / "Data").is_dir() else root
BJ = timedelta(hours=8)
WINDOWS = {"w1": (9, 17), "w2": (10, 16)}
STAYS = {"stay": 120, "stay60": 60}

home = {}
for r in csv.DictReader(open("geolife_homerule_v2.csv")):
    if r["home_nights"] and int(r["nights"]) >= 12 and int(r["home_nights"]) * 2 >= int(r["nights"]):
        home[r["user_id"]] = (float(r["home_lat"]), float(r["home_lon"]))

def best(counter, pts):
    ranked = sorted(counter, key=lambda c: (counter[c], pts[c]), reverse=True)
    return ranked

rows = []
for udir in sorted(p for p in data.iterdir() if p.is_dir()):
    # per window: day -> cell -> [first, last], and point counts per cell
    span = {w: defaultdict(dict) for w in WINDOWS}
    pts = {w: Counter() for w in WINDOWS}
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
                if t.weekday() >= 5:
                    continue
                c = (round(lat, 2), round(lon, 2))
                for w, (a, b) in WINDOWS.items():
                    if a <= t.hour < b:
                        d = span[w][t.date()]
                        if c in d:
                            d[c][0] = min(d[c][0], t); d[c][1] = max(d[c][1], t)
                        else:
                            d[c] = [t, t]
                        pts[w][c] += 1

    r = {"user_id": udir.name}
    for w in WINDOWS:
        days = span[w]
        any_days = Counter(c for d in days.values() for c in d)
        r[f"{w}_days"] = len(days)
        for x in ("any_lat", "any_lon", "any_days"):
            r[f"{w}_{x}"] = ""
        if any_days:
            c = best(any_days, pts[w])[0]
            r.update({f"{w}_any_lat": c[0], f"{w}_any_lon": c[1], f"{w}_any_days": any_days[c]})
        for s, mins in STAYS.items():
            stay = Counter(c for d in days.values() for c, (a, b) in d.items()
                           if (b - a).total_seconds() >= mins * 60)
            for x in ("lat", "lon", "days", "share", "second"):
                r[f"{w}_{s}_{x}"] = ""
            r[f"{w}_{s}_same_as_home"] = ""
            if stay:
                ranked = best(stay, pts[w])
                c = ranked[0]
                r.update({f"{w}_{s}_lat": c[0], f"{w}_{s}_lon": c[1], f"{w}_{s}_days": stay[c],
                          f"{w}_{s}_share": round(stay[c] / len(days), 3),
                          f"{w}_{s}_second": stay[ranked[1]] if len(ranked) > 1 else 0})
                if udir.name in home:
                    r[f"{w}_{s}_same_as_home"] = "yes" if home[udir.name] == c else "no"
    rows.append(r)
    print(udir.name, flush=True, end=" ")

with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
print("\nusers", len(rows), "home users", len(home))
