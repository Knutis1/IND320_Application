import plotly.express as px
import streamlit as st
from modules.Utils import load_data, VALUE_COLS, UNITS

st.title("Plot")
df = load_data()

# Drop-down: one column or all columns
choice = st.selectbox("Choose column", ["All columns"] + VALUE_COLS)

# A slider to choose the range over the months ("YYYY-MM")
month_labels = df.index.strftime("%Y-%m")
months = sorted(month_labels.unique())
start, end = st.select_slider("Choose months", options=months,
                              value=(months[0], months[0]))

# Keep rows between the chosen start and end month decided by the slider
subset = df[(month_labels >= start) & (month_labels <= end)]

if choice == "All columns":
    # Different scales -> divide by each column's max absolute value
    plot_df = subset / df.abs().max()
    y_label = "Value / max |value|"
else:
    plot_df = subset[[choice]]
    y_label = UNITS[choice]

# Line chart with markers (few weekly points per month)
fig = px.line(plot_df, markers=True,
              title=f"{choice} – Norway total ({start} to {end})")
fig.update_layout(xaxis_title="Date", yaxis_title=y_label, legend_title="Column")
st.plotly_chart(fig)