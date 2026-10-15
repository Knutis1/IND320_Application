import pandas as pd
import streamlit as st

from modules.nve_api import (fetch_reservoirs, select_area, pivot_filling,
                             VALUE_COLS)

UNITS = {
    "filling_level": "Share of capacity (0–1)",
    "capacity_TWh": "TWh",
    "stored_energy_TWh": "TWh",
    "filling_level_prev_week": "Share of capacity (0–1)",
    "filling_level_change": "Change (share of capacity)",
}

# Readable names for the three area types the API offers
AREA_TYPES = {"NO": "Norway total", "EL": "Price areas (NO1–NO5)",
              "VASS": "Watercourse areas"}


@st.cache_data(ttl=3600)
def load_raw():
    """
    One call to the NVE API per hour. The API has no date parameters: it
    always returns the full history, so the download interval chosen by the
    user is applied immediately afterwards, in load_interval().
    """
    return fetch_reservoirs()


@st.cache_data(ttl=3600)
def load_interval(start_month, end_month, area_type):
    """
    Return the chosen interval for the chosen area type, one column per area
    number. Both arguments are part of the cache key, so each combination is
    computed once and reused.
    """
    df = load_raw()
    months = df["date"].dt.strftime("%Y-%m")
    df = df[(months >= start_month) & (months <= end_month)]
    return pivot_filling(df, area_type)


@st.cache_data(ttl=3600)
def month_options():
    """All months present in the data, as 'YYYY-MM' strings, for the slider."""
    df = load_raw()
    return sorted(df["date"].dt.strftime("%Y-%m").unique())