"""
Analysis functions shared by the Streamlit app.

The methods are the same as in notebooks/Task3.ipynb, where each one is
explained and tested. In Part 4 the plots were changed from matplotlib to
Plotly, so they are interactive (zoom, hover) and use the app's theme
(modules/theme.py). The app shows them with st.plotly_chart().
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.fft import dct, idct
from scipy.signal import spectrogram
from scipy.stats import median_abs_deviation
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.seasonal import STL

from modules.theme import HIGHLIGHT


def spc_outliers(series, cutoff_days=30, n_sigma=3.0, title="Temperature (°C)"):
    """
    Statistical Process Control on a high-pass filtered series.

    series      : hourly pandas Series with a time index (any weather property)
    cutoff_days : DCT frequency cut-off, given as a period in days.
                  Variation slower than this is removed (the seasonal part).
    n_sigma     : number of robust standard deviations to the boundaries

    Returns (figure, summary dict, DataFrame of the outliers).
    """
    x = series.to_numpy(dtype=float)
    n = len(x)

    # DCT coefficient k is a cosine with period 2n/k samples (hours here),
    # so the cut-off period in days gives the cut-off index like this:
    k_cut = int(round(2 * n / (cutoff_days * 24)))

    coeffs = dct(x, type=2, norm="ortho")
    low = coeffs.copy()
    low[k_cut:] = 0                              # keep only the slow coefficients
    seasonal = idct(low, type=2, norm="ortho")   # slow part, back in time domain
    satv = x - seasonal                          # high-pass: the fast variations

    # Robust statistics over the whole year: median and MAD instead of
    # mean and std, so the extreme hours don't widen their own threshold.
    # scale="normal" multiplies MAD by 1.4826 to make it comparable to a std.
    centre = np.median(satv)
    sigma = median_abs_deviation(satv, scale="normal")

    upper = seasonal + centre + n_sigma * sigma
    lower = seasonal + centre - n_sigma * sigma
    is_out = np.abs(satv - centre) > n_sigma * sigma

    # Plot the original series with the boundaries. SATV itself is not plotted.
    fig = go.Figure()
    fig.add_scatter(x=series.index, y=x, name=title, line=dict(width=1))
    fig.add_scatter(x=series.index, y=upper, name=f"SPC boundaries (±{n_sigma} robust σ)",
                    line=dict(color="black", width=1, dash="dash"))
    fig.add_scatter(x=series.index, y=lower, name="lower boundary", showlegend=False,
                    line=dict(color="black", width=1, dash="dash"))
    fig.add_scatter(x=series.index[is_out], y=x[is_out], name="Outliers",
                    mode="markers", marker=dict(color=HIGHLIGHT, size=5))
    fig.update_layout(title=f"{title}: SPC outliers (DCT cut-off {cutoff_days} days)",
                      xaxis_title="Time (UTC)", yaxis_title=title, hovermode="closest")

    outliers = pd.DataFrame({"value": x[is_out], "satv": satv[is_out]},
                            index=series.index[is_out])
    summary = {
        "n_hours": n,
        "n_outliers": int(is_out.sum()),
        "share_outliers_pct": round(100 * is_out.mean(), 2),
        "cutoff_days": cutoff_days,
        "dct_cutoff_index": k_cut,
        "n_sigma": n_sigma,
        "robust_sigma": round(sigma, 4),
    }
    return fig, summary, outliers


def lof_anomalies(series, contamination=0.01, n_neighbors=20,
                  title="Temperature (°C)"):
    """
    Anomaly detection with Local Outlier Factor.

    series        : hourly pandas Series with a time index
    contamination : expected proportion of anomalies (default 1 %)
    n_neighbors   : number of neighbours each point is compared with

    Returns (figure, summary dict, DataFrame of the anomalies).
    """
    values = series.to_numpy(dtype=float)

    # Features: position in time and value, scaled to the same range
    X = StandardScaler().fit_transform(
        np.column_stack([np.arange(len(values)), values]))

    lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    is_out = lof.fit_predict(X) == -1          # -1 marks an anomaly

    fig = go.Figure()
    fig.add_scatter(x=series.index, y=values, name=title, line=dict(width=1))
    fig.add_scatter(x=series.index[is_out], y=values[is_out], name="Anomalies (LOF)",
                    mode="markers", marker=dict(color=HIGHLIGHT, size=5))
    fig.update_layout(title=f"{title}: Local Outlier Factor anomalies "
                            f"(contamination {contamination:.1%})",
                      xaxis_title="Time (UTC)", yaxis_title=title, hovermode="closest")

    anomalies = pd.DataFrame({"value": values[is_out]},
                             index=series.index[is_out])
    summary = {
        "n_hours": len(values),
        "n_anomalies": int(is_out.sum()),
        "share_anomalies_pct": round(100 * is_out.mean(), 2),
        "contamination": contamination,
        "n_neighbors": n_neighbors,
        "min_anomaly": round(float(values[is_out].min()), 2),
        "max_anomaly": round(float(values[is_out].max()), 2),
    }
    return fig, summary, anomalies


def stl_decomposition(series, period=52, seasonal=13, trend=89, robust=True,
                      title="Filling level, NO3"):
    """
    STL decomposition of a weekly series.

    period   : length of the seasonal cycle in observations (52 weeks)
    seasonal : seasonal smoother window, odd number
    trend    : trend smoother window, odd number larger than period
    robust   : down-weight unusual observations

    Returns the figure.
    """
    # Regular weekly index (the data is published on Sundays); interpolate
    # any missing weeks, since STL needs evenly spaced observations
    s = series.asfreq("W-SUN").interpolate()

    result = STL(s, period=period, seasonal=seasonal, trend=trend,
                 robust=robust).fit()

    # One panel per component, sharing the time axis
    parts = {"Observed": s, "Trend": result.trend, "Seasonal": result.seasonal,
             "Residual": result.resid}
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.04,
                        subplot_titles=list(parts))
    for row, (name, values) in enumerate(parts.items(), start=1):
        if name == "Residual":
            fig.add_scatter(x=values.index, y=values, name=name, mode="markers",
                            marker=dict(size=3), row=row, col=1)
        else:
            fig.add_scatter(x=values.index, y=values, name=name, row=row, col=1)
    fig.update_layout(height=750, showlegend=False,
                      title=f"{title}: STL (seasonal={seasonal}, trend={trend}, "
                            f"robust={robust})")
    return fig


def spectrogram_plot(series, window_length=104, overlap=78,
                     title="Filling level, NO3"):
    """
    Spectrogram of a weekly series.

    window_length : weeks per window (default two years)
    overlap       : weeks shared by neighbouring windows, less than window_length

    Returns the figure.
    """
    if overlap >= window_length:
        raise ValueError("overlap must be smaller than window_length")

    s = series.asfreq("W-SUN").interpolate()

    # fs=52 samples per year, so frequencies come out in cycles per year;
    # detrend removes the slow drift inside each window
    freqs, t, power = spectrogram(s.to_numpy(), fs=52, nperseg=window_length,
                                  noverlap=overlap, detrend="linear")

    # t is in years from the start; convert to dates for the x-axis
    times = s.index[0] + pd.to_timedelta(t * 365.25, unit="D")

    fig = go.Figure(go.Heatmap(x=times, y=freqs, z=10 * np.log10(power + 1e-12),
                               colorscale="Viridis",
                               colorbar=dict(title="Power (dB)")))
    fig.update_layout(title=f"{title}: spectrogram (window {window_length} weeks, "
                            f"overlap {overlap})",
                      xaxis_title="Time", yaxis_title="Frequency (cycles per year)",
                      hovermode="closest")
    return fig


# ---- Sliding window correlation (Part 4) -----------------------------------
def sliding_window_correlation(weather, reservoir, window=26, lag=0):
    """
    Correlation between a weather series and a reservoir series in a window
    that slides through time.

    weather, reservoir : weekly Series on the same weeks
    window             : number of weeks in each window
    lag                : weeks the weather is moved forward. lag = 4 compares
                         the reservoir this week with the weather 4 weeks earlier,
                         i.e. it tests whether the weather "leads" the reservoir.

    Returns a DataFrame with the shifted weather, the reservoir series and the
    rolling correlation (the value is placed at the last week of each window).
    """
    data = pd.DataFrame({"weather": weather.shift(lag), "reservoir": reservoir}).dropna()
    data["correlation"] = data["weather"].rolling(window).corr(data["reservoir"])
    return data


def lag_scan(weather, reservoir, max_lag=26):
    """Correlation over the whole period for every lag from -max_lag to max_lag."""
    lags = range(-max_lag, max_lag + 1)
    return pd.Series([reservoir.corr(weather.shift(lag)) for lag in lags],
                     index=pd.Index(lags, name="lag (weeks)"), name="correlation")


def correlation_plot(data, weather_label, reservoir_label, window, lag):
    """
    Two panels sharing the time axis: the two series (each on its own axis),
    and the sliding window correlation below, coloured by sign.
    """
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        row_heights=[0.5, 0.5],
                        specs=[[{"secondary_y": True}], [{}]],
                        subplot_titles=[f"{weather_label} (moved {lag} weeks) and "
                                        f"{reservoir_label}",
                                        f"Correlation in a {window}-week window"])
    fig.add_scatter(x=data.index, y=data["reservoir"], name=reservoir_label, row=1, col=1)
    fig.add_scatter(x=data.index, y=data["weather"], name=weather_label, row=1, col=1,
                    secondary_y=True, line=dict(width=1))

    corr = data["correlation"]
    fig.add_scatter(x=corr.index, y=corr.clip(lower=0), name="positive correlation",
                    fill="tozeroy", line=dict(width=0), fillcolor="rgba(27,42,74,0.55)",
                    row=2, col=1)
    fig.add_scatter(x=corr.index, y=corr.clip(upper=0), name="negative correlation",
                    fill="tozeroy", line=dict(width=0), fillcolor="rgba(192,57,43,0.55)",
                    row=2, col=1)
    fig.add_hline(y=0, line=dict(color="black", width=1), row=2, col=1)
    fig.update_yaxes(title_text=reservoir_label, row=1, col=1)
    fig.update_yaxes(title_text=weather_label, secondary_y=True, row=1, col=1)
    fig.update_yaxes(title_text="correlation", range=[-1, 1], row=2, col=1)
    # Legend below the chart, so it does not cover the panel titles at the top
    fig.update_layout(height=720, hovermode="x unified",
                      title="Sliding window correlation",
                      legend=dict(orientation="h", y=-0.08, yanchor="top", x=0),
                      margin=dict(t=90, b=60))
    return fig
