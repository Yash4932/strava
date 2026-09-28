"""Cleans the Fitbit/Strava CSVs and builds strava.db (SQLite). Usage: python clean.py [data_dir]"""
import sys, pathlib, sqlite3, pandas as pd
SRC = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "data")
HERE = pathlib.Path(__file__).parent
log = []
rd = lambda n: pd.read_csv(SRC / f"{n}_merged.csv")
WD = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
def wk(df, c="date"):
    df["weekday_num"] = df[c].dt.dayofweek; df["weekday"] = df.weekday_num.map(dict(enumerate(WD))); return df
def dedupe(df, name):
    n = len(df); df = df.drop_duplicates(); log.append(f"- {name}: {n-len(df)} duplicate rows removed, {int(df.isna().sum().sum())} nulls"); return df
DT = "%m/%d/%Y %I:%M:%S %p"

# daily activity
d = dedupe(rd("dailyActivity"), "daily_activity")
d["date"] = pd.to_datetime(d.ActivityDate, format="%m/%d/%Y")
d = d.rename(columns={"Id":"id","TotalSteps":"total_steps","TotalDistance":"total_distance","VeryActiveMinutes":"very_active_min",
    "FairlyActiveMinutes":"fairly_active_min","LightlyActiveMinutes":"lightly_active_min","SedentaryMinutes":"sedentary_min","Calories":"calories"})
d["tracked_min"] = d[["very_active_min","fairly_active_min","lightly_active_min","sedentary_min"]].sum(axis=1)
d["not_worn"] = ((d.very_active_min + d.fairly_active_min + d.lightly_active_min) == 0).astype(int)
neg = int((d[["total_steps","total_distance","calories","sedentary_min"]] < 0).sum().sum())
log.append(f"- daily_activity: {neg} negative values; {int(d.not_worn.sum())} days flagged not_worn (0 active minutes, sedentary up to 1440)")
d = wk(d)[["id","date","weekday","weekday_num","total_steps","total_distance","very_active_min","fairly_active_min","lightly_active_min","sedentary_min","tracked_min","calories","not_worn"]]

# sleep per day
s = dedupe(rd("sleepDay"), "sleep_day"); s["date"] = pd.to_datetime(s.SleepDay, format=DT).dt.normalize()
s = wk(s.rename(columns={"Id":"id","TotalSleepRecords":"records","TotalMinutesAsleep":"minutes_asleep","TotalTimeInBed":"time_in_bed"}))
s = s[["id","date","weekday","weekday_num","records","minutes_asleep","time_in_bed"]]

# hourly (calories + steps + intensity merged)
h = rd("hourlyCalories").merge(rd("hourlySteps"), on=["Id","ActivityHour"]).merge(rd("hourlyIntensities"), on=["Id","ActivityHour"])
h = dedupe(h, "hourly"); h["ts"] = pd.to_datetime(h.ActivityHour, format=DT); h["date"] = h.ts.dt.normalize(); h["hour"] = h.ts.dt.hour
h = wk(h.rename(columns={"Id":"id","Calories":"calories","StepTotal":"steps","TotalIntensity":"intensity"}))
h = h[["id","ts","date","hour","weekday","weekday_num","calories","steps","intensity"]]

# weight
w = dedupe(rd("weightLogInfo"), "weight_log"); w["date"] = pd.to_datetime(w.Date, format=DT).dt.normalize()
w = w.rename(columns={"Id":"id","WeightKg":"weight_kg","BMI":"bmi","Fat":"fat"})[["id","date","weight_kg","bmi","fat"]].round(2)

# minute sleep -> one row per sleep session (minute rows are summarised, never analysed one by one)
m = pd.read_csv(SRC / "minuteSleep_merged.csv"); m["t"] = pd.to_datetime(m.date, format=DT); m = m.drop_duplicates(["Id","logId","t"])
g = m.groupby(["Id","logId"]).agg(bed_time=("t","min"), wake_time=("t","max"), asleep_min=("value", lambda v:(v==1).sum()),
    restless_min=("value", lambda v:(v==2).sum()), awake_min=("value", lambda v:(v==3).sum())).reset_index()
g = g.rename(columns={"Id":"id","logId":"log_id"})
g["bed_hour"] = (g.bed_time.dt.hour + g.bed_time.dt.minute/60).apply(lambda x: x+24 if x < 12 else x).round(2)
g["is_nap"] = ((g.wake_time - g.bed_time).dt.total_seconds()/60 < 180).astype(int)
log.append(f"- sleep_sessions: {len(m)} minute rows summarised into {len(g)} sessions ({int(g.is_nap.sum())} naps)")

with sqlite3.connect(HERE / "strava.db") as c:
    for name, df in [("daily_activity",d),("sleep_day",s),("hourly",h),("weight_log",w),("sleep_sessions",g)]:
        out = df.copy()
        for col in out.columns:
            if str(out[col].dtype).startswith("datetime"): out[col] = out[col].dt.strftime("%Y-%m-%d %H:%M:%S")
        out.to_sql(name, c, if_exists="replace", index=False)
        log.append(f"- **{name}**: {len(df)} rows, {df.id.nunique()} users")
(HERE / "cleaning_log.md").write_text("# Cleaning log\n\nDates parsed to real timestamps, columns renamed to snake_case, duplicates dropped.\n\n" + "\n".join(log))
print("\n".join(log))
