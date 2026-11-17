import streamlit as st

from modules.theme import page_header

page_header("About", "About")
st.write("IND320 – Data to Decision, NMBU. Course project by Knut Ivar.")
st.markdown("""
**Pages and data**

- **Reservoirs**: weekly filling level from NVE's Magasinstatistikk API,
  downloaded live and cached for one hour.
- **Weather**: hourly ERA5 data from the open-meteo archive API. 1000 random
  locations per area were sampled from NVE's shapefiles in the notebook; the app
  averages a random subset of the ERA5 grid cells they fall in.
- **Cross-border flows**: ENTSO-E physical flows, processed with Spark and
  Cassandra and stored in MongoDB Atlas.
- **Exchange rates**: EUR and USD from Norges Bank's open API.

**Navigation**

The menu groups the pages by data source. The area chosen in the sidebar is
shared by all reservoir and weather pages; settings for each method are chosen
on the page itself.
""")
