import branca.colormap as cm
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from modules.area import AREA_TYPE_NAMES, area_label, current_area, region_id, set_area
from modules.geo import load_geojson
from modules.theme import HIGHLIGHT, NAVY, page_header
from modules.Utils import get_reservoirs, weekly_weather_year
from modules.weather import WeatherAPIError

page_header("Map", "Overview",
            "Click an area to choose it for all pages. Colours show the filling level "
            "(NVE) or a weather property (open-meteo, ERA5) for the chosen week.")

AREA_NUMBERS = {"EL": [1, 2, 3, 4, 5], "VASS": [1, 2, 3], "NO": [0]}

# What the areas can be coloured by: label -> (column, unit, colour scale)
COLOUR_BY = {
    "Filling level": ("filling_level", "share of capacity", cm.linear.Blues_09),
    "Temperature": ("temperature", "°C, weekly mean", cm.linear.RdYlBu_11),
    "Precipitation": ("precipitation", "mm per week", cm.linear.GnBu_09),
    "Snowfall": ("snowfall", "cm per week", cm.linear.PuBu_09),
    "Wind speed": ("wind_speed", "km/h, mean of daily max", cm.linear.YlOrBr_09),
}

area_type, area_number = current_area()
reservoirs = get_reservoirs()

# ---- Controls -------------------------------------------------------------
col1, col2 = st.columns([1, 2])
types = list(AREA_NUMBERS)
shown = col1.radio("Areas", types, index=types.index(area_type),
                   format_func=lambda t: AREA_TYPE_NAMES[t], horizontal=True)
if shown != area_type:
    # Switching area type on the map changes the shared area as well
    set_area(shown, AREA_NUMBERS[shown][0])
    st.rerun()

colour_by = col2.radio("Colour by", list(COLOUR_BY), horizontal=True)
column, unit, scale = COLOUR_BY[colour_by]

# Time: one week (Sunday), shared with the forecast page through session_state
weeks = sorted(reservoirs["date"].unique())
weeks = [pd.Timestamp(w) for w in weeks if pd.Timestamp(w).year >= 2010]
default = st.session_state.get("week", weeks[-1])
week = st.select_slider("Week", options=weeks, value=default if default in weeks else weeks[-1],
                        format_func=lambda d: f"{d:%Y} week {d.isocalendar().week}")
st.session_state["week"] = week

# ---- Values for each area in the chosen week ---------------------------------
numbers = AREA_NUMBERS[area_type]


values = {}
if column == "filling_level":
    rows = reservoirs[(reservoirs["area_type"] == area_type) & (reservoirs["date"] == week)]
    values = dict(zip(rows["area_number"], rows["filling_level"]))
else:
    # One download per area and year; cached, so moving the slider within a
    # year does not download again. A progress bar shows how far it has come.
    progress = st.progress(0.0, text="Downloading weather from open-meteo ...")
    failed = []
    for i, n in enumerate(numbers):
        try:
            weather = weekly_weather_year(region_id(area_type, n), week.year)
            if week in weather.index:
                values[n] = weather.loc[week, column]
        except WeatherAPIError:
            failed.append(area_label(area_type, n))
        progress.progress((i + 1) / len(numbers),
                          text=f"Weather downloaded for {i + 1} of {len(numbers)} areas")
    progress.empty()
    if failed:
        st.warning("open-meteo did not answer for " + ", ".join(failed) +
                   ". These areas are grey. Try again in a little while.")
    if not values:
        st.info("No weather data for this week yet (ERA5 is published about five "
                "days late). Choose an earlier week.")

# Colour scale over the values that exist (fixed 0-1 for the filling level)
known = [v for v in values.values() if pd.notna(v)]
if column == "filling_level":
    colours = scale.scale(0, 1)
elif known:
    low, high = min(known), max(known)
    colours = scale.scale(low, high if high > low else low + 1)
else:
    colours = None
if colours is not None:
    colours.caption = f"{colour_by} ({unit})"

# ---- Map ------------------------------------------------------------------------
geojson = load_geojson(area_type)
for feature in geojson["features"]:
    n = feature["properties"]["area_number"]
    v = values.get(n)
    feature["properties"]["name"] = area_label(area_type, n)
    feature["properties"]["value"] = "no data" if v is None or pd.isna(v) else f"{v:.2f}"


def style(feature):
    n = feature["properties"]["area_number"]
    v = values.get(n)
    chosen = n == area_number
    return {
        "fillColor": colours(v) if colours is not None and v is not None and pd.notna(v) else "#BBBBBB",
        "fillOpacity": 0.55,                              # transparent, the map shows through
        "color": HIGHLIGHT if chosen else NAVY,           # outline: contrast colour when chosen
        "weight": 5 if chosen else 1.2,                   # ... and thicker
    }


fmap = folium.Map(location=[65, 15], zoom_start=4, tiles="OpenStreetMap")
layer = folium.GeoJson(
    geojson, style_function=style,
    highlight_function=lambda f: {"weight": 3, "fillOpacity": 0.75},
    tooltip=folium.GeoJsonTooltip(["name", "value"], aliases=["Area", colour_by]),
).add_to(fmap)
fmap.fit_bounds(layer.get_bounds())          # zoom so that Norway fills the map
if colours is not None:
    colours.add_to(fmap)

left, right = st.columns([3, 1])
with left:
    result = st_folium(fmap, height=620, use_container_width=True, key="map",
                       returned_objects=["last_active_drawing", "last_object_clicked"])

# A click on an area makes it the chosen area for every page. The click
# position is remembered, so the same click is not handled twice when the
# page reruns (otherwise the sidebar selection could never change the area).
click = (result or {}).get("last_object_clicked")
feature = (result or {}).get("last_active_drawing")
if click and feature and click != st.session_state.get("map_last_click"):
    st.session_state["map_last_click"] = click
    clicked = feature["properties"]["area_number"]
    if clicked != area_number:
        set_area(area_type, clicked)
        st.rerun()

with right:
    st.subheader(area_label(area_type, area_number))
    chosen_value = values.get(area_number)
    st.metric(f"{colour_by}, {week:%d.%m.%Y}",
              "no data" if chosen_value is None or pd.isna(chosen_value) else f"{chosen_value:.2f}",
              help=unit)
    table = pd.DataFrame({"Area": [area_label(area_type, n) for n in numbers],
                          colour_by: [values.get(n) for n in numbers]})
    st.dataframe(table, hide_index=True, column_config={
        colour_by: st.column_config.NumberColumn(format="%.2f")})
    st.caption("The chosen area has a thick red outline. Its choice and the week "
               "are used on the other pages.")
