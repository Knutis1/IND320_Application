import streamlit as st

from modules.area import area_label, current_area
from modules.theme import GROUP_COLOURS

st.title("💧 Reservoirs, weather and power in Norway")
st.write("IND320 project. The app combines NVE's reservoir statistics, weather "
         "data from open-meteo, cross-border power flows from ENTSO-E and "
         "exchange rates from Norges Bank.")

area_type, area_number = current_area()
st.info(f"Chosen area: **{area_label(area_type, area_number)}**. Change it in the "
        "sidebar. It is used on all reservoir and weather pages.")

# One card per group, with links to its pages
st.page_link("views/map.py", label="**Start with the map**: choose an area and a week", icon="🗺️")

groups = {
    "Reservoirs": ("Reservoirs (NVE)", [
        ("views/filling_levels.py", "Filling levels", "Weekly filling level per area"),
        ("views/decomposition.py", "Decomposition", "STL and spectrogram"),
        ("views/forecast.py", "Forecast", "SNARIMAX forecast with weather inputs"),
    ]),
    "Weather": ("Weather (open-meteo)", [
        ("views/weather_anomalies.py", "Outliers & anomalies", "SPC and LOF on a weather property"),
        ("views/correlation.py", "Weather vs reservoirs", "Sliding window correlation with lag"),
    ]),
    "Power & economy": ("Power & economy", [
        ("views/flows.py", "Cross-border flows", "ENTSO-E flows from MongoDB"),
        ("views/exchange_rates.py", "Exchange rates", "EUR and USD from Norges Bank"),
    ]),
}

columns = st.columns(len(groups))
for column, (group, (heading, pages)) in zip(columns, groups.items()):
    with column.container(border=True):
        st.markdown(f"<h4 style='color:{GROUP_COLOURS[group]}'>{heading}</h4>",
                    unsafe_allow_html=True)
        for path, title, text in pages:
            st.page_link(path, label=title)
            st.caption(text)
