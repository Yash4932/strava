-- SQL analysis for the Strava fitness case study (SQLite). Tables: daily_activity, sleep_day, hourly, weight_log, sleep_sessions
-- name: 1. Dataset coverage
-- note: Data integrity check. How many users and rows does each table hold?
SELECT 'daily_activity' AS dataset, COUNT(DISTINCT id) AS users, COUNT(*) AS row_count FROM daily_activity
UNION ALL SELECT 'hourly', COUNT(DISTINCT id), COUNT(*) FROM hourly
UNION ALL SELECT 'sleep_day', COUNT(DISTINCT id), COUNT(*) FROM sleep_day
UNION ALL SELECT 'weight_log', COUNT(DISTINCT id), COUNT(*) FROM weight_log;
-- name: 2. Range and negative-value check
-- note: Cleaning check. No negatives, so no rows had to be dropped.
SELECT MIN(total_steps) AS min_steps, MAX(total_steps) AS max_steps, MIN(calories) AS min_cal, MAX(calories) AS max_cal,
       MIN(sedentary_min) AS min_sed, MAX(sedentary_min) AS max_sed FROM daily_activity;
-- name: 3. Days the tracker was not worn, per user
-- note: A day with zero active minutes is treated as not worn. This supports the "detect wear" recommendation.
SELECT CAST(id AS TEXT) AS user_id, COUNT(*) AS not_worn_days FROM daily_activity WHERE not_worn = 1 GROUP BY id ORDER BY not_worn_days DESC LIMIT 15;
-- name: 4. Average steps by weekday
-- note: Worn days only.
SELECT weekday, ROUND(AVG(total_steps)) AS avg_steps FROM daily_activity WHERE not_worn = 0 GROUP BY weekday_num ORDER BY weekday_num;
-- name: 5. Share of days reaching 10,000 steps
-- note: The CDC-style step target, per user.
SELECT CAST(id AS TEXT) AS user_id, ROUND(100.0 * SUM(total_steps >= 10000) / COUNT(*), 1) AS pct_days_10k FROM daily_activity WHERE not_worn = 0 GROUP BY id ORDER BY pct_days_10k DESC;
-- name: 6. Most sedentary users
-- note: Average sedentary hours per day (worn days).
SELECT CAST(id AS TEXT) AS user_id, ROUND(AVG(sedentary_min) / 60.0, 1) AS avg_sedentary_hours FROM daily_activity WHERE not_worn = 0 GROUP BY id ORDER BY avg_sedentary_hours DESC LIMIT 15;
-- name: 7. Active minutes by intensity and weekday
-- note: Light activity dominates; very active time is small.
SELECT weekday, ROUND(AVG(lightly_active_min), 1) AS lightly_active, ROUND(AVG(fairly_active_min), 1) AS fairly_active, ROUND(AVG(very_active_min), 1) AS very_active
FROM daily_activity WHERE not_worn = 0 GROUP BY weekday_num ORDER BY weekday_num;
-- name: 8. Active minutes vs calories by weekday
-- note: Do busier days burn more?
SELECT weekday, ROUND(AVG(very_active_min + fairly_active_min + lightly_active_min), 1) AS avg_active_min, ROUND(AVG(calories)) AS avg_calories
FROM daily_activity WHERE not_worn = 0 GROUP BY weekday_num ORDER BY weekday_num;
-- name: 9. Calories burnt by hour of day
-- note: Lowest overnight, peaks in the early evening.
SELECT hour, ROUND(AVG(calories), 1) AS avg_calories FROM hourly GROUP BY hour ORDER BY hour;
-- name: 10. Best hours to send an inactivity nudge
-- note: The five quietest waking hours (09:00 to 20:00) by average steps.
SELECT hour, ROUND(AVG(steps)) AS avg_steps FROM hourly WHERE hour BETWEEN 9 AND 20 GROUP BY hour ORDER BY avg_steps ASC LIMIT 5;
-- name: 11. Average sleep by weekday
-- note: Sleep in hours. Sleep data covers fewer users.
SELECT weekday, ROUND(AVG(minutes_asleep) / 60.0, 2) AS avg_sleep_hours FROM sleep_day GROUP BY weekday_num ORDER BY weekday_num;
-- name: 12. Sleep vs steps (JOIN)
-- note: Do people sleep more on high-step days?
SELECT CASE WHEN a.total_steps >= 10000 THEN '3: 10k+ steps' WHEN a.total_steps >= 5000 THEN '2: 5k-10k steps' ELSE '1: under 5k steps' END AS step_band,
       ROUND(AVG(s.minutes_asleep) / 60.0, 2) AS avg_sleep_hours, COUNT(*) AS nights
FROM sleep_day s JOIN daily_activity a ON a.id = s.id AND a.date = s.date GROUP BY step_band ORDER BY step_band;
-- name: 13. User segments by average steps (CTE)
-- note: Standard step-count bands used in activity research.
WITH u AS (SELECT id, AVG(total_steps) AS s FROM daily_activity WHERE not_worn = 0 GROUP BY id)
SELECT CASE WHEN s >= 10000 THEN '4 Active 10k+' WHEN s >= 7500 THEN '3 Somewhat active' WHEN s >= 5000 THEN '2 Low active' ELSE '1 Sedentary' END AS segment, COUNT(*) AS users
FROM u GROUP BY segment ORDER BY segment;
-- name: 14. Bedtime and sleep efficiency (from minute data, summarised)
-- note: Main sleep sessions only (naps excluded). Bed hour above 24 means after midnight.
SELECT CAST(id AS TEXT) AS user_id, ROUND(AVG(bed_hour), 1) AS avg_bed_hour, ROUND(100.0 * SUM(asleep_min) / SUM(asleep_min + restless_min + awake_min), 1) AS pct_time_asleep
FROM sleep_sessions WHERE is_nap = 0 GROUP BY id ORDER BY avg_bed_hour;
-- name: 15. Weight log participation
-- note: Only a few users logged weight, so weight is not used for conclusions.
SELECT CAST(id AS TEXT) AS user_id, COUNT(*) AS logs, ROUND(MIN(weight_kg), 1) AS min_kg, ROUND(MAX(weight_kg), 1) AS max_kg, ROUND(AVG(bmi), 1) AS avg_bmi FROM weight_log GROUP BY id;
