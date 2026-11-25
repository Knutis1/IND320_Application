"""
Forecasting the weekly reservoir filling level with River's SNARIMAX
(seasonal ARIMA with exogenous variables, trained one week at a time).

Used both by the notebook (Task4.ipynb) and the Streamlit forecast page,
so the two always run the same model.

Time resolution: weekly. Magasinstatistikk only has one value per week, so
a finer resolution would only add interpolated values and make the model
slower without adding information. All other sources are therefore
aggregated to the same weeks (ending on Sunday, like dato_Id).
"""

import numpy as np
import pandas as pd
from river import linear_model, optim, preprocessing, time_series

WEEKS_PER_YEAR = 52

# Exogenous columns that follow the calendar (weather). Their future values are
# unknown, so they are replaced by the average for the same week in earlier years.
# Other columns (exchange rates) keep their last known value.
CURRENCY_COLUMNS = ["EUR", "USD"]

# The best settings from the tests in Task4.ipynb (used as defaults in Streamlit)
DEFAULTS = dict(history_years=15, p=1, d=0, q=0, sp=1, sd=1, sq=0,
                learning_rate=0.01)

# The exogenous variables that gave the best forecasts in the tests
DEFAULT_EXOG = ["temperature", "snowfall"]


def to_weekly(series, utc=True, how="mean"):
    """
    Hourly or daily data -> weekly values on the same weeks as Magasinstatistikk.
    utc=True: naive UTC timestamps are converted to Norwegian time first.
    Weeks end on Sunday (W-SUN), the same day as the dates in Magasinstatistikk.
    """
    s = series.copy()
    if utc:
        s.index = (s.index.tz_localize("UTC").tz_convert("Europe/Oslo")
                           .tz_localize(None))
    return s.resample("W-SUN").agg(how)


def _week_of_year(index):
    """ISO week number, with week 53 treated as week 52."""
    return np.minimum(index.isocalendar().week.to_numpy(), WEEKS_PER_YEAR)


def fill_gaps(exog):
    """
    Fill missing values so River never gets a NaN:
    weather by the average for that week of the year, currencies by the
    last (or first) known value.
    """
    exog = exog.copy()
    weeks = _week_of_year(exog.index)
    for col in exog.columns:
        if col in CURRENCY_COLUMNS:
            exog[col] = exog[col].ffill().bfill()
        else:
            climate = exog[col].groupby(weeks).transform("mean")
            exog[col] = exog[col].fillna(climate).ffill().bfill()
    return exog


def future_exog(exog, horizon):
    """
    Values of the exogenous variables for the coming weeks, which are not known
    yet: weather = average for the same week in the training years,
    currencies = last known value.
    """
    future_index = pd.date_range(exog.index[-1] + pd.Timedelta(weeks=1),
                                 periods=horizon, freq="W-SUN")
    weeks = _week_of_year(exog.index)
    future_weeks = _week_of_year(future_index)
    future = pd.DataFrame(index=future_index)
    for col in exog.columns:
        if col in CURRENCY_COLUMNS:
            future[col] = exog[col].iloc[-1]
        else:
            climate = exog[col].groupby(weeks).mean()
            future[col] = climate.reindex(future_weeks).to_numpy()
    return future


def make_model(p=1, d=0, q=0, sp=1, sd=1, sq=0, learning_rate=0.01, quantile=None):
    """
    SNARIMAX with a 52-week season. The regressor is a linear model trained
    with stochastic gradient descent; the scaler puts all inputs on the same
    scale so one learning rate works for all of them.

    quantile : None for the normal forecast (squared loss). A number such as
               0.05 or 0.95 trains the model with the quantile (pinball) loss
               instead, so it predicts that quantile. Two such models give a
               confidence interval around the forecast.
    """
    loss = optim.losses.Squared() if quantile is None else optim.losses.Quantile(alpha=quantile)
    regressor = (preprocessing.StandardScaler()
                 | linear_model.LinearRegression(intercept_init=0, loss=loss,
                                                 optimizer=optim.SGD(learning_rate),
                                                 intercept_lr=learning_rate))
    return time_series.SNARIMAX(p=p, d=d, q=q, m=WEEKS_PER_YEAR,
                                sp=sp, sd=sd, sq=sq, regressor=regressor)


def forecast_filling(fill, exog=None, exog_columns=None, history_years=15,
                     horizon=12, end=None, p=1, d=0, q=0, sp=1, sd=1, sq=0,
                     learning_rate=0.01, quantile=None):
    """
    Forecast the weekly filling level for one area.

    fill          : weekly filling level (Series, date index), one area
    exog          : weekly exogenous variables (DataFrame on the same weeks) or None
    exog_columns  : which columns of exog to use (the data source selection);
                    None = all, [] = none
    history_years : years of history used for training
    horizon       : number of weeks to forecast
    end           : last week used for training (None = newest week).
                    Setting it earlier lets the forecast be compared with what
                    actually happened.
    p, d, q       : non-seasonal AR order, differencing, MA order
    sp, sd, sq    : the same for the 52-week season
    learning_rate : step size of the regressor
    quantile      : None for the normal forecast, or e.g. 0.05 / 0.95 for the
                    lower / upper limit of a confidence interval

    Returns a Series with the forecast, indexed by the coming weeks.
    """
    fill = fill.asfreq("W-SUN").interpolate()        # regular weeks, no gaps
    if end is not None:
        fill = fill[:end]
    train = fill.iloc[-history_years * WEEKS_PER_YEAR:]

    x_train = None
    if exog is not None:
        columns = list(exog.columns) if exog_columns is None else list(exog_columns)
        if columns:
            x_train = fill_gaps(exog[columns].reindex(fill.index)).loc[train.index]

    model = make_model(p, d, q, sp, sd, sq, learning_rate, quantile)
    for t, y in train.items():                        # online learning, week by week
        x = None if x_train is None else x_train.loc[t].to_dict()
        model.learn_one(y, x=x)

    xs = None
    if x_train is not None:
        xs = future_exog(x_train, horizon).to_dict("records")

    # Dynamic forecast: each step uses the model's own earlier predictions
    values = np.clip(model.forecast(horizon=horizon, xs=xs), 0, 1)
    index = pd.date_range(train.index[-1] + pd.Timedelta(weeks=1),
                          periods=horizon, freq="W-SUN")
    return pd.Series(values, index=index, name="forecast")


def backtest(fill, origins, horizon=12, **settings):
    """
    Mean absolute error of the forecast over several start weeks (origins).
    For each origin the model is trained on data up to that week only, and
    the forecast is compared with the weeks that followed.
    """
    fill = fill.asfreq("W-SUN").interpolate()
    errors = []
    for origin in origins:
        origin = fill.index[fill.index <= origin][-1]
        pred = forecast_filling(fill, end=origin, horizon=horizon, **settings)
        actual = fill.reindex(pred.index)
        errors.append((pred - actual).abs().mean())
    return float(np.mean(errors))
