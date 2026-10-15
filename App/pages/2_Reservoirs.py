import pandas as pd
import plotly.express as px
import streamlit as st

from modules.Utils import AREA_TYPES, load_interval, month_options

st.title("Reservoir filling levels")
st.caption("Source: NVE Magasinstatistikk API")

# ---- Controls -----------------------------------------------------------
# The slider decides which part of the data is downloaded/kept, so everything
# below reacts to it. Default: the last 12 months.
months = month_options()
default_start = months[-12] if len(months) > 12 else months[0]

start, end = st.select_slider(
    "Download interval (months)",
    options=months,
    value=(default_start, months[-1]),
)

# Radio buttons pick the area type; each type has its own set of area numbers
area_type = st.radio(
    "Area type",
    options=list(AREA_TYPES),
    format_func=lambda key: f"{key} – {AREA_TYPES[key]}",
    horizontal=True,
)

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

# ---- Plot: one line per area number -------------------------------------
fig = px.line(wide, markers=False,
              title=f"Filling level per area – {AREA_TYPES[area_type]}")
fig.update_layout(xaxis_title="Date",
                  yaxis_title="Filling level (share of capacity)",
                  legend_title="Area")
st.plotly_chart(fig)