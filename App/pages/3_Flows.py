import pandas as pd
import plotly.express as px
import streamlit as st
from pymongo import MongoClient

st.title("Cross-border flows")


@st.cache_resource          # a connection: one shared object for the app
def get_db():
    return MongoClient(st.secrets["MONGO_URI"])["ind320"]


@st.cache_data(ttl=3600)    # data: cached per argument combination
def load_yearly():
    return pd.DataFrame(list(get_db().flows_yearly.find({}, {"_id": 0})))


@st.cache_data(ttl=3600)
def load_hourly(connection, months):
    """Hourly rows for one connection, limited to the chosen months."""
    rows = list(get_db().flows_hourly.find({"connection": connection},
                                           {"_id": 0}))
    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["ts"])
    return df[df["ts"].dt.month.isin(months)].sort_values("ts")


yearly = load_yearly()
connections = sorted(yearly["connection"].unique())

left, right = st.columns(2)

with left:
    st.subheader("Yearly totals")
    conn = st.radio("Connection", connections)
    year = st.selectbox("Year", sorted(yearly["year"].unique(), reverse=True))

    subset = yearly[(yearly["connection"] == conn) & (yearly["year"] == year)]
    pie = px.pie(subset, values="total_mwh", names="direction",
                 title=f"{conn}, {year}: in and out of Norway")
    st.plotly_chart(pie)

with right:
    st.subheader("Hourly flows")
    MONTHS = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
              "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}

    # Pills let the user pick any set of months
    picked = st.pills("Months", options=list(MONTHS), selection_mode="multi",
                      default=["Jan"])

    if not picked:
        st.info("Choose at least one month.")
    else:
        hourly = load_hourly(conn, [MONTHS[m] for m in picked])
        line = px.line(hourly, x="ts", y="flow_mw", color="direction",
                       title=f"{conn}: flow per direction")
        line.update_layout(xaxis_title="Time (UTC)", yaxis_title="Flow (MW)",
                           legend_title="Direction")
        st.plotly_chart(line)

with st.expander("Data sources"):
    st.markdown("""
**Cross-border flows** — ENTSO-E Transparency Platform, physical flows,
downloaded in the Jupyter Notebook, stored in Cassandra, aggregated with
Spark and written to MongoDB. Each connection has two directions, queried
separately; timestamps are stored in UTC.

**Reservoir data** (other pages) — NVE Magasinstatistikk API, read live.
""")