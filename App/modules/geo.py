"""
Area outlines for the map, read from the GeoJSON files made in Task4.ipynb
(converted from NVE's shapefiles and simplified).
"""

import json
from pathlib import Path

import streamlit as st

GEOJSON_DIR = Path(__file__).parent.parent / "data" / "geojson"


@st.cache_data
def load_geojson(area_type):
    """The GeoJSON for one area type: "EL", "VASS" or "NO"."""
    with open(GEOJSON_DIR / f"{area_type}.geojson", encoding="utf-8") as f:
        return json.load(f)
