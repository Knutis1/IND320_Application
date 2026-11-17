"""
Shared look for the app: colours, the Plotly template and the coloured group
header at the top of each page.

The colours match .streamlit/config.toml, so the Streamlit widgets and the
Plotly charts look like one app.
"""

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

NAVY = "#1B2A4A"        # same as primaryColor/textColor in config.toml
BEIGE = "#EFE6D2"       # same as secondaryBackgroundColor (sidebar)
PRIMARY = NAVY
TEXT = NAVY
GRID = "#E6DCC6"        # light beige grid lines

# One colour per page group, so it is easy to see which group is active
GROUP_COLOURS = {
    "Overview": NAVY,
    "Reservoirs": "#2D5D8A",
    "Weather": "#3D7A5C",
    "Power & economy": "#B07A3B",
    "About": NAVY,
}

# Colours for lines and areas in the charts: navy and a darker beige first,
# then colours that are easy to tell apart on a white background
COLOURWAY = ["#1B2A4A", "#B08D57", "#4F86C6", "#3D7A5C", "#8E5B9F",
             "#D08C60", "#6C7A89", "#C9A227"]
HIGHLIGHT = "#C0392B"   # outliers, anomalies and forecasts

pio.templates["ind320"] = go.layout.Template(
    layout=go.Layout(
        colorway=COLOURWAY,
        font=dict(family="sans-serif", color=TEXT, size=13),
        paper_bgcolor="rgba(0,0,0,0)",       # transparent: the app background shows
        plot_bgcolor="rgba(255,255,255,0.6)",
        xaxis=dict(gridcolor=GRID, zeroline=False),
        yaxis=dict(gridcolor=GRID, zeroline=False),
        # Title at the very top, the legend in its own row below it and
        # above the plot, so the two never overlap
        title=dict(x=0, xanchor="left", y=0.98, yanchor="top", yref="container",
                   font=dict(size=17)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    title=dict(side="left")),
        margin=dict(l=10, r=10, t=110, b=10),
        hovermode="x unified",
    )
)
pio.templates.default = "plotly_white+ind320"   # used by every Plotly figure


def page_header(title, group, caption=None):
    """Title with a small coloured label showing which group the page belongs to."""
    colour = GROUP_COLOURS.get(group, PRIMARY)
    st.markdown(
        f"<span style='background:{colour};color:white;padding:2px 10px;"
        f"border-radius:10px;font-size:0.8rem'>{group}</span>",
        unsafe_allow_html=True)
    st.title(title)
    if caption:
        st.caption(caption)
