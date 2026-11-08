import matplotlib.pyplot as plt
import streamlit as st

from modules.analysis import lof_anomalies, spc_outliers
from modules.area import area_label, area_selector, region_id
from modules.weather import download_weather

st.title("Weather analysis")
st.caption("Source: open-meteo archive API, ERA5 reanalysis (hourly)")

# Same area as on the other pages (shared selector in the sidebar), so the
# downloaded weather always matches the reservoir area being looked at
area_type, area_number = area_selector()
label = area_label(area_type, area_number)

year = st.selectbox("Year", list(range(2025, 2014, -1)), index=1)   # default 2024

N_CELLS = 20   # grid cells per download (the notebook uses more)


# The download is part of the page rather than a separate download page:
# it starts automatically when area or year changes, and the result is
# cached, so the same area and year are only downloaded once.
@st.cache_data(ttl=None, show_spinner="Downloading ERA5 data from open-meteo ...")
def get_weather(region, year):
    return download_weather(region, f"{year}-01-01", f"{year}-12-31",
                            n_cells=N_CELLS)


try:
    weather = get_weather(region_id(area_type, area_number), year)
except Exception as err:
    st.error("The open-meteo server did not answer. It is often busy; "
             "try again in a minute.")
    st.caption(f"Details: {err}")
    st.stop()

st.caption(f"{label}, {year}: average of {N_CELLS} randomly chosen ERA5 grid "
           f"cells from the region's 1000 sampled locations.")

tab_spc, tab_lof = st.tabs(["Outliers (SPC) – precipitation",
                            "Anomalies (LOF) – temperature"])

# ---- SPC ---------------------------------------------------------------
with tab_spc:
    st.markdown(
        "A DCT high-pass filter removes the slow, seasonal part of the "
        "precipitation. The boundaries come from the median and MAD of what is "
        "left, and are drawn around the original series. Hours outside them "
        "are outliers.")

    col1, col2 = st.columns(2)
    cutoff_days = col1.slider("DCT cut-off (days)", 2, 90, 30,
                              help="Variation slower than this is treated as seasonal")
    n_sigma = col2.slider("Number of robust standard deviations", 1.0, 6.0, 3.0, 0.5)

    fig, summary, outliers = spc_outliers(weather["precipitation"],
                                          cutoff_days=cutoff_days, n_sigma=n_sigma,
                                          title="Precipitation (mm/h)")
    st.pyplot(fig)
    plt.close(fig)

    m1, m2, m3 = st.columns(3)
    m1.metric("Outliers", summary["n_outliers"])
    m2.metric("Share of hours", f"{summary['share_outliers_pct']} %")
    m3.metric("Robust σ (mm/h)", summary["robust_sigma"])

    st.write("Largest outliers")
    st.dataframe(outliers.sort_values("value", ascending=False).head(10)
                         .rename(columns={"value": "precipitation (mm/h)"}))

# ---- LOF ---------------------------------------------------------------
with tab_lof:
    st.markdown(
        "Local Outlier Factor compares each hour with its neighbours in time and "
        "temperature. Hours in a much sparser area than their neighbours are "
        "anomalies. The proportion of anomalies defaults to 1 %.")

    col1, col2 = st.columns(2)
    contamination = col1.slider("Proportion of anomalies", 0.001, 0.10, 0.01, 0.001,
                                format="%.3f")
    n_neighbors = col2.slider("Neighbours", 5, 100, 20)

    fig, summary, anomalies = lof_anomalies(weather["temperature_2m"],
                                            contamination=contamination,
                                            n_neighbors=n_neighbors)
    st.pyplot(fig)
    plt.close(fig)

    m1, m2, m3 = st.columns(3)
    m1.metric("Anomalies", summary["n_anomalies"])
    m2.metric("Coldest anomaly", f"{summary['min_anomaly']} °C")
    m3.metric("Warmest anomaly", f"{summary['max_anomaly']} °C")

    st.write("Anomalies")
    st.dataframe(anomalies.rename(columns={"value": "temperature (°C)"}).head(20))
