from pathlib import Path
import pandas as pd
import streamlit as st

# Norwegian -> English column names (same as in the notebook)
COLUMN_NAMES = {
    "dato_Id": "date", "omrType": "area_type", "omrnr": "area_number",
    "iso_aar": "iso_year", "iso_uke": "iso_week",
    "fyllingsgrad": "filling_level", "kapasitet_TWh": "capacity_TWh",
    "fylling_TWh": "stored_energy_TWh",
    "neste_Publiseringsdato": "next_publication_date",
    "fyllingsgrad_forrige_uke": "filling_level_prev_week",
    "endring_fyllingsgrad": "filling_level_change",
}

# Measurement columns shown in the app
VALUE_COLS = ["filling_level", "capacity_TWh", "stored_energy_TWh",
              "filling_level_prev_week", "filling_level_change"]

# Units for axis labels
UNITS = {
    "filling_level": "Share of capacity (0–1)",
    "capacity_TWh": "TWh",
    "stored_energy_TWh": "TWh",
    "filling_level_prev_week": "Share of capacity (0–1)",
    "filling_level_change": "Change (share of capacity)",
}

@st.cache_data
def load_data():
    # __file__ is modules/utils.py -> go up to the repo root, then into data/
    csv_path = Path(__file__).parent.parent / "data" / "reservoirs.csv"
    df = pd.read_csv(csv_path).rename(columns=COLUMN_NAMES)
    df["date"] = pd.to_datetime(df["date"])
    # Norway total only, sorted by date, date as index
    df = df[df["area_type"] == "NO"].sort_values("date").set_index("date")
    return df[VALUE_COLS]