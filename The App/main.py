import streamlit as st

st.set_page_config(page_title="IND320 Project", layout="wide")

st.title("IND320 – Reservoir statistics")
st.write("Weekly reservoir filling levels for Norway, 1995–2026 (source: NVE).")
st.write("Use the menu in the sidebar to open the other pages.")
# Streamlit builds the sidebar menu automatically from the files in pages/