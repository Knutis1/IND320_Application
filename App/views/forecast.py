import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.area import area_label, current_area, current_week, region_id
from modules.forecast import CURRENCY_COLUMNS, DEFAULT_EXOG, DEFAULTS, forecast_filling
from modules.norges_bank import download_exchange_rates
from modules.nve_api import select_area
from modules.decorations import weather_friends
from modules.theme import HIGHLIGHT, NAVY, page_header
from modules.Utils import get_reservoirs, weekly_weather_years

weather_friends()       # weather figures in the side margins
page_header("Forecast", "Reservoirs",
            "SNARIMAX (River) forecast of the weekly filling level, with weather "
            "(open-meteo) and exchange rates (Norges Bank) as optional inputs")

area_type, area_number = current_area()
label = area_label(area_type, area_number)
fill = select_area(get_reservoirs(), area_type, area_number)["filling_level"]
fill = fill.asfreq("W-SUN").interpolate()

EXOG = {"temperature": "Temperature", "snowfall": "Snowfall", "precipitation": "Precipitation",
        "wind_speed": "Wind speed", "EUR": "EUR/NOK", "USD": "USD/NOK"}

# ---- Time frame: training end is the week chosen on the map ---------------------
weeks = [w for w in fill.index if w.year >= 2012]
default_end = current_week(weeks[-1])
default_end = default_end if default_end in weeks else weeks[-1]
end = st.select_slider("Last week used for training (shared with the map)", options=weeks,
                       value=default_end,
                       format_func=lambda d: f"{d:%Y} week {d.isocalendar().week}")
st.session_state["week"] = end          # moving it here moves the map's week too

col1, col2 = st.columns(2)
history_years = col1.slider("Years of training history", 3, 25, DEFAULTS["history_years"])
horizon = col2.slider("Forecast horizon (weeks)", 4, 52, 12)

exog_columns = st.multiselect("Exogenous variables", list(EXOG), default=DEFAULT_EXOG,
                              format_func=EXOG.get,
                              help="Default: temperature and snowfall, which gave the best "
                                   "forecasts in the notebook tests.")

with st.expander("Model parameters (defaults = best settings from the notebook)"):
    c1, c2, c3 = st.columns(3)
    p = c1.number_input("p (AR order)", 0, 4, DEFAULTS["p"])
    d = c2.number_input("d (differencing)", 0, 2, DEFAULTS["d"])
    q = c3.number_input("q (MA order)", 0, 4, DEFAULTS["q"])
    c1, c2, c3 = st.columns(3)
    sp = c1.number_input("sp (seasonal AR)", 0, 3, DEFAULTS["sp"])
    sd = c2.number_input("sd (seasonal differencing)", 0, 1, DEFAULTS["sd"])
    sq = c3.number_input("sq (seasonal MA)", 0, 3, DEFAULTS["sq"])
    learning_rate = st.select_slider("Learning rate", [0.001, 0.002, 0.005, 0.01, 0.02, 0.03, 0.05],
                                     value=DEFAULTS["learning_rate"])
show_interval = st.toggle("Show 90 % interval (quantile models)", value=False,
                          help="Two extra models trained with the quantile loss "
                               "(optim.losses.Quantile) predict the 5 % and 95 % levels.")

# ---- Exogenous data (only what is selected) ---------------------------------------
first_year = (end - pd.DateOffset(years=history_years)).year
exog_parts = []
weather_cols = [c for c in exog_columns if c not in CURRENCY_COLUMNS]
currency_cols = [c for c in exog_columns if c in CURRENCY_COLUMNS]

if weather_cols:
    weather, failed = weekly_weather_years(region_id(area_type, area_number), first_year, end.year)
    if failed:
        st.warning("No weather for " + ", ".join(map(str, failed)) + " (open-meteo did not "
                   "answer). Missing weeks are filled with the average for that week of the year.")
    if weather.empty:
        st.error("No weather data could be loaded, so the weather variables are left out.")
        weather_cols = []
    else:
        exog_parts.append(weather[weather_cols])

if currency_cols:
    @st.cache_data(ttl=6 * 3600, show_spinner=False)
    def weekly_rates(start, stop):
        return download_exchange_rates(start, stop).resample("W-SUN").mean()
    try:
        with st.spinner("Downloading exchange rates from Norges Bank ..."):
            rates = weekly_rates(f"{first_year}-01-01", end.strftime("%Y-%m-%d"))
        exog_parts.append(rates[currency_cols])
    except Exception as err:
        st.warning(f"Could not get exchange rates from Norges Bank, so they are left out. ({err})")
        currency_cols = []

used = weather_cols + currency_cols
exog = pd.concat(exog_parts, axis=1) if exog_parts else None

# ---- Forecast -------------------------------------------------------------------------
settings = dict(history_years=history_years, horizon=horizon, end=end, p=int(p), d=int(d),
                q=int(q), sp=int(sp), sd=int(sd), sq=int(sq), learning_rate=learning_rate)
try:
    with st.spinner("Training the model and forecasting ..."):
        pred = forecast_filling(fill, exog, used, **settings)
        lower = upper = None
        if show_interval:
            lower = forecast_filling(fill, exog, used, quantile=0.05, **settings)
            upper = forecast_filling(fill, exog, used, quantile=0.95, **settings)
except Exception as err:
    st.error("The model could not be trained with these settings. Try other parameters "
             "(for example lower orders) or more history.")
    st.caption(f"Details: {err}")
    st.stop()

actual = fill.reindex(pred.index).dropna()

m1, m2, m3, m4 = st.columns(4)
m1.metric(f"{label}, {end:%d.%m.%Y}", f"{fill[end]:.1%}")
m2.metric(f"Forecast in {horizon} weeks", f"{pred.iloc[-1]:.1%}",
          f"{(pred.iloc[-1] - fill[end]) * 100:+.1f} percentage points")
m3.metric("Exogenous inputs", f"{len(used)} variables",
          help=", ".join(EXOG[c] for c in used) or "none")
if len(actual):
    mae = (pred.reindex(actual.index) - actual).abs().mean()
    m4.metric(f"Error vs actual ({len(actual)} weeks)", f"{mae * 100:.1f} pp",
              help="Mean absolute error in percentage points for the weeks that have happened.")

# ---- Animated plot: the forecast is drawn one week at a time -------------------------
history = fill[end - pd.DateOffset(years=2):end]
after = fill[end:pred.index[-1]]

fig = go.Figure()
fig.add_scatter(x=history.index, y=history, name="Filling level (training data)",
                line=dict(color=NAVY))
if len(after) > 1:
    fig.add_scatter(x=after.index, y=after, name="What actually happened",
                    line=dict(color="#6C7A89", dash="dot"))
if show_interval:
    fig.add_scatter(x=upper.index, y=upper, line=dict(width=0), showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=lower.index, y=lower, name="90 % interval", fill="tonexty",
                    line=dict(width=0), fillcolor="rgba(192,57,43,0.15)")
fig.add_scatter(x=[end], y=[fill[end]], name="Forecast", mode="lines+markers",
                line=dict(color=HIGHLIGHT, width=3))
forecast_trace = len(fig.data) - 1

# Frame k shows the first k forecast weeks (starting from the last known week)
path_x = [end] + list(pred.index)
path_y = [fill[end]] + list(pred.values)
fig.frames = [go.Frame(data=[go.Scatter(x=path_x[:k + 1], y=path_y[:k + 1])],
                       traces=[forecast_trace], name=str(k))
              for k in range(1, len(path_x))]
fig.update_layout(
    title=f"Filling level {label}: {horizon}-week forecast from {end:%d.%m.%Y}",
    xaxis=dict(range=[history.index[0], pred.index[-1] + pd.Timedelta(weeks=2)], title="Week"),
    yaxis=dict(range=[0, 1.05], title="Filling level (share of capacity)", tickformat=".0%"),
    height=560,
    updatemenus=[dict(type="buttons", direction="left", x=0, y=-0.15, xanchor="left",
                      buttons=[dict(label="▶ Play", method="animate",
                                    args=[None, dict(frame=dict(duration=250, redraw=False),
                                                     fromcurrent=True, transition=dict(duration=0))]),
                               dict(label="⏸ Pause", method="animate",
                                    args=[[None], dict(mode="immediate",
                                                       frame=dict(duration=0, redraw=False))])])],
    sliders=[dict(x=0.15, y=-0.12, len=0.85, currentvalue=dict(prefix="Week ahead: "),
                  steps=[dict(label=str(k), method="animate",
                              args=[[str(k)], dict(mode="immediate",
                                                   frame=dict(duration=0, redraw=False))])
                         for k in range(1, len(path_x))])],
)
fig.update_layout(margin=dict(b=90))
st.plotly_chart(fig)
st.caption("Press ▶ Play to watch the forecast being built week by week. Each forecast "
           "week uses the model's own forecasts for the weeks before it (dynamic forecast). "
           "Future weather is the average for the same week in the training years; "
           "exchange rates keep their last value.")

table = pd.DataFrame({"forecast": pred})
if show_interval:
    table["lower 5 %"], table["upper 95 %"] = lower, upper
table["actual"] = fill.reindex(pred.index)
with st.expander("Forecast table"):
    st.dataframe(table.style.format("{:.1%}", na_rep="–"))
