"""
Weather data from open-meteo for the Streamlit app.

The notebook (Task3.ipynb) samples 1000 points per region and stores them in
data/sample_points.csv. Here those points are snapped to the ERA5 grid, a small
random subset of grid cells is downloaded, and the hourly regional average is
returned.

download_weather_daily() gets daily values for many years at once (used for
the forecast and the map), and weekly_weather() turns them into the same weeks
as Magasinstatistikk.

The app uses fewer cells than the notebook: a live download must be quick, and
every visitor's request counts against open-meteo's free quota. Because the
weather varies smoothly across a region, a few well-spread cells give a regional
average close to the one from all cells.
"""

import time
from pathlib import Path

import pandas as pd
import requests

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Only the two variables the analysis pages use, to keep requests cheap
WEATHER_VARS = ["temperature_2m", "precipitation"]

# Hourly properties the user can choose between in the app (name -> label)
WEATHER_PROPERTIES = {
    "temperature_2m": "Temperature (°C)",
    "precipitation": "Precipitation (mm/h)",
    "snowfall": "Snowfall (cm/h)",
    "wind_speed_10m": "Wind speed (km/h)",
    "relative_humidity_2m": "Relative humidity (%)",
}

ERA5_GRID = 0.25   # ERA5 resolution in degrees

POINTS_FILE = Path(__file__).parent.parent / "data" / "sample_points.csv"


def load_points(path=POINTS_FILE):
    """The 1000 sampled points per region, made in the notebook."""
    return pd.read_csv(path)


def grid_cells(points, region_id, grid=ERA5_GRID):
    """
    Snap a region's points to the ERA5 grid and count the points in each cell.
    The API returns the nearest grid cell anyway, so each cell is downloaded
    once and weighted by how many points it stands for.
    """
    pts = points[points["region_id"] == region_id]
    snapped = pts.assign(lat=(pts["lat"] / grid).round() * grid,
                         lon=(pts["lon"] / grid).round() * grid)
    return (snapped.groupby(["lat", "lon"]).size()
                   .rename("n_points").reset_index())


class WeatherAPIError(RuntimeError):
    """open-meteo could not deliver the data (busy, rate limit or daily limit)."""


def _get_json(params, attempts=4):
    """
    One request with a simple retry. Busy-server and rate-limit answers
    (429, 5xx) and replies that arrive cut off are retried after a pause.
    When the daily limit is used up, retrying is pointless, so it stops at
    once with open-meteo's own explanation.
    """
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(ARCHIVE_URL, params=params, timeout=120)
            if response.status_code in (429, 500, 502, 503, 504):
                reason = ""
                try:
                    reason = response.json().get("reason", "")
                except ValueError:
                    pass
                if "daily" in reason.lower():
                    raise WeatherAPIError(reason)
                raise requests.HTTPError(f"HTTP {response.status_code} {reason}")
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as err:
            if attempt == attempts:
                raise WeatherAPIError(f"open-meteo did not answer: {err}") from err
            time.sleep(10 * attempt)


def download_weather(region_id, start, end, n_cells=20, variables=WEATHER_VARS,
                     batch_size=10, seed=1):
    """
    Download hourly ERA5 data for a region and return the regional average.

    region_id  : "NO1".."NO5", "VASS1".."VASS3" or "NO"
    start, end : "YYYY-MM-DD"
    n_cells    : number of randomly chosen ERA5 grid cells to download
    batch_size : grid cells per request
    seed       : makes the random subset the same every time
    """
    cells = grid_cells(load_points(), region_id)
    if n_cells is not None and n_cells < len(cells):
        cells = cells.sample(n_cells, random_state=seed).reset_index(drop=True)

    frames = []
    for i in range(0, len(cells), batch_size):
        batch = cells.iloc[i:i + batch_size]
        result = _get_json({
            "latitude": ",".join(batch["lat"].astype(str)),
            "longitude": ",".join(batch["lon"].astype(str)),
            "start_date": start,
            "end_date": end,
            "hourly": ",".join(variables),
            "models": "era5",        # ERA5 only, not the default model blend
            "timezone": "UTC",
        })
        if isinstance(result, dict):   # one location returns an object
            result = [result]
        for location, n in zip(result, batch["n_points"]):
            df = pd.DataFrame(location["hourly"])
            df["weight"] = n
            frames.append(df)

    hourly = pd.concat(frames, ignore_index=True)
    hourly["time"] = pd.to_datetime(hourly["time"])

    # Weighted average over the cells for each hour
    weighted = hourly[variables].mul(hourly["weight"], axis=0)
    weighted["weight"] = hourly["weight"]
    weighted["time"] = hourly["time"]
    sums = weighted.groupby("time").sum()
    return sums[variables].div(sums["weight"], axis=0)


# ---- Daily data for long periods (Part 4) ---------------------------------
# Daily values are enough for weekly analysis and the replies are 24 times
# smaller than hourly ones, which avoids the cut-off replies and timeouts
# seen in Part 3.
DAILY_VARS = ["temperature_2m_mean", "precipitation_sum", "snowfall_sum",
              "wind_speed_10m_max"]


def download_weather_daily(region_id, start, end, n_cells=10,
                           variables=DAILY_VARS, seed=1, pause=12):
    """
    Download daily ERA5 data for a region, one year per request, and return
    the regional (weighted) daily average.

    The days follow Norwegian time (timezone Europe/Oslo), so a day here is
    the same day as in Magasinstatistikk and Norges Bank.
    pause : seconds between requests, to stay under the per-minute limit
    """
    cells = grid_cells(load_points(), region_id)
    if n_cells is not None and n_cells < len(cells):
        cells = cells.sample(n_cells, random_state=seed).reset_index(drop=True)

    years = pd.period_range(start, end, freq="Y")
    frames = []
    for k, year in enumerate(years):
        chunk_start = max(pd.Timestamp(start), year.start_time)
        chunk_end = min(pd.Timestamp(end), year.end_time.normalize())
        if k > 0:
            time.sleep(pause)
        result = _get_json({
            "latitude": ",".join(cells["lat"].astype(str)),
            "longitude": ",".join(cells["lon"].astype(str)),
            "start_date": chunk_start.strftime("%Y-%m-%d"),
            "end_date": chunk_end.strftime("%Y-%m-%d"),
            "daily": ",".join(variables),
            "models": "era5",
            "timezone": "Europe/Oslo",
        })
        if isinstance(result, dict):
            result = [result]
        for location, n in zip(result, cells["n_points"]):
            df = pd.DataFrame(location["daily"])
            df["weight"] = n
            frames.append(df)

    daily = pd.concat(frames, ignore_index=True)
    daily["time"] = pd.to_datetime(daily["time"])

    # Weighted average over the cells for each day. Missing values (the
    # newest days are not in ERA5 yet) are left out of the average.
    values = daily[variables]
    weights = values.notna().mul(daily["weight"], axis=0)
    sums = values.fillna(0).mul(daily["weight"], axis=0).groupby(daily["time"]).sum()
    total_weight = weights.groupby(daily["time"]).sum()
    return (sums / total_weight.where(total_weight > 0)).dropna(how="all")


def weekly_weather(daily):
    """
    Daily weather -> weeks ending on Sunday, like Magasinstatistikk.
    Temperature and wind are averaged, precipitation and snowfall are summed.
    Weeks with fewer than 7 days of data (the newest one) are dropped.
    """
    weekly = pd.DataFrame({
        "temperature": daily["temperature_2m_mean"].resample("W-SUN").mean(),
        "precipitation": daily["precipitation_sum"].resample("W-SUN").sum(),
        "snowfall": daily["snowfall_sum"].resample("W-SUN").sum(),
        "wind_speed": daily["wind_speed_10m_max"].resample("W-SUN").mean(),
    })
    days = daily["temperature_2m_mean"].resample("W-SUN").count()
    return weekly[days == 7]
