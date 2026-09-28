# Cleaning log

Dates parsed to real timestamps, columns renamed to snake_case, duplicates dropped.

- daily_activity: 0 duplicate rows removed, 0 nulls
- daily_activity: 0 negative values; 83 days flagged not_worn (0 active minutes, sedentary up to 1440)
- sleep_day: 3 duplicate rows removed, 0 nulls
- hourly: 0 duplicate rows removed, 0 nulls
- weight_log: 0 duplicate rows removed, 65 nulls
- sleep_sessions: 187978 minute rows summarised into 459 sessions (66 naps)
- **daily_activity**: 940 rows, 33 users
- **sleep_day**: 410 rows, 24 users
- **hourly**: 22099 rows, 33 users
- **weight_log**: 67 rows, 8 users
- **sleep_sessions**: 459 rows, 24 users