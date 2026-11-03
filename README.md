# One Spot: GeoLife home and work cells per user

`one_spot_users.csv` has one row per volunteer in Microsoft's GeoLife GPS dataset. Each row shows the user's likely home area, likely daytime (work or study) area, and how many other volunteers share those areas. The question behind it: **can one spot, or one pair of spots, single a person out?**

Labels used below: **[Fact]** = checked in the data. **[Guess]** = interpretation or a choice I made.

## Files

| File | What it is |
|---|---|
| `one_spot_users.csv` | The dataset: 182 rows + header, 21 columns, ~19 KB, UTF-8, comma-separated |
| `build_one_spot.py` | The script that builds the CSV from the raw GeoLife folder (Python 3, standard library only) |
| `one-spot-summary.html` | Visual summary with charts, also published as a private page |
| `one-spot-csv-plan.md` | The design notes written before the build |

## Source data

- **Dataset:** GeoLife GPS Trajectories 1.3, Microsoft Research Asia. Download: https://www.microsoft.com/en-us/download/details.aspx?id=52367
- **[Fact]** Input read: 182 users, 18,670 `.plt` trajectory files, 24,876,978 GPS points, 0 unreadable lines.
- **[Fact]** The 2011 user guide (v1.1) lists 17,621 trajectories. Version 1.3 has more files (18,670).
- **[Fact]** Raw point format: `lat,lon,0,altitude_ft,days_since_1899-12-30,date,time`, after 6 header lines. Times are GMT.
- **[Fact]** The user ID exists only in the folder name (`Data/<user_id>/Trajectory/`).

## How to rebuild

```
python3 build_one_spot.py "<path to Geolife Trajectories 1.3>" one_spot_users.csv
```

The script reads one `.plt` file at a time, so it does not need much memory. On your Mac it took about 2 minutes 20 seconds. It prints the totals so you can check them against the numbers above.

## Two rules used throughout

1. **Time:** raw times are GMT. The script adds 8 hours to get Beijing time before any day, night or weekday test.
2. **Cell:** a square about 1 km wide. Latitude and longitude are rounded to 2 decimals, e.g. `40.0137, 116.3092` → `40.01, 116.31`. In Beijing a cell is about 1.1 km × 0.85 km and holds thousands of homes.

Time windows:
- **Night:** 22:00–06:00 Beijing time. A point after midnight counts for the evening before.
- **Weekday daytime:** Monday–Friday, 09:00–17:00 Beijing time.

## Columns

Example values are for user `001`. Empty cells mean "no data", never zero.

| # | Column | Type | Meaning and how it is made | Example |
|---|---|---|---|---|
| 1 | `user_id` | text (3 digits) | Folder name of the user. Keep as text to keep the leading zeros | `001` |
| 2 | `n_trajectories` | integer | Number of `.plt` files (recorded trips) | `71` |
| 3 | `total_points` | integer | Number of GPS points | `108607` |
| 4 | `first_day` | date | Earliest date with a point (Beijing time) | `2008-10-23` |
| 5 | `last_day` | date | Latest date with a point (Beijing time) | `2008-12-15` |
| 6 | `active_days` | integer | Number of different dates with at least one point | `44` |
| 7 | `nights_of_data` | integer | Number of different nights with at least one night point | `21` |
| 8 | `home_lat` | decimal (2 dp) | Latitude of the **home cell**: the cell with the most night points | `40.01` |
| 9 | `home_lon` | decimal (2 dp) | Longitude of the home cell | `116.31` |
| 10 | `home_confidence_score` | 0–1 | Night points in the home cell ÷ all night points. Higher = sleeps in the same area more often. **Not a measured accuracy** | `0.602` |
| 11 | `work_lat` | decimal (2 dp) | Latitude of the **work cell**: the cell with the most weekday-daytime points | `39.98` |
| 12 | `work_lon` | decimal (2 dp) | Longitude of the work cell | `116.33` |
| 13 | `work_confidence_score` | 0–1 | Weekday-daytime points in the work cell ÷ all weekday-daytime points | `0.301` |
| 14 | `people_in_home_cell` | integer | How many of the 182 users have this same home cell. Includes the user, so 1 = alone | `1` |
| 15 | `people_with_same_home_work` | integer | How many users have this same home cell **and** work cell | `1` |
| 16 | `unique_by_home` | yes / no | `yes` if `people_in_home_cell` = 1. Blank if no home cell | `yes` |
| 17 | `unique_by_home_work` | yes / no | `yes` if `people_with_same_home_work` = 1. Blank if either cell is missing | `yes` |
| 18 | `home_confidence_level` | text | **none** = no night points · **sparse** = under 3 nights · **strong** = 10+ nights and score ≥ 0.30 · **partial** = everything else | `strong` |
| 19 | `home_km_from_work` | decimal (1 dp) | Straight-line (haversine) distance between the home and work cell centres. 0.0 = same cell | `3.7` |
| 20 | `home_in_beijing` | yes / no | `yes` if the home cell is inside lat 39.4–41.1, lon 115.4–117.5 | `yes` |
| 21 | `has_mode_labels` | yes / no | `yes` if the user's folder has a `labels.txt` (transport modes) | `no` |

## Key numbers

All **[Fact]**, counted from the CSV.

| Measure | Value |
|---|---|
| Users | 182 |
| Users with a home cell | 168 |
| Users with both a home and a work cell | 150 |
| Users alone in their home cell | 72 of 168 (43%) |
| Users with a home + work pair nobody else has | 111 of 150 (74%) |
| Home confidence level | strong 31 · partial 96 · sparse 41 · none 14 |
| Different home cells | 93 |
| Most crowded home cell | 39.98, 116.33 with 26 users |
| Home cell outside Beijing | 24 users |
| Median home-to-work distance | 3.4 km |
| Users with transport-mode labels | 69 |
| Points per user | median 35,182 · min 17 (user 060) · max 2,156,994 (user 153) |

## Limits and known issues

- **[Fact]** GeoLife has no true home or work labels. Home and work cells are inferences, and their accuracy cannot be measured.
- **[Fact]** "Unique" means unique among the 182 volunteers, not among all Beijing residents.
- **[Fact]** The method cannot tell work from study.
  - **[Guess]** Many volunteers were students or staff near the Microsoft Research Asia / Zhongguancun area. The 26-user cell at 39.98, 116.33 is probably that campus area.
- **[Fact]** 24 users' home cells are outside Beijing, for example user 172 in Frankfurt.
  - **[Guess]** These are mostly travel periods, not real homes.
- **[Fact]** Users `057`, `094` and `150` are identical in every column.
  - **[Guess]** The same person's data appears three times in the source. If so, their shared pair (count 3) is really one person, and the unique counts should be read with that in mind.
- **[Fact]** User `089` has a tie between two home cells, each with 2.9% of night points. The script keeps the first cell it finds. An earlier analysis chose the other cell, which is why it reported 73 and 112 unique users instead of 72 and 111.
- **[Fact]** User `163`'s `first_day` is 2000-01-02.
  - **[Guess]** This is a GPS clock error, since collection started in 2007.
- **[Guess]** The Beijing box (column 20) is my own choice, drawn loosely around the municipality.

## Citation

Zheng, Y., Fu, H., Xie, X., Ma, W.-Y., & Li, Q. (2011). *Geolife GPS trajectory dataset – User Guide*. Microsoft Research. https://www.microsoft.com/en-us/research/publication/geolife-gps-trajectory-dataset-user-guide/

Background on why home + work pairs identify people: Golle, P. & Partridge, K. *On the Anonymity of Home/Work Location Pairs* (in the project's `knowledge/` folder).
