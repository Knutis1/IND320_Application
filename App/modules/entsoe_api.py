"""
Connection to the ENTSO-E Transparency Platform.
Downloads physical cross-border flows between Norwegian bidding zones
and their neighbours.
"""

import os

import pandas as pd
from dotenv import load_dotenv
from entsoe import EntsoePandasClient

load_dotenv()  # reads the .env file at the project root

# The connections we use. Each entry is (Norwegian zone, neighbour zone).
# Flow is physical, so each connection needs TWO queries, one per direction.
CONNECTIONS = {
    "NO2-DK1": ("NO_2", "DK_1"),   # Skagerrak
    "NO2-NL":  ("NO_2", "NL"),     # NorNed
    "NO1-SE3": ("NO_1", "SE_3"),   # to Sweden
}


def get_client():
    """Create an ENTSO-E client using the token from .env."""
    token = os.environ.get("ENTSOE_TOKEN")
    if not token:
        raise RuntimeError("ENTSOE_TOKEN missing - check the .env file")
    return EntsoePandasClient(api_key=token)


def fetch_connection(client, name, start, end):
    """
    Download both directions for one connection and return a long DataFrame
    with the columns: connection, direction, ts, flow_mw.

    Timestamps are converted to UTC and then made naive, so that Cassandra,
    Spark and MongoDB all store the same instant without timezone confusion.
    (This is the lesson from the date columns in Part 1.)
    """
    zone_no, zone_other = CONNECTIONS[name]
    frames = []

    for direction, (a, b) in {
        "export": (zone_no, zone_other),   # out of Norway
        "import": (zone_other, zone_no),   # into Norway
    }.items():
        series = client.query_crossborder_flows(a, b, start=start, end=end)
        df = series.rename("flow_mw").to_frame()
        df.index.name = "ts"
        df = df.reset_index()
        df["ts"] = pd.to_datetime(df["ts"], utc=True).dt.tz_localize(None)
        df["connection"] = name
        df["direction"] = direction
        frames.append(df[["connection", "direction", "ts", "flow_mw"]])

    return pd.concat(frames, ignore_index=True)


def fetch_all(years=2):
    """
    Download every connection for the last N years, one year at a time
    (a single two-year request often times out on the ENTSO-E side).
    """
    client = get_client()
    end = pd.Timestamp.now(tz="Europe/Oslo").normalize()
    all_frames = []

    for year_offset in range(years, 0, -1):
        chunk_start = end - pd.DateOffset(years=year_offset)
        chunk_end = end - pd.DateOffset(years=year_offset - 1)
        for name in CONNECTIONS:
            try:
                df = fetch_connection(client, name, chunk_start, chunk_end)
                all_frames.append(df)
                print(f"{name} {chunk_start.date()} to {chunk_end.date()}: {len(df)} rows")
            except Exception as exc:
                # Some borders have gaps; keep going rather than losing everything
                print(f"{name} {chunk_start.date()}: FAILED - {exc}")

    return pd.concat(all_frames, ignore_index=True)