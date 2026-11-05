#!/usr/bin/env python3
"""Read-only: compare three work-day definitions (A 07-19 split 12, B 08-19 split 13, C 08:00/13:00 snapshots)."""
import csv, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

root = Path(sys.argv[1]).expanduser()
out = sys.argv[2] if len(sys.argv) > 2 else "geolife_work_v3.csv"
data = root / "Data" if (root / "Data").is_dir() else root
BJ = timedelta(hours=8)
SNAP = timedelta(minutes=15)

home = {}
for r in csv.DictReader(open("geolife_homerule_v4.csv")):
    if r["is_home"] == "yes":
        home[r["user_id"]] = (float(r["home_lat"]), float(r["home_lon"]))

def nearest(ps, target):
    best = min(ps, key=lambda tc: abs(tc[0] - target), default=None)
    return best[1] if best and abs(best[0] - target) <= SNAP else None

def day_marks(ps, version):
    """Return (in_window, morning_cell, afternoon_cell) for one weekday's sorted points."""
    if version == "a":
        win = [tc for tc in ps if 7 <= tc[0].hour < 19]
        mo = [c for t, c in win if t.hour < 12]
        af = [c for t, c in win if t.hour >= 12]
        return bool(win), mo[-1] if mo else None, af[0] if af else None
    if version == "b":
        win = [tc for tc in ps if 8 <= tc[0].hour < 19]
        mo = [c for t, c in win if t.hour < 13]
        af = [c for t, c in win if t.hour >= 13]
        return bool(win), mo[-1] if mo else None, af[0] if af else None
    win = [tc for tc in ps if 8 <= tc[0].hour < 19]
    d = ps[0][0].date()
    return (bool(win), nearest(ps, datetime(d.year, d.month, d.day, 8)),
            nearest(ps, datetime(d.year, d.month, d.day, 13)))

stats = {v: Counter() for v in "abc"}
lost_arrival = 0
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
                if t.weekday() < 5 and 7 <= t.hour < 19 or (t.weekday() < 5 and t.hour == 6 and t.minute >= 45):
                    days[t.date()].append((t, (round(lat, 2), round(lon, 2))))

    r = {"user_id": udir.name}
    h = home.get(udir.name)
    for ps in days.values():
        ps.sort()
        mo7 = [t for t, c in ps if 7 <= t.hour < 12]
        if mo7 and mo7[0].hour == 7 and mo7[-1].hour < 8:
            lost_arrival += 1
    for v in "abc":
        work, pts = Counter(), Counter()
        n = 0
        for ps in days.values():
            inwin, m, a = day_marks(ps, v)
            if not inwin:
                continue
            n += 1
            s = stats[v]
            s["days"] += 1; s["morning"] += m is not None; s["afternoon"] += a is not None
            s["both"] += m is not None and a is not None
            for t, c in ps:
                pts[c] += 1
            for c in {m, a} - {None}:
                work[c] += 1
        r[f"{v}_weekdays"] = n
        for x in ("work_lat", "work_lon", "work_days", "work_share", "same_as_home"):
            r[f"{v}_{x}"] = ""
        if work:
            wc = max(work, key=lambda c: (work[c], pts[c]))
            r.update({f"{v}_work_lat": wc[0], f"{v}_work_lon": wc[1], f"{v}_work_days": work[wc],
                      f"{v}_work_share": round(work[wc] / n, 3)})
            if h:
                r[f"{v}_same_as_home"] = "yes" if wc == h else "no"
    rows.append(r)
    print(udir.name, flush=True, end=" ")

with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

print()
for v in "abc":
    s = stats[v]
    e = [r for r in rows if r[f"{v}_weekdays"] >= 12]
    p = [r for r in e if r[f"{v}_work_share"] != "" and r[f"{v}_work_share"] >= 0.5]
    hp = [r for r in p if r["user_id"] in home]
    print(f"{v.upper()}: weekdays={s['days']} morning={s['morning']/s['days']:.1%} afternoon={s['afternoon']/s['days']:.1%} "
          f"both={s['both']/s['days']:.1%} | users>=12={len(e)} pass50={len(p)} home_users_pass={len(hp)} "
          f"work_eq_home={sum(r[f'{v}_same_as_home'] == 'yes' for r in hp)}")
diff = sum(1 for r in rows if r["a_work_lat"] != "" and r["b_work_lat"] != ""
           and (r["a_work_lat"], r["a_work_lon"]) != (r["b_work_lat"], r["b_work_lon"]))
print("A vs B users with different work square:", diff)
print("user-weekdays whose morning recording is only 07:00-07:59:", lost_arrival)
