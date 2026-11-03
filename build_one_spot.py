#!/usr/bin/env python3
import csv, math, sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

root = Path(sys.argv[1]).expanduser()
out = Path(sys.argv[2]).expanduser()
data = root / "Data" if (root / "Data").is_dir() else root
BJ = timedelta(hours=8)
BOX = (39.4, 41.1, 115.4, 117.5)

def cell(lat, lon):
    return (round(lat, 2), round(lon, 2))

rows, totals = [], Counter()
for udir in sorted(p for p in data.iterdir() if p.is_dir()):
    files = sorted((udir / "Trajectory").glob("*.plt"))
    n_pts, bad = 0, 0
    days, nights = set(), set()
    night_cells, day_cells = Counter(), Counter()
    for f in files:
        with open(f, encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh):
                if i < 6:
                    continue
                parts = line.strip().split(",")
                if len(parts) < 7:
                    bad += 1
                    continue
                try:
                    lat, lon = float(parts[0]), float(parts[1])
                    t = datetime.strptime(parts[5] + " " + parts[6], "%Y-%m-%d %H:%M:%S") + BJ
                except ValueError:
                    bad += 1
                    continue
                n_pts += 1
                days.add(t.date())
                c = cell(lat, lon)
                if t.hour >= 22 or t.hour < 6:
                    night_cells[c] += 1
                    nights.add((t - timedelta(hours=6)).date())
                if t.weekday() < 5 and 9 <= t.hour < 17:
                    day_cells[c] += 1
    totals["files"] += len(files); totals["points"] += n_pts; totals["bad_lines"] += bad

    def top(cnt):
        if not cnt:
            return None, None, None
        (la, lo), k = cnt.most_common(1)[0]
        return la, lo, round(k / sum(cnt.values()), 3)

    hla, hlo, hs = top(night_cells)
    wla, wlo, ws = top(day_cells)
    rows.append(dict(
        user_id=udir.name, n_trajectories=len(files), total_points=n_pts,
        first_day=min(days).isoformat() if days else "", last_day=max(days).isoformat() if days else "",
        active_days=len(days), nights_of_data=len(nights),
        home_lat=hla, home_lon=hlo, home_confidence_score=hs,
        work_lat=wla, work_lon=wlo, work_confidence_score=ws,
        has_mode_labels="yes" if (udir / "labels.txt").exists() else "no",
    ))

home_n = Counter((r["home_lat"], r["home_lon"]) for r in rows if r["home_lat"] is not None)
pair_n = Counter((r["home_lat"], r["home_lon"], r["work_lat"], r["work_lon"])
                 for r in rows if r["home_lat"] is not None and r["work_lat"] is not None)

def km(a, b, c, d):
    p = math.pi / 180
    h = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))

for r in rows:
    has_h, has_w = r["home_lat"] is not None, r["work_lat"] is not None
    hn = home_n[(r["home_lat"], r["home_lon"])] if has_h else None
    pn = pair_n[(r["home_lat"], r["home_lon"], r["work_lat"], r["work_lon"])] if has_h and has_w else None
    r["people_in_home_cell"] = hn
    r["people_with_same_home_work"] = pn
    r["unique_by_home"] = "" if hn is None else ("yes" if hn == 1 else "no")
    r["unique_by_home_work"] = "" if pn is None else ("yes" if pn == 1 else "no")
    n, s = r["nights_of_data"], r["home_confidence_score"]
    r["home_confidence_level"] = ("none" if not has_h else "sparse" if n < 3
                                  else "strong" if n >= 10 and s >= 0.30 else "partial")
    r["home_km_from_work"] = round(km(r["home_lat"], r["home_lon"], r["work_lat"], r["work_lon"]), 1) if has_h and has_w else None
    r["home_in_beijing"] = "" if not has_h else ("yes" if BOX[0] <= r["home_lat"] <= BOX[1] and BOX[2] <= r["home_lon"] <= BOX[3] else "no")

cols = ["user_id", "n_trajectories", "total_points", "first_day", "last_day", "active_days",
        "nights_of_data", "home_lat", "home_lon", "home_confidence_score", "work_lat", "work_lon",
        "work_confidence_score", "people_in_home_cell", "people_with_same_home_work",
        "unique_by_home", "unique_by_home_work", "home_confidence_level", "home_km_from_work",
        "home_in_beijing", "has_mode_labels"]
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r[k] is None else r[k]) for k in cols})

print(f"users={len(rows)} files={totals['files']} points={totals['points']} bad_lines={totals['bad_lines']}")
print("home_confidence_level:", dict(Counter(r["home_confidence_level"] for r in rows)))
print("unique_by_home=yes:", sum(r["unique_by_home"] == "yes" for r in rows),
      "| unique_by_home_work=yes:", sum(r["unique_by_home_work"] == "yes" for r in rows),
      "of", sum(r["people_with_same_home_work"] is not None for r in rows))
print("wrote", out)
