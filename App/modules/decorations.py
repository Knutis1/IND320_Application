"""
Animated decorations for some of the pages (pure HTML/CSS, no images).

Each function adds one decoration with st.html. The CSS is only on the page
that calls the function, so it disappears when the user moves to another page.
All decorations ignore the mouse (pointer-events: none) and sit behind or
beside the content, so they never block buttons or charts.
"""

import random
from urllib.parse import quote

import streamlit as st

def _page_css(css):
    """
    CSS that must reach Streamlit's own elements (the main area and its
    padding). st.html keeps its CSS inside its own block, so this goes through
    st.markdown instead.
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def money_rain(seed=4):
    """
    Banknotes falling slowly in the background of the page. The notes are
    drawn in two SVG tiles used as background images of the main area, so
    they always stay behind the text and charts. The two tiles have different
    sizes and move the length of one tile in the same time, so they fall at
    different speeds, which gives some depth.
    """
    rng = random.Random(seed)

    def tile(size, n):
        notes = ""
        for _ in range(n):
            # Keep each note away from the tile edges, so none is cut in half
            x, y = rng.uniform(30, size - 80), rng.uniform(70, size - 50)
            notes += (f"<text x='{x:.0f}' y='{y:.0f}' font-size='{rng.uniform(26, 38):.0f}' "
                      f"transform='rotate({rng.uniform(-20, 20):.0f} {x + 20:.0f} {y - 15:.0f})'>"
                      f"{rng.choice(['💵', '💶', '💷', '💴'])}</text>")
        svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}'>"
               f"<g opacity='0.35'>{notes}</g></svg>")
        return f'url("data:image/svg+xml;utf8,{quote(svg)}")'

    _page_css(f"""
[data-testid="stMain"] {{
    background-image: {tile(260, 3)}, {tile(380, 3)};
    background-size: 260px 260px, 380px 380px;
    animation: money-fall 14s linear infinite;
}}
@keyframes money-fall {{
    from {{ background-position: 0 0, 120px 0; }}
    to   {{ background-position: 0 260px, 120px 380px; }}
}}
""")


def power_lines():
    """A banner at the top of the page with power lines that carry 'current'."""
    # The drawing is an SVG used as a background image (st.html removes inline
    # SVG). Each wire hangs between the poles (a curve); the yellow dashes moving
    # along the same curves look like electricity flowing through them.
    wires = ""
    for i, y in enumerate([40, 64, 88]):
        path = f"M0,{y} Q150,{y + 34} 300,{y} T600,{y} T900,{y} T1200,{y}"
        wires += (f"<path d='{path}' class='wire'/>"
                  f"<path d='{path}' class='current' style='animation-delay:-{i * 0.7}s'/>")
    poles = "".join(f"<rect x='{x - 4}' y='22' width='8' height='110' class='pole'/>"
                    f"<rect x='{x - 30}' y='28' width='60' height='6' class='pole'/>"
                    for x in (300, 600, 900))
    sparks = "".join(f"<path d='M{x},6 l-8,14 h7 l-5,12 l13,-17 h-7 l5,-9 z' class='spark' "
                     f"style='animation-delay:-{d}s'/>" for x, d in ((300, 0), (900, 0.6)))
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 130' "
        "preserveAspectRatio='none'>"
        "<style>"
        ".pole{fill:#8A7353}"
        ".wire{fill:none;stroke:#0E1628;stroke-width:4}"
        ".current{fill:none;stroke:#FFE45C;stroke-width:3;stroke-dasharray:18 70;"
        "filter:url(#glow);animation:flow 1.6s linear infinite}"
        ".spark{fill:#FFE45C;animation:blink 1.2s infinite}"
        "@keyframes flow{to{stroke-dashoffset:-176}}"
        "@keyframes blink{0%,70%,100%{opacity:0}80%{opacity:1}}"
        "</style>"
        "<defs><filter id='glow'><feGaussianBlur stdDeviation='2.5' result='b'/>"
        "<feMerge><feMergeNode in='b'/><feMergeNode in='SourceGraphic'/></feMerge>"
        f"</filter></defs>{poles}{wires}{sparks}</svg>")
    st.html(f"""
<style>
.power-banner {{ width: 100%; height: 130px; pointer-events: none; margin-bottom: 4px;
                 border-radius: 12px; overflow: hidden;
                 background: url("data:image/svg+xml;utf8,{quote(svg)}") center / 100% 100% no-repeat,
                             linear-gradient(180deg, #1B2A4A 0%, #2D3E63 100%); }}
</style>
<div class="power-banner"></div>
""")


def sun():
    """A glowing sun with slowly turning rays in the top right corner."""
    st.html("""
<style>
.sun-corner { position: relative; height: 0; pointer-events: none; }
.sun-corner .sun { position: absolute; right: 10px; top: -30px; width: 110px; height: 110px; }
.sun-corner .rays { position: absolute; inset: -38px; border-radius: 50%;
    background: repeating-conic-gradient(rgba(255, 196, 0, 0.55) 0deg 8deg,
                                         transparent 8deg 24deg);
    -webkit-mask: radial-gradient(circle, transparent 52%, black 54%, transparent 72%);
            mask: radial-gradient(circle, transparent 52%, black 54%, transparent 72%);
    animation: sun-turn 30s linear infinite; }
.sun-corner .disc { position: absolute; inset: 0; border-radius: 50%;
    background: radial-gradient(circle at 40% 40%, #FFF3A6, #FFC400 55%, #FF9F1C);
    box-shadow: 0 0 40px 12px rgba(255, 190, 40, 0.55);
    animation: sun-glow 4s ease-in-out infinite alternate; }
@keyframes sun-turn { to { transform: rotate(360deg); } }
@keyframes sun-glow { to { box-shadow: 0 0 60px 22px rgba(255, 190, 40, 0.75); } }
</style>
<div class="sun-corner"><div class="sun"><div class="rays"></div><div class="disc"></div></div></div>
""")


def rain_and_snow(seed=7):
    """A banner at the top: rain clouds on the left half, snowfall on the right."""
    rng = random.Random(seed)
    drops = "".join(
        f"<i class='drop' style='left:{rng.uniform(2, 48):.1f}%;"
        f"animation-duration:{rng.uniform(0.6, 1.1):.2f}s;"
        f"animation-delay:-{rng.uniform(0, 1):.2f}s'></i>" for _ in range(45))
    flakes = "".join(
        f"<i class='flake' style='left:{rng.uniform(52, 98):.1f}%;"
        f"font-size:{rng.uniform(10, 20):.0f}px;"
        f"animation-duration:{rng.uniform(4, 8):.1f}s;"
        f"animation-delay:-{rng.uniform(0, 8):.1f}s'>❄</i>" for _ in range(35))
    clouds = "".join(
        f"<span class='cloud' style='left:{x}%;top:{top}px;font-size:{size}px;"
        f"filter:{'brightness(0.55)' if x < 50 else 'none'}'>☁️</span>"
        for x, top, size in [(-2, -18, 78), (12, -26, 92), (28, -20, 84), (40, -24, 70),
                             (52, -22, 80), (66, -28, 94), (82, -20, 84), (93, -24, 70)])
    st.html(f"""
<style>
.weather-banner {{ position: relative; width: 100%; height: 150px; overflow: hidden;
                   pointer-events: none; border-radius: 12px; margin-bottom: 4px;
                   background: linear-gradient(90deg, #5E6B7D 0%, #8592A3 49.5%,
                                               #DCE6F0 50.5%, #F4F8FB 100%); }}
.weather-banner .cloud {{ position: absolute; z-index: 2; line-height: 1;
                          animation: cloud-drift 9s ease-in-out infinite alternate; }}
.weather-banner .drop {{ position: absolute; top: -20px; width: 2px; height: 16px;
                         background: linear-gradient(transparent, #BFD7F2);
                         animation: rain-fall linear infinite; }}
.weather-banner .flake {{ position: absolute; top: -20px; color: white; font-style: normal;
                          text-shadow: 0 0 3px #9DB4CC;
                          animation: snow-fall linear infinite; }}
@keyframes rain-fall {{ to {{ transform: translateY(190px); }} }}
@keyframes snow-fall {{ 0% {{ transform: translate(0, 0) rotate(0deg); }}
                        50% {{ transform: translate(12px, 90px) rotate(180deg); }}
                        100% {{ transform: translate(-6px, 180px) rotate(360deg); }} }}
@keyframes cloud-drift {{ to {{ transform: translateX(14px); }} }}
</style>
<div class="weather-banner">{clouds}{drops}{flakes}</div>
""")


def waterfalls(width=70):
    """
    Water running down both sides of the page, in the empty space beside the
    content. The content is narrowed a little so there is room for the water.
    """
    # A tile of water: blue with lighter streaks. Moving the background
    # downwards makes the water look like it is falling.
    tile = ("data:image/svg+xml;utf8,"
            "<svg xmlns='http://www.w3.org/2000/svg' width='90' height='160'>"
            "<rect width='90' height='160' fill='%232D5D8A'/>"
            "<path d='M10 0 v60 M28 30 v80 M46 10 v50 M64 50 v90 M80 0 v40 "
            "M18 100 v60 M38 120 v40 M56 0 v25 M72 110 v50' "
            "stroke='%23A9CBEA' stroke-width='3' stroke-linecap='round' opacity='0.8'/>"
            "<path d='M4 70 v30 M52 75 v30 M86 60 v45' stroke='white' stroke-width='2' "
            "stroke-linecap='round' opacity='0.6'/></svg>")
    _page_css(f"""
[data-testid="stMain"] {{
    background-image: url("{tile}"), url("{tile}");
    background-repeat: repeat-y, repeat-y;
    background-size: {width}px 160px, {width}px 160px;
    background-position: left 0 top 0, right 0 top 0;
    animation: water-fall 1.2s linear infinite;
}}
[data-testid="stMainBlockContainer"] {{
    padding-left: {width + 60}px !important; padding-right: {width + 60}px !important;
}}
@keyframes water-fall {{
    to {{ background-position: left 0 top 160px, right 0 top 160px; }}
}}
""")


def _svg_url(svg):
    """An SVG drawing as a CSS background url (animations inside the SVG still run)."""
    return f'url("data:image/svg+xml;utf8,{quote(svg)}")'


def weather_friends():
    """
    Four small weather figures (sun, rain cloud, snow cloud and wind) floating
    in the empty space on both sides of the page, so they never cover the
    content. Each one bobs gently up and down.
    """
    face = ("<circle cx='-9' cy='-2' r='3.2' fill='#1B2A4A'/>"
            "<circle cx='9' cy='-2' r='3.2' fill='#1B2A4A'/>"
            "<path d='M-7,8 Q0,14 7,8' stroke='#1B2A4A' stroke-width='2.5' fill='none' "
            "stroke-linecap='round'/>")
    cloud = ("<g fill='{c}' stroke='#1B2A4A' stroke-width='2'>"
             "<circle cx='-22' cy='8' r='18'/><circle cx='0' cy='-6' r='24'/>"
             "<circle cx='24' cy='6' r='19'/><rect x='-40' y='6' width='82' height='22' rx='11'/>"
             "</g><rect x='-38' y='8' width='78' height='18' fill='{c}'/>")
    sun = ("<g class='bob'><g class='spin'>"
           + "".join(f"<rect x='-4' y='-52' width='8' height='16' rx='4' fill='#F4A300' "
                     f"transform='rotate({a})'/>" for a in range(0, 360, 45))
           + "</g><circle r='30' fill='#FFC93C' stroke='#1B2A4A' stroke-width='2'/>"
           + face + "</g>")
    rain = ("<g class='bob' style='animation-delay:-1s'>" + cloud.format(c="#9DB4CC")
            + "".join(f"<path class='drop' d='M{x},34 v10' stroke='#2D5D8A' stroke-width='3' "
                      f"stroke-linecap='round' style='animation-delay:-{d}s'/>"
                      for x, d in ((-22, 0), (-4, 0.4), (14, 0.2), (30, 0.6)))
            + "<g transform='translate(0,6)'>" + face + "</g></g>")
    snow = ("<g class='bob' style='animation-delay:-2s'>" + cloud.format(c="#F4F8FB")
            + "".join(f"<text class='flake' x='{x}' y='44' font-size='14' fill='#7FA7CF' "
                      f"style='animation-delay:-{d}s'>✻</text>"
                      for x, d in ((-26, 0), (-6, 0.9), (16, 0.5)))
            + "<g transform='translate(0,6)'>" + face + "</g></g>")
    wind = ("<g class='bob' style='animation-delay:-0.5s'>"
            + "".join(f"<path class='gust' d='M-40,{y} H20 a12,12 0 1 0 -12,-12' "
                      f"stroke='#5B6C7D' stroke-width='5' fill='none' stroke-linecap='round' "
                      f"style='animation-delay:-{d}s'/>"
                      for y, d in ((-12, 0), (8, 0.5), (28, 1)))
            + "</g>")
    style = ("<style>"
             ".bob{animation:bob 3.5s ease-in-out infinite alternate}"
             ".spin{animation:spin 18s linear infinite}"
             ".drop{animation:drop 1.1s linear infinite}"
             ".flake{animation:drop 2.6s linear infinite}"
             ".gust{stroke-dasharray:60 40;animation:gust 2s linear infinite}"
             "@keyframes bob{to{transform:translateY(14px)}}"
             "@keyframes spin{to{transform:rotate(360deg)}}"
             "@keyframes drop{from{transform:translateY(0);opacity:1}"
             "to{transform:translateY(26px);opacity:0}}"
             "@keyframes gust{to{stroke-dashoffset:-100}}"
             "</style>")

    def column(first, second):
        return (f"<svg xmlns='http://www.w3.org/2000/svg' width='120' height='760'>{style}"
                f"<g transform='translate(60,110)'>{first}</g>"
                f"<g transform='translate(60,470)'>{second}</g></svg>")

    _page_css(f"""
[data-testid="stMain"] {{
    background-image: {_svg_url(column(sun, rain))}, {_svg_url(column(snow, wind))};
    background-repeat: no-repeat, no-repeat;
    background-position: left 10px top 60px, right 10px top 60px;
    background-size: 120px 760px, 120px 760px;
}}
[data-testid="stMainBlockContainer"] {{
    padding-left: 160px !important; padding-right: 160px !important;
}}
""")


def snow_to_reservoir():
    """
    A banner that tells the story of the correlation page: snow falls on the
    mountains in winter, melts when the sun comes back in spring, runs down
    the river and fills the reservoir behind the dam, which is then slowly
    drawn down until the next winter. One loop is one year (14 seconds).
    """
    flakes = "".join(
        f"<circle class='flake' cx='{x}' cy='-5' r='{r}' fill='white' "
        f"style='animation-delay:-{d}s'/>"
        for x, r, d in ((80, 3, 0), (170, 2.5, 0.8), (260, 3, 1.6), (350, 2, 0.4),
                        (430, 3, 1.2), (520, 2.5, 2.0), (610, 3, 0.6), (690, 2, 1.8)))
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 170' "
        "preserveAspectRatio='xMidYMid slice'>"
        "<style>"
        "*{transform-box:fill-box}"
        ".sky{animation:sky 14s linear infinite}"
        ".sun{animation:sun 14s ease-in-out infinite}"
        ".cap{transform-origin:50% 0%;animation:cap 14s ease-in-out infinite}"
        ".flake{animation:fall 2.4s linear infinite,season 14s linear infinite}"
        ".river{stroke-dasharray:14 10;animation:flow 0.8s linear infinite,riverflow 14s linear infinite}"
        ".water{transform-origin:50% 100%;animation:fill 14s ease-in-out infinite}"
        ".label{font:600 15px sans-serif;fill:#1B2A4A}"
        "@keyframes sky{0%,30%{fill:#AFC3D6}45%,80%{fill:#BFE3F7}100%{fill:#AFC3D6}}"
        "@keyframes sun{0%,25%{transform:translateY(90px)}45%,75%{transform:translateY(0)}"
        "100%{transform:translateY(90px)}}"
        "@keyframes cap{0%,30%{transform:scaleY(1)}55%,85%{transform:scaleY(0.15)}100%{transform:scaleY(1)}}"
        "@keyframes fall{from{transform:translateY(0)}to{transform:translateY(120px)}}"
        "@keyframes season{0%,28%{opacity:1}35%,88%{opacity:0}95%,100%{opacity:1}}"
        "@keyframes flow{to{stroke-dashoffset:-48}}"
        "@keyframes riverflow{0%,30%{opacity:0.15}40%,60%{opacity:1}75%,100%{opacity:0.25}}"
        "@keyframes fill{0%,32%{transform:scaleY(0.3)}62%{transform:scaleY(1)}100%{transform:scaleY(0.3)}}"
        "</style>"
        "<rect class='sky' width='1200' height='170'/>"
        "<g class='sun'><circle cx='560' cy='45' r='24' fill='#FFC93C'/></g>"
        f"{flakes}"
        # mountains with snow caps that shrink in spring
        "<polygon points='0,170 150,40 300,170' fill='#4A5A75'/>"
        "<polygon points='180,170 360,25 540,170' fill='#3B4A66'/>"
        "<polygon points='420,170 560,70 700,170' fill='#4A5A75'/>"
        "<g class='cap'><polygon points='114,70 150,40 186,70 165,64 150,72 133,64' fill='white'/></g>"
        "<g class='cap'><polygon points='310,66 360,25 410,66 385,58 360,70 335,58' fill='white'/></g>"
        "<g class='cap'><polygon points='532,93 560,70 588,93 572,88 560,96 547,88' fill='white'/></g>"
        # ground, river from the mountains to the reservoir
        "<rect y='150' width='1200' height='20' fill='#B9A57E'/>"
        "<path class='river' d='M360,120 C450,150 600,135 700,150 S860,150 900,140' "
        "stroke='#4F86C6' stroke-width='7' fill='none' stroke-linecap='round'/>"
        # reservoir basin, water and dam
        "<rect x='880' y='60' width='230' height='95' rx='6' fill='#E6DCC6'/>"
        "<g class='water'><rect x='884' y='64' width='222' height='88' rx='4' fill='#2D5D8A'/></g>"
        "<rect x='1105' y='40' width='22' height='120' fill='#8A7353'/>"
        "<text class='label' x='640' y='24'>snow in winter → melt in spring → full reservoir</text>"
        "</svg>")
    st.html(f"""
<style>
.melt-banner {{ width: 100%; height: 170px; border-radius: 12px; pointer-events: none;
                margin-bottom: 4px; background: {_svg_url(svg)} center / cover no-repeat; }}
</style>
<div class="melt-banner"></div>
""")
