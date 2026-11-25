import pandas as pd
import plotly.express as px
import streamlit as st

from modules.analysis import correlation_plot, lag_scan, sliding_window_correlation
from modules.area import area_label, current_area, current_week, region_id
from modules.nve_api import select_area
from modules.decorations import snow_to_reservoir
from modules.theme import page_header
from modules.Utils import get_reservoirs, weekly_weather_years

snow_to_reservoir()     # banner: snow -> melt -> reservoir
page_header("Weather vs reservoirs", "Weather",
            "Sliding window correlation between weekly weather (open-meteo, ERA5) "
            "and the reservoirs (NVE Magasinstatistikk)")

area_type, area_number = current_area()
label = area_label(area_type, area_number)

WEATHER = {"temperature": "Temperature (°C)", "precipitation": "Precipitation (mm/week)",
           "snowfall": "Snowfall (cm/week)", "wind_speed": "Wind speed (km/h)"}
RESERVOIR = {"change": "Weekly change in filling level",
             "filling_level": "Filling level"}

# ---- Controls ------------------------------------------------------------------
col1, col2 = st.columns(2)
weather_var = col1.selectbox("Weather property", list(WEATHER), format_func=WEATHER.get)
reservoir_var = col2.selectbox(
    "Reservoir variable", list(RESERVOIR), format_func=RESERVOIR.get,
    help="The weekly change shows when water comes in or goes out; the weather "
         "affects the change more directly than the level itself.")

this_year = pd.Timestamp.today().year
end_year = current_week(pd.Timestamp.today()).year      # follows the week on the map
first, last = st.select_slider("Years", options=list(range(2010, this_year + 1)),
                               value=(max(2010, end_year - 4), end_year))

col1, col2 = st.columns(2)
window = col1.slider("Window length (weeks)", 8, 104, 26, step=2)
lag = col2.slider("Lag (weeks)", -26, 26, 0,
                  help="Positive: the weather is compared with the reservoir that many "
                       "weeks later (the weather leads).")

# ---- Data ------------------------------------------------------------------------
weather, failed = weekly_weather_years(region_id(area_type, area_number), first, last)
if failed:
    st.warning("open-meteo did not answer for " + ", ".join(map(str, failed)) +
               ". Those years are left out.")
if weather.empty:
    st.error("No weather data could be loaded. open-meteo may be busy or the daily "
             "limit used up; please try again later.")
    st.stop()

fill = select_area(get_reservoirs(), area_type, area_number)["filling_level"]
fill = fill.asfreq("W-SUN").interpolate()
reservoir = fill.diff() if reservoir_var == "change" else fill
reservoir = reservoir[(reservoir.index.year >= first) & (reservoir.index.year <= last)]

data = sliding_window_correlation(weather[weather_var], reservoir, window=window, lag=lag)
if len(data) < window:
    st.warning("The chosen years give fewer weeks than the window length. "
               "Choose more years or a shorter window.")
    st.stop()

# ---- Results ---------------------------------------------------------------------
m1, m2, m3 = st.columns(3)
m1.metric("Correlation, whole period", f"{data['weather'].corr(data['reservoir']):.2f}")
m2.metric("Highest in a window", f"{data['correlation'].max():.2f}")
m3.metric("Lowest in a window", f"{data['correlation'].min():.2f}")

st.plotly_chart(correlation_plot(data, WEATHER[weather_var], RESERVOIR[reservoir_var],
                                 window, lag))

# Which lag gives the strongest connection? Useful when choosing inputs for
# the forecast: a weather variable that leads the reservoir can help predict it.
scan = lag_scan(weather[weather_var], reservoir).reset_index()
best = scan.loc[scan["correlation"].abs().idxmax()]
fig = px.bar(scan, x="lag (weeks)", y="correlation",
             title=f"Correlation over the whole period for each lag – strongest at "
                   f"{int(best['lag (weeks)'])} weeks ({best['correlation']:.2f})")
fig.update_traces(marker_color=["#C0392B" if v < 0 else "#1B2A4A" for v in scan["correlation"]])
fig.update_yaxes(range=[-1, 1])
st.plotly_chart(fig)

with st.expander("How to read this"):
    st.markdown(f"""
- **Area**: {label}, years {first}–{last}. Change the area in the sidebar or on the map.
- The top panel shows the two series; the bottom panel the correlation inside each
  {window}-week window. Blue means they move together, red that they move opposite.
- **Lag**: with a positive lag the weather is compared with the reservoir that many
  weeks later. If the correlation is strongest at a positive lag, the weather "leads"
  the reservoir, which is what makes it useful in a forecast.
- Correlation is not causation, and a window of a few months mostly picks up the
  seasons: in spring warm weeks and rising reservoirs go together (snow melt).
""")
