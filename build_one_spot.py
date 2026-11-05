#!/usr/bin/env python3
"""Build the One Spot CSV (one row per user) from the raw GeoLife Trajectories 1.3 folder.

Home: night 21:00-07:00 Beijing time; a home night for a cell = the evening's last point
(21:00-03:00) or the morning's first point (03:00-07:00) is in the cell.
Work: Mon-Fri 07:00-19:00; a work day for a cell = the morning's last point (07:00-13:00)
or the afternoon's first point (13:00-19:00) is in the cell; never the home cell.
Cells are 1 km squares (lat/lon rounded to 2 decimals). Ties go to the cell with more points.
"""
import csv, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

root = Path(sys.argv[1]).expanduser()
out = Path(sys.argv[2] if len(sys.argv) > 2 else "data/one_spot_users.csv").expanduser()
data = root / "Data" if (root / "Data").is_dir() else root

BJ = timedelta(hours=8)
MIN_DAYS = 12        # nights (home) or weekdays (work) needed to judge at all
MEDIUM_SHARE = 0.50  # top cell on at least half of them
STRONG_SHARE = 0.70  # top cell clearly dominant
STRONG_DAYS = 12     # and seen on at least this many nights/weekdays

def cell(lat, lon):
    return (round(lat, 2), round(lon, 2))

def level(top_days, total_days):
    if total_days == 0:
        return ""
    share = top_days / total_days
    if total_days >= MIN_DAYS and share >= STRONG_SHARE and top_days >= STRONG_DAYS:
        return "strong"
    if total_days >= MIN_DAYS and share >= MEDIUM_SHARE:
        return "medium"
    return "weak"

def top_cell(marks, pts, skip=None):
    """Cell with the most marked days (ties by points), excluding `skip`."""
    ranked = sorted((c for c in marks if c != skip), key=lambda c: (marks[c], pts[c]), reverse=True)
    return (ranked[0], marks[ranked[0]]) if ranked else (None, 0)

rows, totals = [], Counter()
for udir in sorted(p for p in data.iterdir() if p.is_dir()):
    files = sorted((udir / "Trajectory").glob("*.plt"))
    n_pts, bad = 0, 0
    days = set()
    nights = defaultdict(list)    # night key -> [(time, cell)]
    weekdays = defaultdict(list)  # date -> [(time, cell)]
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
                if t.hour >= 21 or t.hour < 7:
                    nights[(t - timedelta(hours=7)).date()].append((t, c))
                if t.weekday() < 5 and 7 <= t.hour < 19:
                    weekdays[t.date()].append((t, c))
    totals["files"] += len(files); totals["points"] += n_pts; totals["bad_lines"] += bad

    home_marks, home_pts, home_and = Counter(), Counter(), Counter()
    for ps in nights.values():
        ps.sort()
        evening = [c for t, c in ps if t.hour >= 21 or t.hour < 3]
        morning = [c for t, c in ps if 3 <= t.hour < 7]
        home_pts.update(c for t, c in ps)
        e, m = evening[-1] if evening else None, morning[0] if morning else None
        home_marks.update({e, m} - {None})
        if e and e == m:
            home_and[e] += 1
    hc, hn = top_cell(home_marks, home_pts)
    hlevel = level(hn, len(nights))
    home = hc if hlevel in ("strong", "medium") else None

    work_marks, work_pts, work_and = Counter(), Counter(), Counter()
    for ps in weekdays.values():
        ps.sort()
        am = [c for t, c in ps if t.hour < 13]
        pm = [c for t, c in ps if t.hour >= 13]
        work_pts.update(c for t, c in ps)
        a, p = am[-1] if am else None, pm[0] if pm else None
        work_marks.update({a, p} - {None})
        if a and a == p:
            work_and[a] += 1
    wc, wn = top_cell(work_marks, work_pts, skip=home)
    wlevel = level(wn, len(weekdays))
    work = wc if wlevel in ("strong", "medium") else None

    rows.append(dict(
        user_id=udir.name, total_points=n_pts,
        first_day=min(days).isoformat() if days else "", last_day=max(days).isoformat() if days else "",
        active_days=len(days),
        home_lat=f"{home[0]:.2f}" if home else "", home_lon=f"{home[1]:.2f}" if home else "",
        total_nights=len(nights), total_nights_top_cell=hn, home_and_nights=home_and[hc] if hc else 0,
        home_confidence_level=hlevel,
        work_lat=f"{work[0]:.2f}" if work else "", work_lon=f"{work[1]:.2f}" if work else "",
        total_weekdays=len(weekdays), total_weekdays_top_cell=wn, work_and_days=work_and[wc] if wc else 0,
        work_confidence_level=wlevel,
    ))

home_n = Counter((r["home_lat"], r["home_lon"]) for r in rows if r["home_lat"])
work_n = Counter((r["work_lat"], r["work_lon"]) for r in rows if r["work_lat"])
pair_n = Counter((r["home_lat"], r["home_lon"], r["work_lat"], r["work_lon"])
                 for r in rows if r["home_lat"] and r["work_lat"])
for r in rows:
    # "unique" = no other user has the same square, among users whose home/work was found
    hu = bool(r["home_lat"]) and home_n[(r["home_lat"], r["home_lon"])] == 1
    wu = bool(r["work_lat"]) and work_n[(r["work_lat"], r["work_lon"])] == 1
    pu = bool(r["home_lat"] and r["work_lat"]) and pair_n[(r["home_lat"], r["home_lon"], r["work_lat"], r["work_lon"])] == 1
    r["unique_by"] = ("no_location" if not (r["home_lat"] or r["work_lat"]) else
                      "both" if hu and wu else "home" if hu else "work" if wu else "pair" if pu else "none")

cols = ["user_id", "total_points", "first_day", "last_day", "active_days",
        "home_lat", "home_lon", "total_nights", "total_nights_top_cell", "home_and_nights", "home_confidence_level",
        "work_lat", "work_lon", "total_weekdays", "total_weekdays_top_cell", "work_and_days", "work_confidence_level",
        "unique_by"]
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

has_h = {r["user_id"] for r in rows if r["home_lat"]}
has_w = {r["user_id"] for r in rows if r["work_lat"]}
print(f"users={len(rows)} files={totals['files']} points={totals['points']} bad_lines={totals['bad_lines']}")
print("home_confidence_level:", dict(Counter(r["home_confidence_level"] or "blank" for r in rows)))
print("work_confidence_level:", dict(Counter(r["work_confidence_level"] or "blank" for r in rows)))
print(f"home={len(has_h)} work={len(has_w)} both={len(has_h & has_w)}")
print("unique_by:", dict(Counter(r["unique_by"] for r in rows)))
print("wrote", out)
