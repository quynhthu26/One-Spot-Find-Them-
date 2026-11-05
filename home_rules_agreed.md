# One Spot: home rules agreed with thu (2026-11-04)

Labels: [Fact] = checked in the data. [Guess] = interpretation.

## Home rule
1. Night window: 21:00–07:00 Beijing time (GMT+8). A night belongs to its evening: night key = (t − 7h).date().
2. Cell: 1 km grid square, lat/lon rounded to 2 decimals (~1.1 × 0.85 km in Beijing).
3. Home night for a cell: the evening's recording ENDS there (last point 21:00–03:00) OR the morning's recording STARTS there (first point 03:00–07:00). Late-night points (00:00–05:00) on their own do NOT count. Decided: OR (AND tested: only 1 user, 035, passes because only 30% of nights have any morning recording).
4. Home cell: the cell with the most home nights; ties broken by more points.
5. Minimum nights of data: ≥ 12 (stability test: 12 nights → 92% same home as full data).
6. Home share: home nights in the home cell ÷ all nights ≥ 50%.
7. No minimum on points in the cell. No separate 8-home-night rule (removed; with 12 nights + 50% it never changes the result).
8. Homes outside Beijing count as homes.

## Result with rules 1–8 (OR version) [Fact]
- 46 of 182 users get a home; 31 different cells; 25 alone in their square.
- Nobody else within 1 km (centre to centre): 17; within 1.5 km: 12.
- Biggest shared cells: 39.98,116.33 (8 users); 40.01,116.32 (5).
- Passers: 001 002 004 005 007 008 009 012 014 015 016 017 018 020 022 025 028 029 030 035 036 038 039 041 044 056 067 068 071 074 078 082 084 085 095 096 097 119 125 128 140 144 154 167 168 179
- Source: explore/geolife_homerule_v2.csv (script explore_homerule_v2.py on thu's Mac).

## Still open
- (Decided) Extra column home_nights_end_and_start: nights where BOTH evening end and morning start are in the home cell.
- Ties / cell-border near-ties: show runner-up nights column.
- Status column naming the failed rule.
- Extra column: other users' homes within 1 km.
- Work-cell rules.
