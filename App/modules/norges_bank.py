"""
Exchange rates from Norges Bank's open API (same function as in Task4.ipynb).
"""

from io import StringIO

import pandas as pd
import requests

# B = business days, SP = spot rate, NOK = quote currency.
# Several currencies can be asked for at once by joining them with "+".
NB_URL = "https://data.norges-bank.no/api/data/EXR/B.{currencies}.NOK.SP"


def download_exchange_rates(start, end, currencies=("EUR", "USD")):
    """
    Daily exchange rates (NOK per unit) from Norges Bank.

    start, end : "YYYY-MM-DD"
    Returns a DataFrame with one column per currency and the date as index.
    """
    params = {"format": "csv", "startPeriod": start, "endPeriod": end, "locale": "en"}
    url = NB_URL.format(currencies="+".join(currencies))
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    df = pd.read_csv(StringIO(response.text), sep=";")
    rates = df.pivot(index="TIME_PERIOD", columns="BASE_CUR", values="OBS_VALUE")
    rates.index = pd.to_datetime(rates.index)
    rates.index.name = "date"
    rates.columns.name = None
    return rates
