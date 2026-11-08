import streamlit as st

st.title("About")
st.write("IND320 – Data to Decision, NMBU. Course project by Knut Ivar.")
st.markdown("""
- **Reservoirs / Reservoir analysis**: weekly filling level from NVE's
  Magasinstatistikk API, downloaded live and cached for one hour.
- **Weather analysis**: hourly ERA5 data from the open-meteo archive API.
  1000 random locations per area were sampled from NVE's shapefiles in the
  notebook; the app averages a random subset of the ERA5 grid cells they fall in.
- **Flows**: ENTSO-E cross-border flows, processed with Spark/Cassandra and
  stored in MongoDB Atlas.
""")
