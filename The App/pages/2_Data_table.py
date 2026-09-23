import pandas as pd
import streamlit as st
from modules.Utils import load_data, VALUE_COLS

st.title("Data table")
df = load_data()

# Find the first month in the data and keep only its rows
months = df.index.to_period("M")
first_month = months[0]
df_first = df[months == first_month]

# Build a new table: one row per data column,
# with that column's values for the first month stored as a list
table = pd.DataFrame({
    "column": VALUE_COLS,
    "first_month": [df_first[col].tolist() for col in VALUE_COLS],
})

# LineChartColumn draws a small line chart from each list
st.dataframe(
    table,
    column_config={
        "column": st.column_config.TextColumn("Column"),
        "first_month": st.column_config.LineChartColumn(f"First month ({first_month})"),
    },
    hide_index=True,
)