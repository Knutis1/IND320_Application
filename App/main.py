import streamlit as st

st.set_page_config(page_title="IND320 Project", layout="wide")

st.title("IND320 – Reservoirs, weather and power flows")
st.write("Use the menu in the sidebar to open the pages. The area chosen in the "
         "sidebar (price area, watercourse area or all of Norway) is shared by "
         "the reservoir and analysis pages.")

st.markdown("""
| Page | Content | Data |
|---|---|---|
| **Reservoirs** | Weekly filling levels per area, table and plot | NVE Magasinstatistikk API |
| **Reservoir analysis** | STL decomposition and spectrogram of the filling level | NVE Magasinstatistikk API |
| **Weather analysis** | Precipitation outliers (SPC) and temperature anomalies (LOF) | open-meteo, ERA5 |
| **Flows** | Cross-border power flows | ENTSO-E data stored in MongoDB |
| **About** | About the project | |
""")
# Streamlit builds the sidebar menu automatically from the files in pages/
