import streamlit as st

from modules.analysis import lof_anomalies, spc_outliers
from modules.area import area_label, current_area, region_id
from modules.decorations import sun
from modules.theme import page_header
from modules.weather import WEATHER_PROPERTIES, WeatherAPIError, download_weather

sun()                 # sun in the top right corner
page_header("Outliers & anomalies", "Weather",
            "Source: open-meteo archive API, ERA5 reanalysis (hourly)")

area_type, area_number = current_area()
label = area_label(area_type, area_number)

year = st.selectbox("Year", list(range(2025, 2014, -1)), index=1)   # default 2024

N_CELLS = 10   # ERA5 grid cells per download, chosen at random from the 1000 points


# The download is part of the page: it starts by itself when area or year
# changes, and is cached, so each area and year is downloaded only once.
@st.cache_data(ttl=None, show_spinner=False)
def get_weather(region, year):
    return download_weather(region, f"{year}-01-01", f"{year}-12-31",
                            n_cells=N_CELLS, variables=list(WEATHER_PROPERTIES))


try:
    with st.spinner(f"Downloading ERA5 weather for {label}, {year} ..."):
        weather = get_weather(region_id(area_type, area_number), year)
except WeatherAPIError as err:
    st.error("open-meteo could not deliver the weather data right now. It is often "
             "busy, or the free daily limit may be used up. Please try again later.")
    st.caption(f"Details: {err}")
    st.stop()

st.caption(f"{label}, {year}: average of {N_CELLS} randomly chosen ERA5 grid "
           f"cells from the area's 1000 sampled locations.")

names = list(WEATHER_PROPERTIES)
tab_spc, tab_lof = st.tabs(["Outliers (SPC)", "Anomalies (LOF)"])

# ---- SPC ---------------------------------------------------------------
with tab_spc:
    st.markdown(
        "A DCT high-pass filter removes the slow, seasonal part of the series "
        "(SATV is what is left). The boundaries come from the median and MAD of the "
        "SATV, and are drawn around the original series. Hours outside them are "
        "outliers.")
    prop = st.selectbox("Weather property", names, index=0,   # temperature by default
                        format_func=WEATHER_PROPERTIES.get, key="spc_property")
    col1, col2 = st.columns(2)
    cutoff_days = col1.slider("DCT cut-off (days)", 2, 90, 30,
                              help="Variation slower than this is treated as seasonal")
    n_sigma = col2.slider("Number of robust standard deviations", 1.0, 6.0, 3.0, 0.5)

    series = weather[prop].dropna()
    if series.empty:
        st.warning("No data for this property.")
    else:
        fig, summary, outliers = spc_outliers(series, cutoff_days=cutoff_days,
                                              n_sigma=n_sigma,
                                              title=WEATHER_PROPERTIES[prop])
        st.plotly_chart(fig)
        if summary["robust_sigma"] == 0:
            st.warning("Most hours have the same value here (for example no "
                       "snow), so the robust spread is 0 and every change counts "
                       "as an outlier. SPC works best on temperature, humidity "
                       "and wind.")
        m1, m2, m3 = st.columns(3)
        m1.metric("Outliers", summary["n_outliers"])
        m2.metric("Share of hours", f"{summary['share_outliers_pct']} %")
        m3.metric("Robust σ", f"{summary['robust_sigma']:.3f}")
        st.write("Largest deviations")
        st.dataframe(outliers.reindex(outliers["satv"].abs()
                                      .sort_values(ascending=False).index).head(10)
                     .rename(columns={"value": WEATHER_PROPERTIES[prop],
                                      "satv": "SATV"}))

# ---- LOF ---------------------------------------------------------------
with tab_lof:
    st.markdown(
        "Local Outlier Factor compares each hour with its neighbours in time and "
        "value. Hours in a much sparser area than their neighbours are "
        "anomalies. The proportion of anomalies defaults to 1 %.")
    prop = st.selectbox("Weather property", names, index=0,
                        format_func=WEATHER_PROPERTIES.get, key="lof_property")
    col1, col2 = st.columns(2)
    contamination = col1.slider("Proportion of anomalies", 0.001, 0.10, 0.01, 0.001,
                                format="%.3f")
    n_neighbors = col2.slider("Neighbours", 5, 100, 20)

    series = weather[prop].dropna()
    if series.empty:
        st.warning("No data for this property.")
    else:
        with st.spinner("Running Local Outlier Factor ..."):
            fig, summary, anomalies = lof_anomalies(series, contamination=contamination,
                                                    n_neighbors=n_neighbors,
                                                    title=WEATHER_PROPERTIES[prop])
        st.plotly_chart(fig)
        m1, m2, m3 = st.columns(3)
        m1.metric("Anomalies", summary["n_anomalies"])
        m2.metric("Lowest anomaly", summary["min_anomaly"])
        m3.metric("Highest anomaly", summary["max_anomaly"])
        st.write("Anomalies")
        st.dataframe(anomalies.rename(columns={"value": WEATHER_PROPERTIES[prop]}).head(20))
