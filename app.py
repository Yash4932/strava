import sqlite3, base64, pathlib, pandas as pd, plotly.express as px, plotly.graph_objects as go, streamlit as st
from plotly.subplots import make_subplots
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

HERE = pathlib.Path(__file__).parent; DB = HERE / "strava.db"
OR, PEACH = "#FC4C02", "#FDB69A"; DAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
SC = [[0,"#1c0f08"],[.5,OR],[1,"#FFE3D6"]]
st.set_page_config(page_title="Strava Fitness Lab", page_icon="🟧", layout="wide")
b64 = lambda f: base64.b64encode((HERE/"assets"/f).read_bytes()).decode()

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;700&family=Barlow+Condensed:wght@700;800&display=swap');
@property --n{syntax:'<integer>';initial-value:0;inherits:false}
@keyframes cnt{from{--n:0}to{--n:var(--t)}}
@keyframes rise{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}
@keyframes sheen{to{background-position:200% center}}
@keyframes bob{50%{transform:translateY(-8px) rotate(-3deg)}}
@keyframes pulse{50%{box-shadow:0 0 34px rgba(252,76,2,.45)}}
.stApp{background:linear-gradient(rgba(11,11,13,.82),rgba(11,11,13,.93)),url(data:image/jpeg;base64,BG) 0 0/820px repeat fixed;font-family:'Barlow',sans-serif}
[data-testid=stHeader]{background:transparent}
h1,h2,h3{font-family:'Barlow Condensed',sans-serif!important;letter-spacing:.5px;font-weight:800!important}
.hero{display:flex;align-items:center;gap:26px;padding:26px 30px;border-radius:22px;margin-bottom:18px;
 background:linear-gradient(110deg,rgba(252,76,2,.92),rgba(252,76,2,.55) 55%,rgba(20,20,24,.6));animation:rise .9s both,pulse 4s 1s infinite}
.hero img{width:92px;border-radius:20px;animation:bob 4s ease-in-out infinite}
.hero h1{margin:0;font-size:3.4rem;line-height:1;color:#fff;background:linear-gradient(90deg,#fff,#FFE3D6,#fff);background-size:200%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:sheen 5s linear infinite}
.hero p{margin:6px 0 0;color:#fff;opacity:.9;font-size:1.05rem}
.kpi{background:rgba(23,23,26,.82);border:1px solid rgba(252,76,2,.35);border-radius:16px;padding:16px 18px;transition:.25s;animation:rise .8s both}
.kpi:hover{transform:translateY(-4px);border-color:#FC4C02;box-shadow:0 8px 26px rgba(252,76,2,.28)}
.num{display:inline-block;font:800 2.5rem 'Barlow Condensed';color:#FC4C02;animation:cnt 1.8s ease-out forwards;counter-reset:n var(--n)}
.num::after{content:counter(n)}.kpi b{color:#FDB69A;font-weight:700;margin-left:4px}.kpi p{margin:0;opacity:.75;font-size:.9rem}
.chip{display:inline-block;margin:4px 6px 4px 0;padding:6px 14px;border-radius:99px;background:rgba(252,76,2,.16);border:1px solid #FC4C02;font-weight:700}
.note{border-left:4px solid #FC4C02;background:rgba(23,23,26,.8);padding:12px 16px;border-radius:0 12px 12px 0;margin:8px 0}
.stTabs [data-baseweb=tab]{font:700 1.1rem 'Barlow Condensed';letter-spacing:.5px}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
</style>""".replace("BG", b64("bg.jpg")), unsafe_allow_html=True)

@st.cache_data
def load():
    c = sqlite3.connect(DB); t = {}
    for n in ["daily_activity","sleep_day","hourly","weight_log","sleep_sessions"]:
        df = pd.read_sql(f"select * from {n}", c)
        for col in ("date","ts","bed_time","wake_time"):
            if col in df: df[col] = pd.to_datetime(df[col])
        t[n] = df
    return t
T = load()
D, S, H, SS, W = T["daily_activity"], T["sleep_day"], T["hourly"], T["sleep_sessions"], T["weight_log"]

st.sidebar.image(str(HERE/"assets"/"logo.png"), width=90); st.sidebar.markdown("### Strava Fitness Lab")
lo, hi = D.date.min().date(), D.date.max().date()
rng = st.sidebar.date_input("Date range", (lo, hi), min_value=lo, max_value=hi)
if len(rng) == 2:
    a, b = map(pd.Timestamp, rng); D, S, H = [x[x.date.between(a, b)] for x in (D, S, H)]
Dw = D[D.not_worn == 0]
st.sidebar.caption("Worn days only unless stated. 'Not worn' = a day with zero active minutes.")

def fx(fig, h=360):
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=h,
        margin=dict(l=8, r=8, t=44, b=8), font=dict(family="Barlow"), transition=dict(duration=700)); return fig
def kpis(items):
    for col, (lab, v, u), i in zip(st.columns(len(items)), items, range(9)):
        col.markdown(f'<div class="kpi" style="animation-delay:{i*.12}s"><span class="num" style="--t:{int(round(v))}"></span><b>{u}</b><p>{lab}</p></div>', unsafe_allow_html=True)
def bar(df, x, y, title, **k): return fx(px.bar(df, x=x, y=y, title=title, color=y, color_continuous_scale=SC, **k).update_coloraxes(showscale=False))

st.markdown(f'<div class="hero"><img src="data:image/png;base64,{b64("logo.png")}"><div><h1>STRAVA FITNESS LAB</h1><p>How {D.id.nunique()} athletes move, rest and recover, from Apr to May 2016.</p></div></div>', unsafe_allow_html=True)
tabs = st.tabs(["Overview","Athlete Profile","Patterns","Sleep","Personas","SQL Lab","Insights"])

with tabs[0]:
    kpis([("Athletes tracked", D.id.nunique(), ""), ("Avg daily steps", Dw.total_steps.mean(), ""), ("Days at 10k+ steps", 100*(Dw.total_steps >= 10000).mean(), "%"),
          ("Sedentary time per day", Dw.sedentary_min.mean()/60, "h"), ("Avg calories per day", Dw.calories.mean(), "kcal"), ("Days tracker not worn", D.not_worn.sum(), "")])
    c1, c2 = st.columns(2)
    wk = Dw.groupby("weekday").total_steps.mean().reindex(DAYS).round().reset_index()
    c1.plotly_chart(bar(wk, "weekday", "total_steps", "Average steps by weekday", text_auto=".0f"), width="stretch")
    g = Dw.assign(act=Dw.very_active_min + Dw.fairly_active_min + Dw.lightly_active_min).groupby("weekday")[["act","calories"]].mean().reindex(DAYS)
    f = make_subplots(specs=[[{"secondary_y": True}]]); f.add_bar(x=DAYS, y=g.act, name="Active minutes", marker_color=OR)
    f.add_scatter(x=DAYS, y=g.calories, name="Calories", line=dict(color=PEACH, width=4), secondary_y=True)
    c2.plotly_chart(fx(f.update_layout(title="Active minutes vs calories")), width="stretch")
    c3, c4 = st.columns(2)
    tr = Dw.groupby("date").total_steps.mean().reset_index()
    c3.plotly_chart(fx(px.area(tr, x="date", y="total_steps", title="Average steps across the study", color_discrete_sequence=[OR])), width="stretch")
    m = Dw.groupby("weekday")[["lightly_active_min","fairly_active_min","very_active_min"]].mean().reindex(DAYS).reset_index().melt("weekday")
    c4.plotly_chart(fx(px.bar(m, x="weekday", y="value", color="variable", title="Active minutes by intensity", color_discrete_sequence=["#FDB69A", "#FC4C02", "#ffffff"])), width="stretch")

with tabs[1]:
    uid = st.selectbox("Choose an athlete", sorted(D.id.unique()), format_func=str)
    u, uh = Dw[Dw.id == uid].sort_values("date"), H[H.id == uid]
    if u.empty: st.info("No worn days for this athlete in the selected range.")
    else:
        run = (u.total_steps >= 7500); streak = run.groupby((~run).cumsum()).sum().max()
        kpis([("Best day (steps)", u.total_steps.max(), ""), ("Avg steps", u.total_steps.mean(), ""), ("Longest 7.5k+ streak (days)", streak, ""), ("Best calorie day", u.calories.max(), "kcal")])
        ph = uh.groupby("hour").steps.mean().idxmax(); sl = S[S.id == uid].minutes_asleep.mean()
        badges = []
        if (u.total_steps >= 10000).sum() >= 5: badges.append("10K Club")
        if ph < 10: badges.append("Early Bird")
        elif ph >= 17: badges.append("Evening Mover")
        if sl >= 420: badges.append("Sleep Champ")
        if u.very_active_min.mean() >= 30: badges.append("Hard Effort")
        if u.sedentary_min.mean() > 1000: badges.append("Desk Warrior")
        st.markdown("".join(f'<span class="chip">{x}</span>' for x in badges or ["Rookie"]) + f"<br>Most active hour: <b>{ph}:00</b>", unsafe_allow_html=True)
        u = u.assign(wk=(u.date - u.date.min()).dt.days // 7)
        z = u.pivot_table(index="weekday_num", columns="wk", values="total_steps")
        st.plotly_chart(fx(go.Figure(go.Heatmap(z=z.values, x=[f"Week {i+1}" for i in z.columns], y=[DAYS[i] for i in z.index], colorscale=SC, xgap=4, ygap=4)).update_layout(title="Activity calendar (steps per day)", yaxis_autorange="reversed"), 300), width="stretch")

with tabs[2]:
    hm = H.groupby(["weekday","hour"]).steps.mean().unstack().reindex(DAYS)
    st.plotly_chart(fx(go.Figure(go.Heatmap(z=hm.values, x=hm.columns, y=hm.index, colorscale=SC, xgap=2, ygap=2)).update_layout(title="When do athletes move? Average steps by weekday and hour", yaxis_autorange="reversed"), 340), width="stretch")
    c1, c2 = st.columns(2)
    hc = H.groupby("hour").calories.mean().round(1).reset_index()
    c1.plotly_chart(bar(hc, "hour", "calories", "Average calories burnt each hour"), width="stretch")
    ps = Dw.groupby(Dw.id.astype(str)).sedentary_min.mean().div(60).round(1).sort_values().reset_index(); ps.columns = ["user", "hours"]
    c2.plotly_chart(bar(ps, "hours", "user", "Sedentary hours per day by user", orientation="h").update_layout(yaxis=dict(type="category")), width="stretch")
    q = H[H.hour.between(9, 20)].groupby("hour").steps.mean().nsmallest(3)
    st.markdown(f'<div class="note"><b>Nudge-time finder.</b> The quietest waking hours are <b>{", ".join(f"{h}:00" for h in q.index)}</b> (about {q.mean():.0f} steps per hour). Send inactivity reminders in these windows.</div>', unsafe_allow_html=True)

with tabs[3]:
    M = S.merge(D[["id","date","total_steps"]], on=["id","date"]); main = SS[SS.is_nap == 0]
    bh = main.bed_hour.mean() % 24; eff = 100 * S.minutes_asleep.sum() / S.time_in_bed.sum()
    kpis([("Sleep tracked users", S.id.nunique(), f"of {D.id.nunique()}"), ("Avg sleep (min)", S.minutes_asleep.mean(), "min"), ("Time in bed asleep", eff, "%"), ("Avg bedtime (24h)", bh*100, "")])
    st.caption(f"Average bedtime is {int(bh):02d}:{int(bh%1*60):02d}. Sleep data covers only part of the group.")
    c1, c2 = st.columns(2)
    sw = S.groupby("weekday").minutes_asleep.mean().div(60).reindex(DAYS).round(2).reset_index()
    c1.plotly_chart(bar(sw, "weekday", "minutes_asleep", "Average hours asleep by weekday", text_auto=".2f"), width="stretch")
    c2.plotly_chart(fx(px.histogram(main, x="bed_hour", nbins=24, title="When do athletes go to bed? (hour, 24+ = after midnight)", color_discrete_sequence=[OR])), width="stretch")
    M["hrs"] = M.minutes_asleep / 60
    st.plotly_chart(fx(px.scatter(M, x="total_steps", y="hrs", title=f"Steps vs sleep (correlation {M.total_steps.corr(M.hrs):.2f})", color_discrete_sequence=[OR], opacity=.7)), width="stretch")

with tabs[4]:
    U = Dw.groupby("id").agg(steps=("total_steps","mean"), sedentary=("sedentary_min","mean"), very_active=("very_active_min","mean"), calories=("calories","mean")).reset_index()
    U["compliance"] = 100 * (1 - D.groupby("id").not_worn.mean().reindex(U.id).values)
    U["c"] = KMeans(4, n_init=10, random_state=7).fit_predict(StandardScaler().fit_transform(U[["steps","sedentary","very_active","calories"]]))
    order = U.groupby("c").steps.mean().sort_values().index
    U["persona"] = U.c.map(dict(zip(order, ["Desk Dweller","Steady Walker","Active Mover","Power Athlete"])))
    c1, c2 = st.columns([3, 2])
    c1.plotly_chart(fx(px.scatter(U, x="steps", y="sedentary", color="persona", size="calories", hover_name=U.id.astype(str), title="Athlete personas (K-means on steps, sedentary, effort, calories)",
        color_discrete_sequence=[PEACH, OR, "#ffffff", "#8a2a05"]), 420), width="stretch")
    c2.dataframe(U.groupby("persona").agg(athletes=("id","count"), steps=("steps","mean"), sedentary_min=("sedentary","mean"), wear_pct=("compliance","mean")).round(0).sort_values("steps"), width="stretch")
    st.plotly_chart(bar(U.sort_values("compliance").assign(user=lambda d: d.id.astype(str)), "compliance", "user", "Tracker wear compliance (% of days worn)", orientation="h").update_layout(yaxis=dict(type="category"), height=520), width="stretch")

def queries():
    qs = []
    for line in open(HERE/"analysis.sql"):
        if line.startswith("-- name:"): qs.append({"name": line[8:].strip(), "note": "", "sql": ""})
        elif line.startswith("-- note:") and qs: qs[-1]["note"] = line[8:].strip()
        elif qs and not line.startswith("--"): qs[-1]["sql"] += line
    return qs
def run(sql):
    with sqlite3.connect(f"file:{DB}?mode=ro", uri=True) as c: return pd.read_sql(sql, c)

with tabs[5]:
    st.markdown("### SQL analysis")
    for q in queries():
        with st.expander(q["name"]):
            st.caption(q["note"]); st.code(q["sql"].strip(), language="sql"); r = run(q["sql"])
            a, b = st.columns([2, 3]); a.dataframe(r, width="stretch", hide_index=True)
            if len(r) > 1 and len(r.columns) > 1 and pd.api.types.is_numeric_dtype(r.iloc[:, 1]):
                b.plotly_chart(fx(px.bar(r, x=r.columns[0], y=r.columns[1], color_discrete_sequence=[OR]), 280), width="stretch")
    st.markdown("### Playground")
    st.caption("Tables: daily_activity, sleep_day, hourly, weight_log, sleep_sessions. Read-only.")
    sql = st.text_area("Write a SELECT query", "SELECT weekday, ROUND(AVG(calories)) AS avg_calories FROM daily_activity GROUP BY weekday_num ORDER BY weekday_num;", height=110)
    if st.button("Run query"):
        if not sql.strip().lower().startswith(("select", "with")): st.error("Only SELECT queries are allowed.")
        else:
            try: st.dataframe(run(sql), width="stretch")
            except Exception as e: st.error(f"Query failed: {e}")

with tabs[6]:
    ten = 100 * (Dw.total_steps >= 10000).mean(); sed = Dw.sedentary_min.mean() / 60
    st.markdown(f"""### Key findings
- Athletes reach 10,000 steps on only **{ten:.0f}%** of worn days and average **{Dw.total_steps.mean():,.0f}** steps.
- They spend about **{sed:.1f} hours** a day sedentary, and light activity makes up nearly all active time.
- **{D.not_worn.sum()}** days show no activity at all, which suggests the tracker was not worn.
- Sleep averages **{S.minutes_asleep.mean()/60:.1f} hours**, below the 8-hour mark, and it barely changes with step count.
- The dataset has **{D.id.nunique()} users**, not 30. Sleep covers {S.id.nunique()} and weight only {W.id.nunique()}, so those findings are indicative only.

### Recommendations
1. **Detect wear time.** Flag zero-activity days and prompt users to wear the tracker, so sedentary time is not overstated.
2. **Nudge at the right time.** Send inactivity reminders in the quiet midday windows shown in the Patterns tab.
3. **Coach by persona.** Give Desk Dwellers small daily step goals and give Power Athletes recovery and sleep insights.
4. **Add sleep and weight logging prompts.** Low participation limits what the data can say.""")
