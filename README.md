# Strava Fitness Lab

A Streamlit dashboard and SQL analysis of Fitbit tracker data (33 users, April to May 2016), built as a Bellabeat-style marketing analytics case study and styled after Strava.

**Business question:** How are consumers using their smart fitness devices, and what should the marketing strategy do about it?

## What's inside the app

| Tab | What it shows |
|---|---|
| Overview | Animated KPIs, steps by weekday, active minutes vs calories, activity intensity, steps trend |
| Athlete Profile | Pick a user for personal records, streaks, badges and an activity calendar |
| Patterns | Weekday-by-hour heatmap, calories by hour, sedentary time per user, best hours for inactivity nudges |
| Sleep | Sleep by weekday, bedtime distribution, steps vs sleep |
| Personas | K-means athlete groups and tracker wear compliance |
| SQL Lab | 15 documented queries with results and charts, plus a read-only query playground |
| Insights | Key findings and recommendations |

## Run locally

```
pip install -r requirements.txt
streamlit run app.py
```

## Project files

| File | Purpose |
|---|---|
| `app.py` | The Streamlit app |
| `analysis.sql` | All SQL queries (the app reads this file) |
| `strava.db` | Cleaned SQLite database used by the app |
| `clean.py` | Cleaning script that builds `strava.db` from the raw CSVs |
| `cleaning_log.md` | Summary of what the cleaning step did |
| `data/` | Raw CSVs used by `clean.py` |
| `assets/` | Background and logo images |
| `.streamlit/config.toml` | Dark orange theme |

To rebuild the database from the raw CSVs: `python clean.py`

## Data and cleaning

- **Source:** Fitbit Fitness Tracker Data (Kaggle, CC0), collected 12 Mar to 12 May 2016.
- **Files used:** `dailyActivity`, `sleepDay`, `hourlyCalories`, `hourlySteps`, `hourlyIntensities`, `weightLogInfo`, `minuteSleep`.
- **Files not used:** second-level heart rate and the other minute-level files, because the analysis works at day and hour level. `minuteSleep` is only summarised into one row per sleep session.
- **Cleaning steps:**
  - Dates parsed into proper timestamps and columns renamed to snake_case
  - 3 duplicate rows removed from the sleep data
  - No blank or negative values found in the activity data
  - 83 days with zero active minutes flagged as "tracker not worn" and excluded from averages
  - The hourly calories, steps and intensity files merged into a single table

## Limitations

- The data has 33 users, not the 30 stated in the case study.
- Sleep covers 24 users and weight only 8, so those findings are indicative only.
- No age, gender or profession information is available.
- The data is from 2016.

## Recommendations

1. Detect when the tracker is not worn so sedentary time is not overstated.
2. Send inactivity nudges in the quiet midday hours found in the Patterns tab.
3. Coach by persona, with small step goals for Desk Dwellers and recovery insights for Power Athletes.
4. Prompt users to log sleep and weight, since participation was low.
