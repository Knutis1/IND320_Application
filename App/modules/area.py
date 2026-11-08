"""
One area selector shared by all pages.

The choice is stored in st.session_state, so it is kept when the user moves
between pages: the reservoir page, the reservoir analysis and the weather
analysis all follow the same area. This is a global setting rather than one
selector per page, so the pages can never disagree about which area is shown.

The selector writes to its own session_state keys instead of giving the
widgets a key, because Streamlit removes widget keys when the user moves to a
page where that widget is not drawn.
"""

import streamlit as st

# Area numbers available for each Magasinstatistikk area type
AREA_NUMBERS = {"EL": [1, 2, 3, 4, 5], "NO": [0], "VASS": [1, 2, 3]}

AREA_TYPE_NAMES = {"EL": "Price areas", "NO": "Norway total",
                   "VASS": "Watercourse areas"}


def area_label(area_type, area_number):
    """Readable name: EL 3 -> 'NO3', VASS 1 -> 'VASS1', NO 0 -> 'Norway'."""
    if area_type == "EL":
        return f"NO{area_number}"
    if area_type == "NO":
        return "Norway"
    return f"VASS{area_number}"


def region_id(area_type, area_number):
    """The region_id used in data/sample_points.csv for the weather download."""
    if area_type == "NO":
        return "NO"
    return area_label(area_type, area_number)


def area_selector():
    """
    Draw the area selector in the sidebar and return (area_type, area_number).
    Defaults to NO3, the area used in the notebook.
    """
    state = st.session_state
    state.setdefault("area_type", "EL")
    state.setdefault("area_number", 3)

    st.sidebar.subheader("Area")
    types = list(AREA_NUMBERS)
    area_type = st.sidebar.radio(
        "Area type", types,
        index=types.index(state["area_type"]),
        format_func=lambda t: f"{t} – {AREA_TYPE_NAMES[t]}",
    )

    numbers = AREA_NUMBERS[area_type]
    current = state["area_number"] if state["area_number"] in numbers else numbers[0]
    area_number = st.sidebar.selectbox(
        "Area", numbers,
        index=numbers.index(current),
        format_func=lambda n: area_label(area_type, n),
        disabled=len(numbers) == 1,
    )

    state["area_type"], state["area_number"] = area_type, area_number
    st.sidebar.caption("The chosen area is used on every page.")
    return area_type, area_number
