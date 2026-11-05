# Work rule results (v4, home square skipped)

Read-only exploration. Source: `explore/geolife_work_v4.csv` (nh_ columns), home from `explore/geolife_homerule_v4.csv`.

**Rule:** Mon–Fri · 07:00–19:00, split at 13:00 · 1 km squares · a work day for a square = the morning recording ends there (last point 07:00–13:00) OR the afternoon recording starts there (first point 13:00–19:00) · work square = the square with the most work days (ties broken by points), never the user's home square · needs ≥ 12 weekdays and work share (work days ÷ weekdays) ≥ 50% · AND days kept as a column.

## 1. Found vs not found (182 users)
- **Work square found: 48**: 001 002 006 009 011 012 013 014 016 020 022 028 029 032 035 037 040 041 044 046 055 056 067 068 071 073 074 078 082 089 095 096 102 104 112 113 115 126 128 140 141 142 147 154 165 167 168 169
- **Not found: 134**
  - No weekday data 07:00–19:00: 10 (049, 118, 120, 143, 148, 149, 151, 173, 177, 178)
  - Fewer than 12 weekdays: 78 (1–2: 19 · 3–5: 27 · 6–8: 20 · 9–11: 12)
  - 12+ weekdays but share < 50% (too spread out): 46 (0.45–0.49: 7 · 0.40–0.44: 9 · 0.30–0.39: 7 · < 0.30: 23)
- Excluded only because their best square was home: 007, 008

## 2. Among the 48 work users
- Alone in their work square: 12 (nobody else's work square within 1 km: 9)
- Sharing a work square: 36
- Distinct work squares: 15
- Top work squares: 39.98, 116.33: 20 · 39.98, 116.3: 10 · 39.97, 116.33: 6 · 39.9, 116.39: 1 · 39.98, 116.34: 1

## 3. Home + work
- Users with both: 27: 001 002 009 012 014 016 020 022 028 029 035 041 044 056 067 068 071 074 078 082 095 096 128 140 154 167 168
- Distinct home+work pairs: 23, unique (one user): 21
- Home only: 19 · Work only: 21 · Neither: 115

## 4. Strength of evidence (work users)
- Median work days: 27.0 · median share: 0.674 · median AND days: 6.0 · AND = 0: 10

## 5. Outside Beijing
- Work squares outside lat 39.4–41.1 / lon 115.4–117.5: 0
