"""
Analysis functions for Part 3, shared by the Streamlit app.

These are the same functions as in notebooks/Task3.ipynb, where each method is
explained and tested. They return matplotlib figures, which the app shows with
st.pyplot().
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.fft import dct, idct
from scipy.signal import spectrogram
from scipy.stats import median_abs_deviation
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.seasonal import STL


def spc_outliers(series, cutoff_days=30, n_sigma=3.0, title="Precipitation"):
    """
    Statistical Process Control on a high-pass filtered series.

    series      : hourly pandas Series with a time index
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
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(series.index, x, color="steelblue", linewidth=0.6, label=title)
    ax.plot(series.index, upper, color="black", linestyle="--", linewidth=1,
            label=f"SPC boundaries (±{n_sigma} robust σ)")
    ax.plot(series.index, lower, color="black", linestyle="--", linewidth=1)
    ax.scatter(series.index[is_out], x[is_out], color="crimson", s=10,
               zorder=3, label="Outliers")
    ax.set_title(f"{title}: SPC outliers (DCT cut-off {cutoff_days} days)")
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel(title)
    ax.legend(loc="upper right")
    ax.grid(alpha=0.3)

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

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(series.index, values, color="steelblue", linewidth=0.6, label=title)
    ax.scatter(series.index[is_out], values[is_out], color="crimson", s=10,
               zorder=3, label="Anomalies (LOF)")
    ax.set_title(f"{title}: Local Outlier Factor anomalies "
                 f"(contamination {contamination:.0%})")
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel(title)
    ax.legend(loc="upper right")
    ax.grid(alpha=0.3)

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

    fig = result.plot()
    fig.set_size_inches(12, 8)
    fig.suptitle(f"{title}: STL (seasonal={seasonal}, trend={trend}, "
                 f"robust={robust})", y=1.02)
    fig.tight_layout()
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

    fig, ax = plt.subplots(figsize=(12, 5))
    mesh = ax.pcolormesh(times, freqs, 10 * np.log10(power + 1e-12),
                         shading="auto")
    fig.colorbar(mesh, ax=ax, label="Power (dB)")
    ax.set_title(f"{title}: spectrogram (window {window_length} weeks, "
                 f"overlap {overlap})")
    ax.set_xlabel("Time")
    ax.set_ylabel("Frequency (cycles per year)")
    return fig
