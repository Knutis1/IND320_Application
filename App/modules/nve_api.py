"""
Connection to NVE's Magasinstatistikk API.
Replaces the reservoirs.csv file used in Part 1.
Docs: https://biapi.nve.no/magasinstatistikk/swagger
"""

import pandas as pd
import requests

BASE_URL = "https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/"

# Norwegian -> English column names (same mapping as in Part 1)
COLUMN_NAMES = {
    "dato_Id": "date", "omrType": "area_type", "omrnr": "area_number",
    "iso_aar": "iso_year", "iso_uke": "iso_week",
    "fyllingsgrad": "filling_level", "kapasitet_TWh": "capacity_TWh",
    "fylling_TWh": "stored_energy_TWh",
    "neste_Publiseringsdato": "next_publication_date",
    "fyllingsgrad_forrige_uke": "filling_level_prev_week",
    "endring_fyllingsgrad": "filling_level_change",
}

# The columns that hold measurements (the rest are identifiers)
VALUE_COLS = ["filling_level", "capacity_TWh", "stored_energy_TWh",
              "filling_level_prev_week", "filling_level_change"]


def fetch_reservoirs():
    """
    Download the full reservoir history and return it as a DataFrame with
    English column names and a real date column. This is the API replacement
    for pd.read_csv("reservoirs.csv") in Part 1.
    """
    response = requests.get(BASE_URL + "HentOffentligData", timeout=60)
    response.raise_for_status()          # raise an error if NVE is unavailable
    df = pd.DataFrame(response.json()).rename(columns=COLUMN_NAMES)
    df["date"] = pd.to_datetime(df["date"])
    return df


def fetch_areas():
    """
    Downloads the list of areas the API covers. The response is a list holding
    one object with three keys: land (NO), elspot (EL) and vassdrag (VASS).
    Returns one DataFrame with all areas stacked together.
    """
    response = requests.get(BASE_URL + "HentOmr%C3%A5der", timeout=30)
    response.raise_for_status()
    groups = response.json()[0]          # unwrap the single-element list
    frames = [pd.DataFrame(groups[key]) for key in ("land", "elspot", "vassdrag")]
    return pd.concat(frames, ignore_index=True)


def select_area(df, area_type="NO", area_number=0):
    """
    Keep one area, sort by date and use date as the index.
    Needed because every week appears once per area in the raw data,
    and the rows do not arrive in date order.
    """
    mask = (df["area_type"] == area_type) & (df["area_number"] == area_number)
    return df[mask].sort_values("date").set_index("date")[VALUE_COLS]

def pivot_filling(df, area_type):
    """
    Reshape to one column per area number, with filling_level as the values.
    EL gives five columns (NO1-NO5), VASS three, NO just the country total.
    This is the shape both the table and the plot need.
    """
    sub = df[df["area_type"] == area_type]
    wide = sub.pivot_table(index="date", columns="area_number",
                           values="filling_level", aggfunc="mean").sort_index()
    # Make the column names readable: EL 1 -> "NO1", VASS 1 -> "VASS 1", NO 0 -> "Norway"
    if area_type == "EL":
        wide.columns = [f"NO{n}" for n in wide.columns]
    elif area_type == "NO":
        wide.columns = ["Norway"]
    else:
        wide.columns = [f"{area_type} {n}" for n in wide.columns]
    return wide