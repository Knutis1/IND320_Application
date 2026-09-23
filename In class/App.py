import random

import streamlit as st
 
if "value" not in st.session_state:
    st.session_state.value = None
if "presses" not in st.session_state:
    st.session_state.presses = 0
if "show_continue_dialog" not in st.session_state:
    st.session_state.show_continue_dialog = False

st.markdown(
    """
    <style>
    div.stButton > button {
        min-height: 4rem;
        font-size: 1.5rem;
        padding: 0.75rem 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.dialog("Continue?")
def ask_to_continue():
    st.write("The button has been pressed 20 times without reaching 1. Do you want to continue?")
    if st.button("Continue"):
        st.session_state.presses = 0
        st.session_state.show_continue_dialog = False
        st.rerun()
    if st.button("Stop"):
        st.session_state.presses = 0
        st.session_state.show_continue_dialog = False
        st.rerun()
 
label = "Start" if st.session_state.value is None else "Next"
 
if st.button(label):
    st.session_state.presses += 1
    if st.session_state.value is None:
        st.session_state.value = random.randint(1, 100)
    else:
        if st.session_state.value % 2 == 0:
            st.session_state.value = st.session_state.value // 2
        else:
            st.session_state.value = st.session_state.value * 3 + 1

    if st.session_state.value == 1:
        st.session_state.presses = 0
    elif st.session_state.presses >= 20:
        st.session_state.show_continue_dialog = True

if st.session_state.show_continue_dialog:
    ask_to_continue()
 
output = "Ready" if st.session_state.value is None else str(st.session_state.value)
st.write(output)

if st.session_state.value == 1:
    st.markdown("# 😊")
    st.subheader("Jippi")

