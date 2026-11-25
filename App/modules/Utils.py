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

def get_reservoirs():
    """
    load_raw() with error handling for the pages: if the NVE API cannot be
    reached, show a clear message and stop the page instead of a traceback.
    """
    try:
        with st.spinner("Downloading reservoir data from NVE ..."):
            return load_raw()
    except Exception as err:
        st.error("Could not get reservoir data from NVE's Magasinstatistikk API. "
                 "The service may be down; please try again later.")
        st.caption(f"Details: {err}")
        st.stop()


# ---- Weekly weather, shared by the map and the correlation page -------------
@st.cache_data(ttl=24 * 3600, show_spinner=False)
def weekly_weather_year(region, year):
    """
    Weekly weather (weeks ending on Sunday) for one region and one year, from
    daily ERA5 data in Norwegian days. Cached per region and year, so pages that
    need the same year share the download.
    """
    from modules.weather import download_weather_daily, weekly_weather

    end = min(pd.Timestamp(f"{year}-12-31"), pd.Timestamp.today() - pd.Timedelta(days=6))
    # From late December the year before, so the first week of the year is complete
    daily = download_weather_daily(region, f"{year - 1}-12-25",
                                   end.strftime("%Y-%m-%d"), n_cells=10)
    return weekly_weather(daily)


def weekly_weather_years(region, first_year, last_year):
    """
    Weekly weather for several years, with a progress bar. Complete past years
    in a saved file from the notebook (data/weather_weekly_<region>.csv) are
    used directly; other years are downloaded. If open-meteo fails for a year,
    the saved file is used for that year when it has it.

    Returns (weekly DataFrame, list of years that could not be loaded).
    """
    from pathlib import Path

    from modules.weather import WeatherAPIError

    saved_file = Path(__file__).parent.parent / "data" / f"weather_weekly_{region}.csv"
    saved = (pd.read_csv(saved_file, index_col=0, parse_dates=True)
             if saved_file.exists() else None)

    years = list(range(first_year, last_year + 1))
    frames, failed = [], []
    bar = st.progress(0.0, text="Downloading weather from open-meteo ...")
    this_year = pd.Timestamp.today().year
    for i, year in enumerate(years):
        saved_year = None if saved is None else saved[saved.index.year == year]
        try:
            if saved_year is not None and year < this_year and len(saved_year) >= 52:
                frames.append(saved_year)        # a complete saved year: no download needed
            else:
                frames.append(weekly_weather_year(region, year))
        except WeatherAPIError:
            if saved is not None and (saved.index.year == year).any():
                frames.append(saved[saved.index.year == year])
            else:
                failed.append(year)
        bar.progress((i + 1) / len(years),
                     text=f"Weather loaded for {i + 1} of {len(years)} years")
    bar.empty()

    if not frames:
        return pd.DataFrame(), failed
    weekly = pd.concat(frames).sort_index()
    weekly = weekly[~weekly.index.duplicated(keep="last")]
    return weekly[(weekly.index.year >= first_year) & (weekly.index.year <= last_year)], failed
