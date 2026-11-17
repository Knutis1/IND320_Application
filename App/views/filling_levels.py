import pandas as pd
import plotly.express as px
import streamlit as st

from modules.area import area_label, current_area
from modules.decorations import waterfalls
from modules.theme import page_header
from modules.Utils import AREA_TYPES, get_reservoirs, load_interval, month_options

waterfalls()          # water running down both sides
page_header("Filling levels", "Reservoirs", "Source: NVE Magasinstatistikk API")

get_reservoirs()            # downloads (cached) and shows a clear error if NVE is down
area_type, area_number = current_area()

# This page shows every area number of the chosen area type, so the user can
# compare them. The chosen area itself is highlighted in the plot.
months = month_options()
start, end = st.select_slider("Interval (months)", options=months,
                              value=(months[0], months[0]))   # default: first month

wide = load_interval(start, end, area_type)
if wide.empty:
    st.warning("No data in the chosen interval.")
    st.stop()

# ---- Table: one row per area number, sparkline over the interval --------
table = pd.DataFrame({
    "Area": list(wide.columns),
    "Filling level": [wide[col].dropna().tolist() for col in wide.columns],
    "Latest": [wide[col].dropna().iloc[-1] for col in wide.columns],
})
st.subheader(f"Overview {start} to {end}")
st.dataframe(
    table,
    column_config={
        "Area": st.column_config.TextColumn("Area"),
        # LineChartColumn turns each list into a small line chart
        "Filling level": st.column_config.LineChartColumn(
            f"Filling level ({start} – {end})", y_min=0, y_max=1),
        "Latest": st.column_config.NumberColumn("Latest", format="%.3f"),
    },
    hide_index=True,
)

# ---- Plot: one line per area number, the chosen one thicker --------------
fig = px.line(wide, title=f"Filling level per area – {AREA_TYPES[area_type]}")
chosen = area_label(area_type, area_number)
for trace in fig.data:
    trace.line.width = 4 if trace.name == chosen else 1.5
fig.update_layout(xaxis_title="Date", yaxis_title="Filling level (share of capacity)",
                  legend_title="Area")
st.plotly_chart(fig)
st.caption(f"Thick line: the chosen area ({chosen}).")
