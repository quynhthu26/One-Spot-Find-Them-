# One Spot: GeoLife home and work squares per user

`data/one_spot_users.csv` has one row for each of the 182 volunteers in Microsoft's GeoLife GPS dataset. For each person it shows:

- their likely **home** square, where their night recordings end or start,
- their likely **work or study** square, where their weekday morning recordings end or afternoon recordings start,
- how many nights and weekdays back up each guess, and how confident the guess is,
- whether the home, the work square or the home + work pair singles them out among the volunteers.

The question behind it: **can one spot, or one pair of spots, single a person out?**

Labels used below: **[Fact]** = checked in the data. **[Guess]** = an interpretation or a design choice.

## Files

| File | What it is |
|---|---|
| `data/one_spot_users.csv` | The dataset: 182 rows + header, 18 columns, about 15 KB, UTF-8, comma-separated |
| `build_one_spot.py` | The script that builds the CSV from the raw GeoLife folder (Python 3, standard library only) |
| `explore/` | Read-only exploration scripts and outputs used to choose the rules (stability tests, rule variants, charts) |
| `README.md` | This file |

## Source data

- **Dataset:** GeoLife GPS Trajectories 1.3, Microsoft Research Asia. Download: https://www.microsoft.com/en-us/download/details.aspx?id=52367
- **[Fact]** Input read: 182 users, 18,670 `.plt` trajectory files, 24,876,978 GPS points, 0 unreadable lines.
- **[Fact]** The 2011 user guide (v1.1) lists 17,621 trajectories. Version 1.3 has more files (18,670).
- **[Fact]** Each raw point is `lat,lon,0,altitude_ft,days_since_1899-12-30,date,time`, after 6 header lines. Times are GMT.
- **[Fact]** The user ID exists only in the folder name (`Data/<user_id>/Trajectory/`).
- **[Fact]** Volunteers switched recording on and off themselves, so the data is mostly trips. A gap means "not recording", not "not there".

## How to rebuild

From this folder:

```
python3 build_one_spot.py "$HOME/Downloads/Geolife Trajectories 1.3" data/one_spot_users.csv
```

- The output path is optional; it defaults to `data/one_spot_users.csv`.
- At the end it prints the totals. Check that they read `users=182 files=18670 points=24876978 bad_lines=0`.

## How the columns are made

### Time
Raw times are GMT. The script adds 8 hours to get Beijing time before any day, night or weekday test. Beijing has no daylight saving.

### Square
A square is 0.01° × 0.01°: latitude and longitude are rounded to 2 decimals, for example `40.0137, 116.3092` → `40.01, 116.31`.
- In Beijing a square is about **1.11 km north–south × 0.85 km east–west** (about 0.95 km²).
- The stored number is the square's centre: `40.01` covers 40.005 to 40.015.
- Side-by-side squares (east–west) have centres 0.85 km apart, so two "different" squares can be neighbours.
- **[Guess]** One square holds thousands of homes in central Beijing.

### Why "where recording ends or starts", not "how long they stayed"
**[Fact]** Volunteers usually stopped recording soon after arriving (battery, GPS indoors, and the project was about trips). A rule based on stay length found a work square for only 5 users. So both rules look at **where a recording stops or starts**:
- coming home: the evening's recording ends at home,
- leaving home: the morning's recording starts at home,
- arriving at work: the morning's recording ends at work,
- leaving work: the afternoon's recording starts at work.

### Home rule
1. **Night** = 21:00–07:00 Beijing time. A point after midnight counts for the evening before (night key = date of the time minus 7 hours).
2. `total_nights` = nights with at least one point in that window.
3. A **home night** for a square = the **last point between 21:00 and 03:00** is in it **OR** the **first point between 03:00 and 07:00** is in it.
4. The top square = the square with the most home nights (ties: more night points).
5. The home square is filled in only if **`total_nights` ≥ 12** and the top square is home on **≥ 50%** of them (see levels).

### Work rule
1. **Weekday** = Monday–Friday, 07:00–19:00 Beijing time, split at 13:00. Public holidays are **not** skipped.
2. `total_weekdays` = weekdays with at least one point in that window.
3. A **work day** for a square = the **last point between 07:00 and 13:00** is in it **OR** the **first point between 13:00 and 19:00** is in it.
4. The top square = the square with the most work days (ties: more points), **never the user's home square** (when a home was found).
5. The work square is filled in only if **`total_weekdays` ≥ 12** and the top square is a work day on **≥ 50%** of them.

### Confidence levels
The same rule for home and work. "Days" = nights for home, weekdays for work; "share" = days in the top square ÷ all days.

| Level | Rule | Home | Work |
|---|---|---|---|
| **strong** | ≥ 12 days, share ≥ 0.70 **and** ≥ 12 days in the top square | 12 | 20 |
| **medium** | ≥ 12 days and share ≥ 0.50, but not strong | 34 | 28 |
| **weak** | some data, but fewer than 12 days or share < 0.50 | 131 | 124 |
| *(blank)* | no night / weekday data at all | 5 | 10 |

- Latitude and longitude are filled in **only for strong and medium**. Weak users keep their counts, but no location.
- **[Guess]** The thresholds are design choices, checked with stability tests in `explore/`: with 12 weekdays, two separate random sets of days pick the same work square about 96% of the time for users with a regular workplace; for home, 8+ home nights match the full-data home about 97% of the time and 12+ about 99–100%.

### AND columns
`home_and_nights` and `work_and_days` count the days where **both** events happen in the top square (the evening ends **and** the morning starts there; the morning ends **and** the afternoon starts there). They are information only and do not decide anything. Many people record only one of the two trips, so AND is often 0 even for clear homes.

### unique_by
Uniqueness is counted among users whose home or work square was found (strong or medium), using the same square.

| Value | Meaning | Users |
|---|---|---|
| `both` | nobody else has their home square **and** nobody else has their work square | 6 |
| `home` | their home square is unique (work shared or not found) | 19 |
| `work` | their work square is unique (home shared or not found) | 6 |
| `pair` | home and work squares are each shared, but nobody else has the same home + work pair | 5 |
| `none` | has a home and/or work square, but nothing singles them out | 31 |
| `no_location` | no home and no work square found | 115 |

## Columns

Example values are for user `001`. Empty cells mean "not found" or "no data".

| # | Column | Type | Meaning | Example |
|---|---|---|---|---|
| 1 | `user_id` | text (3 digits) | Folder name of the user. Keep as text to keep the leading zeros | `001` |
| 2 | `total_points` | integer | Number of GPS points | `108607` |
| 3 | `first_day` | date | Earliest date with a point (Beijing time) | `2008-10-23` |
| 4 | `last_day` | date | Latest date with a point (Beijing time) | `2008-12-15` |
| 5 | `active_days` | integer | Number of different dates with at least one point (any hour, weekends included) | `44` |
| 6 | `home_lat` | decimal (2 dp) | Latitude of the home square's centre; blank unless strong/medium | `40.01` |
| 7 | `home_lon` | decimal (2 dp) | Longitude of the home square's centre | `116.31` |
| 8 | `total_nights` | integer | Nights with at least one point 21:00–07:00 | `27` |
| 9 | `total_nights_top_cell` | integer | Home nights in the top square | `27` |
| 10 | `home_and_nights` | integer | Nights where the evening ends **and** the morning starts in the top square | `3` |
| 11 | `home_confidence_level` | text | strong / medium / weak / blank | `strong` |
| 12 | `work_lat` | decimal (2 dp) | Latitude of the work square's centre; blank unless strong/medium | `39.98` |
| 13 | `work_lon` | decimal (2 dp) | Longitude of the work square's centre | `116.33` |
| 14 | `total_weekdays` | integer | Mon–Fri days with at least one point 07:00–19:00 | `31` |
| 15 | `total_weekdays_top_cell` | integer | Work days in the top square | `29` |
| 16 | `work_and_days` | integer | Weekdays where the morning ends **and** the afternoon starts in the top square | `10` |
| 17 | `work_confidence_level` | text | strong / medium / weak / blank | `strong` |
| 18 | `unique_by` | text | both / home / work / pair / none / no_location | `home` |

You can check a share yourself. For user 001: home 27 ÷ 27 = 1.00, work 29 ÷ 31 = 0.94.

## Key numbers

All **[Fact]**, counted from the CSV.

| Measure | Value |
|---|---|
| Users | 182 |
| Users with a home square | 46 (strong 12 · medium 34) |
| Users with a work square | 48 (strong 20 · medium 28) |
| Users with both | 27 · 23 different pairs, 21 unique |
| Home only · work only · neither | 19 · 21 · 115 |
| No home: why | no night data 5 (060, 107, 116, 169, 170) · fewer than 12 nights 95 · 12+ nights but share < 50% 36 |
| No work: why | no weekday data 10 · fewer than 12 weekdays 78 · 12+ weekdays but share < 50% 46 (plus 007 and 008, whose best square was home) |
| Different home squares | 31 · 25 users alone in theirs |
| Most crowded home square | 39.98, 116.33 with 8 users |
| Different work squares | 15 · 12 users alone in theirs |
| Most crowded work squares | 39.98, 116.33 with 20 users · 39.98, 116.30 with 10 · 39.97, 116.33 with 6 |
| Singled out by something (`unique_by` both/home/work/pair) | 36 of 182 |
| Home or work squares outside Beijing | 0 |
| Points per user | median 35,182 · min 17 (user 060) · max 2,156,994 (user 153) |

## Limits and known issues

- **[Fact]** GeoLife has no true home or work labels. Home and work squares are inferences; the stability tests measure consistency, not accuracy.
- **[Fact]** "Unique" means unique among the volunteers whose location was found, in the same square, not among all Beijing residents.
- **[Fact]** Squares are a fixed grid: of the 25 users alone in their home square, only 17 have nobody else's home within 1 km (centre to centre).
- **[Fact]** The method cannot tell work from study.
  - **[Guess]** Many volunteers were students or staff near the Microsoft Research Asia / Zhongguancun area. The work square 39.98, 116.33 (20 users) is probably that campus area.
- **[Fact]** Public holidays (e.g. Chinese New Year, Golden Week) count as normal weekdays.
- **[Fact]** Some users change place over time: comparing the first and second half of their weekdays, 10 of 65 users with 24+ weekdays get a clearly different work square, and 12 more move to the square next door.
- **[Fact]** Users `057`, `094` and `150` are identical in every column.
  - **[Guess]** The same person's data appears three times in the source.
- **[Fact]** Users `007` and `008` record in the same months and live in neighbouring squares, but they are different people: when both recorded at the same minute (1,002 minutes) they were a median 12.9 km apart.
- **[Fact]** User `163`'s `first_day` is 2000-01-02.
  - **[Guess]** This is a GPS clock error, since collection started in 2007.

## Citation

Zheng, Y., Fu, H., Xie, X., Ma, W.-Y., & Li, Q. (2011). *Geolife GPS trajectory dataset – User Guide*. Microsoft Research. https://www.microsoft.com/en-us/research/publication/geolife-gps-trajectory-dataset-user-guide/

Background on why home + work pairs identify people: Golle, P. & Partridge, K. *On the Anonymity of Home/Work Location Pairs*.
