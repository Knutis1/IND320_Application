import matplotlib.pyplot as plt
import streamlit as st

from modules.analysis import spectrogram_plot, stl_decomposition
from modules.area import area_label, area_selector
from modules.nve_api import select_area
from modules.Utils import load_raw

st.title("Reservoir analysis")
st.caption("Source: NVE Magasinstatistikk API – weekly filling level")

# Same area as on the other pages (shared selector in the sidebar)
area_type, area_number = area_selector()
label = area_label(area_type, area_number)

# Weekly filling level for the chosen area, from the cached API download
fill = select_area(load_raw(), area_type, area_number)["filling_level"]
st.write(f"**{label}**: {len(fill)} weeks, "
         f"{fill.index.min():%Y-%m-%d} to {fill.index.max():%Y-%m-%d}")

tab_stl, tab_spec = st.tabs(["STL decomposition", "Spectrogram"])

# ---- STL ---------------------------------------------------------------
with tab_stl:
    st.markdown(
        "STL splits the filling level into a **trend**, a **seasonal** pattern "
        "and a **residual**. The data is weekly, so the period is 52. "
        "Both smoothers are window lengths and must be odd; the trend window "
        "must be longer than the period. Robust fitting gives unusual weeks "
        "less weight.")

    col1, col2, col3 = st.columns(3)
    seasonal = col1.slider("Seasonal smoother", 7, 51, 13, step=2)
    trend = col2.slider("Trend smoother", 53, 157, 89, step=2)
    robust = col3.toggle("Robust", value=True)

    fig = stl_decomposition(fill, period=52, seasonal=seasonal, trend=trend,
                            robust=robust, title=f"Filling level, {label}")
    st.pyplot(fig)
    plt.close(fig)   # free the figure; Streamlit reruns the script often

# ---- Spectrogram -------------------------------------------------------
with tab_spec:
    st.markdown(
        "The spectrogram shows how strong each frequency is over time. The "
        "frequency axis is in **cycles per year**, so the yearly cycle is the "
        "band at 1. A longer window gives sharper frequencies but less detail "
        "in time.")

    col1, col2 = st.columns(2)
    window_length = col1.slider("Window length (weeks)", 26, 260, 104, step=2)
    overlap = col2.slider("Overlap (weeks)", 0, window_length - 2,
                          min(78, window_length - 2), step=2)

    fig = spectrogram_plot(fill, window_length=window_length, overlap=overlap,
                           title=f"Filling level, {label}")
    st.pyplot(fig)
    plt.close(fig)
