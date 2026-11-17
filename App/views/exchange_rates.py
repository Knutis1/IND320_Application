import pandas as pd
import plotly.express as px
import streamlit as st

from modules.norges_bank import download_exchange_rates
from modules.decorations import money_rain
from modules.theme import page_header

money_rain()          # falling banknotes in the background
page_header("Exchange rates", "Power & economy",
            "Source: Norges Bank's open currency API (daily, business days)")


@st.cache_data(ttl=6 * 3600, show_spinner=False)   # new rates come once a day
def get_rates(start, end):
    return download_exchange_rates(start, end)


today = pd.Timestamp.today().normalize()
start, end = st.date_input("Period", value=(today - pd.DateOffset(years=3), today),
                           min_value=pd.Timestamp("2000-01-01"), max_value=today)

try:
    with st.spinner("Downloading exchange rates from Norges Bank ..."):
        rates = get_rates(str(start), str(end))
except Exception as err:
    st.error("Could not get exchange rates from Norges Bank. Please try again later.")
    st.caption(f"Details: {err}")
    st.stop()

if rates.empty:
    st.warning("No rates in the chosen period.")
    st.stop()

# Latest rate and the change over the chosen period
cols = st.columns(len(rates.columns))
for col, currency in zip(cols, rates.columns):
    series = rates[currency].dropna()
    col.metric(f"{currency}/NOK, {series.index[-1]:%d.%m.%Y}", f"{series.iloc[-1]:.3f}",
               f"{series.iloc[-1] - series.iloc[0]:+.3f} over the period")

fig = px.line(rates, title="NOK per unit of currency")
fig.update_layout(xaxis_title="Date", yaxis_title="NOK", legend_title="Currency")
st.plotly_chart(fig)

with st.expander("About the data"):
    st.markdown("Rates are published on business days only; weekends and holidays "
                "have no value. On the forecast page they are averaged per week "
                "(weeks ending on Sunday, like NVE's reservoir statistics).")
