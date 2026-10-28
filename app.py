import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Bike Sharing Insights", page_icon="🚲", layout="wide")

# Clean, readable dashboard styling
st.markdown("""
<style>
    .main {background-color: #f6f8fc;}
    [data-testid="stMetric"] {background: white; border: 1px solid #e7ebf3; padding: 16px; border-radius: 14px;}
    h1, h2, h3 {color: #172554;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv("hour.csv")
    df["dteday"] = pd.to_datetime(df["dteday"])
    df["hour_label"] = df["hr"].astype(str).str.zfill(2) + ":00"
    seasons = {1: "Winter", 2: "Spring", 3: "Summer", 4: "Fall"}
    weather = {1: "Clear / Few clouds", 2: "Mist / Cloudy", 3: "Light rain / snow", 4: "Heavy rain / snow"}
    weekdays = {0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday"}
    months = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
    df["season_name"] = df["season"].map(seasons)
    df["weather_name"] = df["weathersit"].map(weather)
    df["weekday_name"] = df["weekday"].map(weekdays)
    df["month_name"] = df["mnth"].map(months)
    df["day_type"] = df["workingday"].map({0:"Non-working day",1:"Working day"})
    df["year_label"] = df["yr"].map({0:"2011",1:"2012"})
    # UCI dataset's temperature/humidity/windspeed are normalized to a 0-1 scale.
    return df

df = load_data()

st.title("🚲 Bike Sharing Insights Dashboard")
st.caption("Interactive exploration of hourly bike rental demand, seasonality, weather, and rider segments.")
st.info("Dataset note: this is a bike rental demand dataset, not a road-traffic congestion dataset. Counts represent bike rentals.")

with st.sidebar:
    st.header("Dashboard filters")
    selected_years = st.multiselect("Year", sorted(df["year_label"].unique()), default=sorted(df["year_label"].unique()))
    selected_seasons = st.multiselect("Season", ["Winter", "Spring", "Summer", "Fall"], default=["Winter", "Spring", "Summer", "Fall"])
    selected_weather = st.multiselect("Weather", sorted(df["weather_name"].dropna().unique()), default=sorted(df["weather_name"].dropna().unique()))
    day_type = st.multiselect("Day type", ["Working day", "Non-working day"], default=["Working day", "Non-working day"])
    selected_months = st.multiselect("Month", list(df["month_name"].drop_duplicates()), default=list(df["month_name"].drop_duplicates()))

f = df[
    df["year_label"].isin(selected_years)
    & df["season_name"].isin(selected_seasons)
    & df["weather_name"].isin(selected_weather)
    & df["day_type"].isin(day_type)
    & df["month_name"].isin(selected_months)
].copy()

if f.empty:
    st.warning("No rows match the selected filters. Please widen your filters.")
    st.stop()

total_rentals = int(f["cnt"].sum())
avg_hourly = f["cnt"].mean()
peak_hour = f.groupby("hour_label")["cnt"].mean().idxmax()
peak_hour_count = f.groupby("hour_label")["cnt"].mean().max()
registered_share = f["registered"].sum() / max(f["cnt"].sum(), 1) * 100
casual_share = f["casual"].sum() / max(f["cnt"].sum(), 1) * 100

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total rentals", f"{total_rentals:,}")
k2.metric("Average rentals / hour", f"{avg_hourly:,.1f}")
k3.metric("Peak average hour", peak_hour, f"{peak_hour_count:,.0f} rentals/hour")
k4.metric("Registered rider share", f"{registered_share:.1f}%")

st.markdown("## Demand overview")
c1, c2 = st.columns([1.45, 1])
with c1:
    daily = f.groupby("dteday", as_index=False).agg(rentals=("cnt","sum"))
    fig = px.line(daily, x="dteday", y="rentals", title="Daily rental demand over time",
                  labels={"dteday":"Date","rentals":"Bike rentals"})
    fig.update_traces(line_width=2)
    fig.update_layout(height=350, margin=dict(l=20,r=20,t=55,b=20))
    st.plotly_chart(fig, use_container_width=True)
with c2:
    segment = pd.DataFrame({"Rider type":["Registered","Casual"], "Rentals":[int(f["registered"].sum()), int(f["casual"].sum())]})
    fig = px.pie(segment, names="Rider type", values="Rentals", hole=.48,
                 title="Rental share by rider type", color="Rider type",
                 color_discrete_map={"Registered":"#2563eb","Casual":"#f59e0b"})
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(height=350, margin=dict(l=20,r=20,t=55,b=20))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("## When do people rent bikes?")
c3, c4 = st.columns(2)
with c3:
    hourly = f.groupby("hr", as_index=False)["cnt"].mean()
    hourly["Hour"] = hourly["hr"].astype(str).str.zfill(2) + ":00"
    fig = px.bar(hourly, x="Hour", y="cnt", title="Average rentals by hour of day",
                 labels={"cnt":"Average rentals","Hour":"Hour"}, color="cnt", color_continuous_scale="Blues")
    fig.update_layout(height=360, coloraxis_showscale=False, margin=dict(l=20,r=20,t=55,b=20))
    st.plotly_chart(fig, use_container_width=True)
with c4:
    day_order = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
    weekday = f.groupby("weekday_name", as_index=False)["cnt"].mean()
    weekday["weekday_name"] = pd.Categorical(weekday["weekday_name"], categories=day_order, ordered=True)
    weekday = weekday.sort_values("weekday_name")
    fig = px.bar(weekday, x="weekday_name", y="cnt", title="Average rentals by day of week",
                 labels={"cnt":"Average hourly rentals","weekday_name":"Day"}, color="cnt", color_continuous_scale="Teal")
    fig.update_layout(height=360, coloraxis_showscale=False, margin=dict(l=20,r=20,t=55,b=20))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("## Weather and seasonal patterns")
c5, c6 = st.columns(2)
with c5:
    weather_avg = f.groupby("weather_name", as_index=False)["cnt"].mean().sort_values("cnt", ascending=False)
    fig = px.bar(weather_avg, x="weather_name", y="cnt", title="Average rentals by weather condition",
                 labels={"cnt":"Average hourly rentals","weather_name":"Weather"}, color="cnt", color_continuous_scale="Sunset")
    fig.update_layout(height=360, coloraxis_showscale=False, margin=dict(l=20,r=20,t=55,b=70))
    fig.update_xaxes(tickangle=-15)
    st.plotly_chart(fig, use_container_width=True)
with c6:
    season_avg = f.groupby("season_name", as_index=False)["cnt"].mean()
    season_avg["season_name"] = pd.Categorical(season_avg["season_name"], categories=["Winter","Spring","Summer","Fall"], ordered=True)
    season_avg = season_avg.sort_values("season_name")
    fig = px.bar(season_avg, x="season_name", y="cnt", title="Average rentals by season",
                 labels={"cnt":"Average hourly rentals","season_name":"Season"}, color="cnt", color_continuous_scale="Viridis")
    fig.update_layout(height=360, coloraxis_showscale=False, margin=dict(l=20,r=20,t=55,b=20))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("## Heatmap: day of week × hour")
heat = f.pivot_table(index="weekday_name", columns="hr", values="cnt", aggfunc="mean")
heat = heat.reindex(day_order)
fig = px.imshow(heat, aspect="auto", color_continuous_scale="YlGnBu",
                labels=dict(x="Hour of day", y="Day of week", color="Avg rentals"),
                title="Where daily demand peaks")
fig.update_layout(height=390, margin=dict(l=20,r=20,t=55,b=20))
st.plotly_chart(fig, use_container_width=True)

st.markdown("## Weather relationships")
c7, c8 = st.columns(2)
with c7:
    fig = px.scatter(f.sample(min(2500, len(f)), random_state=42), x="temp", y="cnt",
                     color="season_name", opacity=.55, title="Temperature vs. hourly rentals",
                     labels={"temp":"Normalized temperature","cnt":"Hourly rentals","season_name":"Season"})
    fig.update_layout(height=350, margin=dict(l=20,r=20,t=55,b=20))
    st.plotly_chart(fig, use_container_width=True)
with c8:
    fig = px.scatter(f.sample(min(2500, len(f)), random_state=42), x="hum", y="cnt",
                     color="weather_name", opacity=.55, title="Humidity vs. hourly rentals",
                     labels={"hum":"Normalized humidity","cnt":"Hourly rentals","weather_name":"Weather"})
    fig.update_layout(height=350, margin=dict(l=20,r=20,t=55,b=20))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("## Key takeaways")
hour_means = f.groupby("hr")["cnt"].mean()
weather_means = f.groupby("weather_name")["cnt"].mean()
season_means = f.groupby("season_name")["cnt"].mean()
weekday_means = f.groupby("weekday_name")["cnt"].mean()
takeaways = [
    f"**Peak hour in the current selection:** {hour_means.idxmax():02d}:00, averaging {hour_means.max():,.0f} rentals per hour.",
    f"**Lowest-demand hour:** {hour_means.idxmin():02d}:00, averaging {hour_means.min():,.0f} rentals per hour.",
]
if len(weather_means):
    takeaways.append(f"**Weather pattern:** highest average demand is during **{weather_means.idxmax()}** conditions.")
if len(season_means):
    takeaways.append(f"**Seasonality:** highest average demand is in **{season_means.idxmax()}**.")
if len(weekday_means):
    takeaways.append(f"**Day pattern:** highest average hourly demand is on **{weekday_means.idxmax()}**.")
for item in takeaways:
    st.markdown("- " + item)

with st.expander("View filtered data"):
    st.dataframe(f, use_container_width=True)
    st.download_button("Download filtered CSV", f.to_csv(index=False).encode("utf-8"), "filtered_bike_sharing.csv", "text/csv")

st.caption("Source: UCI Bike Sharing Dataset. Temperature, apparent temperature, humidity and wind speed are normalized values in the hourly file.")
