"""
Entry point of the app. Run with: streamlit run App/main.py

Part 4: the menu is built with st.navigation, which groups the pages under
headers by data source. This script runs before every page, so the shared
sidebar (the area selector) is drawn here once and works on all pages.
"""

import streamlit as st

from modules import theme  # noqa: F401  (registers the Plotly theme)
from modules.area import area_selector

st.set_page_config(page_title="IND320 – Reservoirs, weather and power",
                   page_icon="💧", layout="wide")

PAGES = {
    "": [
        st.Page("views/home.py", title="Home", icon="🏠", default=True),
    ],
    "Overview": [
        st.Page("views/map.py", title="Map", icon="🗺️"),
    ],
    "Reservoirs (NVE)": [
        st.Page("views/filling_levels.py", title="Filling levels", icon="💧"),
        st.Page("views/decomposition.py", title="Decomposition", icon="📈"),
        st.Page("views/forecast.py", title="Forecast", icon="🔮"),
    ],
    "Weather (open-meteo)": [
        st.Page("views/weather_anomalies.py", title="Outliers & anomalies", icon="🌦️"),
        st.Page("views/correlation.py", title="Weather vs reservoirs", icon="🔗"),
    ],
    "Power & economy": [
        st.Page("views/flows.py", title="Cross-border flows", icon="⚡"),
        st.Page("views/exchange_rates.py", title="Exchange rates", icon="💱"),
    ],
    "About": [
        st.Page("views/about.py", title="About", icon="ℹ️"),
    ],
}

page = st.navigation(PAGES)

# Shared sidebar, below the menu
area_selector()

page.run()
