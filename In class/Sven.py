import random
import streamlit as st

st.set_page_config(page_title="Dota 2 Randomizer", page_icon="⚔️", layout="centered")

if "value" not in st.session_state:
    st.session_state.value = None
if "slash_count" not in st.session_state:
    st.session_state.slash_count = 0

DOTA_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&family=Eczar:wght@500;700&display=swap');

.stApp {
    background: radial-gradient(circle at top, #1c1712 0%, #0b0906 60%, #050403 100%);
    color: #e8d9b5;
}

/* hide default streamlit chrome */
#MainMenu, header, footer {visibility: hidden;}

.dota-title {
    font-family: 'Cinzel', serif;
    font-weight: 800;
    text-align: center;
    font-size: 2.6rem;
    letter-spacing: 3px;
    background: linear-gradient(180deg, #ffcf6b 0%, #c8161d 55%, #7a0f14 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 18px rgba(200, 22, 29, 0.35);
    margin-bottom: 0.2rem;
}

.dota-subtitle {
    font-family: 'Eczar', serif;
    text-align: center;
    color: #a99569;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-size: 0.85rem;
    margin-bottom: 2rem;
}

.dota-panel {
    background: linear-gradient(160deg, #1a1510 0%, #100d09 100%);
    border: 2px solid #7a5c2e;
    border-radius: 10px;
    box-shadow: 0 0 0 1px #2a2115 inset, 0 8px 24px rgba(0,0,0,0.6);
    padding: 2.5rem 2rem;
    text-align: center;
    margin-bottom: 1.5rem;
}

.dota-output-label {
    font-family: 'Eczar', serif;
    color: #a99569;
    text-transform: uppercase;
    letter-spacing: 3px;
    font-size: 0.8rem;
    margin-bottom: 0.6rem;
}

.dota-output-value {
    font-family: 'Cinzel', serif;
    font-weight: 800;
    font-size: 3.2rem;
    color: #ffcf6b;
    text-shadow: 0 0 22px rgba(255, 207, 107, 0.45), 0 0 4px rgba(0,0,0,0.8);
}

div.stButton {
    display: flex;
    justify-content: center;
}

div.stButton > button {
    font-family: 'Cinzel', serif;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-size: 1.1rem;
    color: #ffe9b8;
    background: linear-gradient(180deg, #3a2412 0%, #1c1108 100%);
    border: 2px solid #c8161d;
    border-radius: 6px;
    padding: 0.75rem 3rem;
    box-shadow: 0 0 12px rgba(200, 22, 29, 0.4), inset 0 0 8px rgba(0,0,0,0.6);
    transition: all 0.15s ease-in-out;
}

div.stButton > button:hover {
    color: #fff3d6;
    border-color: #ffcf6b;
    box-shadow: 0 0 20px rgba(255, 207, 107, 0.6), inset 0 0 10px rgba(0,0,0,0.6);
    transform: translateY(-1px);
}

div.stButton > button:active {
    transform: translateY(1px);
}

.sven-stage {
    position: relative;
    height: 0;
    margin-top: -78px;
    margin-bottom: 40px;
    pointer-events: none;
    overflow: visible;
    z-index: 5;
}

.slash-flash {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 340px;
    height: 6px;
    background: linear-gradient(90deg, rgba(255,207,107,0) 0%, #fff8e0 15%, #ffcf6b 50%, #fff8e0 85%, rgba(255,207,107,0) 100%);
    box-shadow: 0 0 14px 3px rgba(255,207,107,0.9);
    transform: translate(-50%, -50%) rotate(-18deg) scaleX(0);
    transform-origin: center;
    animation: slash-swipe 0.45s ease-out forwards;
    animation-delay: 0.18s;
    border-radius: 3px;
}

@keyframes slash-swipe {
    0%   { transform: translate(-50%, -50%) rotate(-18deg) scaleX(0);   opacity: 0; }
    12%  { opacity: 1; }
    55%  { transform: translate(-50%, -50%) rotate(-18deg) scaleX(1);   opacity: 1; }
    100% { transform: translate(-50%, -50%) rotate(-18deg) scaleX(1);   opacity: 0; }
}

.sven-warrior {
    position: absolute;
    top: -34px;
    left: -70px;
    width: 90px;
    height: 110px;
    animation: sven-charge 0.5s cubic-bezier(.3,.1,.4,1) forwards;
    filter: drop-shadow(0 0 6px rgba(255, 207, 107, 0.6));
}

@keyframes sven-charge {
    0%   { transform: translateX(0) translateY(0) rotate(0deg);   opacity: 0; }
    10%  { opacity: 1; }
    50%  { transform: translateX(220px) translateY(-6px) rotate(-8deg); opacity: 1; }
    75%  { transform: translateX(400px) translateY(2px) rotate(4deg); opacity: 1; }
    100% { transform: translateX(560px) translateY(0) rotate(0deg);  opacity: 0; }
}
</style>
"""

st.markdown(DOTA_CSS, unsafe_allow_html=True)

st.markdown('<div class="dota-title">Roshan\'s Bounty</div>', unsafe_allow_html=True)
st.markdown('<div class="dota-subtitle">The Ancients Reveal Your Fate</div>', unsafe_allow_html=True)

label = "Start" if st.session_state.value is None else "Next"

clicked = st.button(label)

if clicked:
    if st.session_state.value is None:
        st.session_state.value = random.randint(1, 100)
    else:
        if st.session_state.value % 2 == 0:
            st.session_state.value = st.session_state.value // 2
        else:
            st.session_state.value = st.session_state.value * 3 + 1
    st.session_state.slash_count += 1

if clicked:
    # Unique key in the animation forces the browser to replay it every press
    warrior_svg = """
    <svg viewBox="0 0 90 110" xmlns="http://www.w3.org/2000/svg">
        <g stroke="#e8d9b5" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
            <!-- legs -->
            <path d="M40 70 L30 105" />
            <path d="M50 70 L64 100" />
            <!-- torso -->
            <path d="M38 40 L52 40 L50 70 L40 70 Z" fill="#3a2412" />
            <!-- head -->
            <circle cx="45" cy="28" r="11" fill="#c9aa71" stroke="#7a5c2e" />
            <!-- trailing arm -->
            <path d="M38 45 L18 55" />
            <!-- sword arm, blade forward -->
            <path d="M52 42 L78 30" stroke="#a99569" stroke-width="4" />
            <path d="M78 30 L96 22" stroke="#ffe9b8" stroke-width="4" />
        </g>
    </svg>
    """
    st.markdown(
        f"""
        <div class="sven-stage" data-slash="{st.session_state.slash_count}">
            <div class="slash-flash"></div>
            <div class="sven-warrior">{warrior_svg}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

output = "Ready" if st.session_state.value is None else str(st.session_state.value)

st.markdown(
    f"""
    <div class="dota-panel">
        <div class="dota-output-label">Aegis Reading</div>
        <div class="dota-output-value">{output}</div>
    </div>
    """,
    unsafe_allow_html=True,
)