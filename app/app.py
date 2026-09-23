# app/app.py
"""
EaglePark AI - CSC 4610 prototype.

Desktop-first Streamlit interface for parking, routing, rideshare,
and evaluation user stories. The layout automatically stacks on
smaller screens.
"""

import os
import sys

import pandas as pd
import pydeck as pdk
import streamlit as st


# Project imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

try:
    from user_stories import get_stories_for_feature
except ImportError:
    def get_stories_for_feature(feature_name):
        return []


# Page setup
st.set_page_config(
    page_title="EaglePark AI",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Demo user profiles
INSTITUTIONAL_ACCOUNTS = {
    "T00123456": {
        "name": "Alex Mercer",
        "role": "Enrolled Student",
        "permit": "Purple",
        "has_permit": True,
    },
    "T00987654": {
        "name": "Jordan Smith",
        "role": "Graduate Assistant",
        "permit": "Purple",
        "has_permit": True,
    },
    "T00554433": {
        "name": "Dr. Vance",
        "role": "Faculty / Staff",
        "permit": "Gold",
        "has_permit": True,
    },
    "T00000000": {
        "name": "Visitor / Guest",
        "role": "Unregistered Commuter",
        "permit": "None",
        "has_permit": False,
    },
}


# Campus buildings used by the route demo
CAMPUS_LANDMARKS = pd.DataFrame(
    [
        {"name": "Ashraf Islam Eng Building (AIEB)", "lat": 36.17765, "lon": -85.50615},
        {"name": "Volpe Library", "lat": 36.17780, "lon": -85.50495},
        {"name": "Prescott Hall", "lat": 36.17625, "lon": -85.50360},
        {"name": "Stonecipher Hall (LSC)", "lat": 36.17690, "lon": -85.50605},
        {"name": "Derryberry Hall", "lat": 36.17540, "lon": -85.50545},
        {"name": "Hooper Eblen Center", "lat": 36.17855, "lon": -85.50760},
        {"name": "Bell Hall", "lat": 36.17480, "lon": -85.50785},
    ]
)


# Simulated TTU parking data
def get_ttu_facilities(preset):
    lots = [
        {
            "id": "LOT-LIB",
            "name": "Volpe Library North Lot",
            "short_code": "Library Lot",
            "permit_required": "Purple",
            "capacity": 340,
            "lat": 36.17755,
            "lon": -85.50550,
            "walk_mins": 1.0,
        },
        {
            "id": "LOT-HOOPER",
            "name": "Hooper Eblen Center Apron",
            "short_code": "Hooper Lot",
            "permit_required": "Purple",
            "capacity": 580,
            "lat": 36.17750,
            "lon": -85.50930,
            "walk_mins": 5.0,
        },
        {
            "id": "LOT-PEACH",
            "name": "Peachtree Commuter Zone",
            "short_code": "Peachtree Lot",
            "permit_required": "Purple",
            "capacity": 220,
            "lat": 36.17360,
            "lon": -85.50390,
            "walk_mins": 4.5,
        },
        {
            "id": "LOT-ASHBURN",
            "name": "Ashburn Drive Staff Facility",
            "short_code": "Ashburn Lot",
            "permit_required": "Gold",
            "capacity": 175,
            "lat": 36.17630,
            "lon": -85.50150,
            "walk_mins": 2.5,
        },
        {
            "id": "LOT-BELL",
            "name": "Bell Hall / 10th St Lot",
            "short_code": "Bell Lot",
            "permit_required": "Purple",
            "capacity": 140,
            "lat": 36.17515,
            "lon": -85.50790,
            "walk_mins": 6.0,
        },
        {
            "id": "LOT-TECH-VILLAGE",
            "name": "Tech Village North Perimeter",
            "short_code": "Tech Village",
            "permit_required": "Purple",
            "capacity": 320,
            "lat": 36.18240,
            "lon": -85.51160,
            "walk_mins": 8.0,
        },
    ]

    if "Low" in preset:
        occupied = [80, 110, 35, 30, 20, 15]
    elif "Transition" in preset:
        occupied = [270, 410, 175, 120, 95, 80]
    elif "Event" in preset:
        occupied = [335, 570, 215, 170, 138, 290]
    else:
        occupied = [326, 545, 185, 155, 65, 45]

    df = pd.DataFrame(lots)
    df["occupied"] = occupied
    df["available"] = df["capacity"] - df["occupied"]
    df["pct_full"] = (df["occupied"] / df["capacity"]) * 100

    def status_from_pct(pct):
        if pct >= 90:
            return "SATURATED"
        if pct >= 75:
            return "FILLING FAST"
        return "AVAILABLE"

    def map_color(pct):
        if pct >= 90:
            return [244, 96, 96, 235]
        if pct >= 75:
            return [244, 180, 64, 235]
        return [61, 201, 145, 235]

    df["status"] = df["pct_full"].apply(status_from_pct)
    df["color"] = df["pct_full"].apply(map_color)
    df["map_label"] = df.apply(
        lambda row: f"{row['short_code']} · {row['available']} open", axis=1
    )
    return df


def recommend_lot(facilities_df, permit):
    if permit not in {"Purple", "Gold"}:
        return None

    permitted = facilities_df[
        facilities_df["permit_required"] == permit
    ].copy()

    if permitted.empty:
        return None

    open_lots = permitted[permitted["pct_full"] < 90]
    if not open_lots.empty:
        return open_lots.sort_values(
            ["walk_mins", "pct_full"], ascending=[True, True]
        ).iloc[0]

    return permitted.sort_values("available", ascending=False).iloc[0]


# Theme state
if "app_theme" not in st.session_state:
    st.session_state.app_theme = "Dark"

light_mode = st.sidebar.toggle(
    "Light mode",
    value=st.session_state.app_theme == "Light",
    help="Switch between dark and light presentation themes.",
)
st.session_state.app_theme = "Light" if light_mode else "Dark"


# Theme colors
if st.session_state.app_theme == "Dark":
    colors = {
        "bg": "#0B111A",
        "sidebar": "#0E1622",
        "panel": "#111B29",
        "panel_2": "#152235",
        "soft": "#1B2A3D",
        "border": "#26384E",
        "text": "#F5F8FC",
        "muted": "#A7B4C6",
        "purple": "#9B82F3",
        "purple_2": "#7156C8",
        "gold": "#F1CA4B",
        "good": "#3DC991",
        "warn": "#F0B84D",
        "bad": "#F06363",
        "track": "#223247",
        "shadow": "0 18px 44px rgba(0,0,0,.28)",
    }
else:
    colors = {
        "bg": "#F4F7FB",
        "sidebar": "#FFFFFF",
        "panel": "#FFFFFF",
        "panel_2": "#F9FBFD",
        "soft": "#EEF3F8",
        "border": "#D8E0EA",
        "text": "#172033",
        "muted": "#617186",
        "purple": "#5E3AA8",
        "purple_2": "#4F2984",
        "gold": "#8D6900",
        "good": "#167B55",
        "warn": "#986000",
        "bad": "#B42318",
        "track": "#E5EBF2",
        "shadow": "0 14px 34px rgba(18,35,58,.08)",
    }


# Modern desktop-first styling
st.markdown(
    f"""
    <style>
        :root {{
            --ep-bg: {colors["bg"]};
            --ep-sidebar: {colors["sidebar"]};
            --ep-panel: {colors["panel"]};
            --ep-panel-2: {colors["panel_2"]};
            --ep-soft: {colors["soft"]};
            --ep-border: {colors["border"]};
            --ep-text: {colors["text"]};
            --ep-muted: {colors["muted"]};
            --ep-purple: {colors["purple"]};
            --ep-purple-2: {colors["purple_2"]};
            --ep-gold: {colors["gold"]};
            --ep-good: {colors["good"]};
            --ep-warn: {colors["warn"]};
            --ep-bad: {colors["bad"]};
            --ep-track: {colors["track"]};
            --ep-shadow: {colors["shadow"]};
        }}

        html, body, [class*="css"] {{
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                         "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}

        html, body,
        [data-testid="stAppViewContainer"],
        .stApp {{
            background: var(--ep-bg) !important;
            color: var(--ep-text) !important;
        }}

        [data-testid="stHeader"] {{
            background: transparent !important;
        }}

        [data-testid="stAppViewBlockContainer"] {{
            width: min(100%, 1500px) !important;
            max-width: 1500px !important;
            padding: 1.4rem 2rem 3rem !important;
        }}

        section[data-testid="stSidebar"] {{
            background: var(--ep-sidebar) !important;
            border-right: 1px solid var(--ep-border) !important;
        }}

        section[data-testid="stSidebar"] > div {{
            background: var(--ep-sidebar) !important;
        }}

        section[data-testid="stSidebar"] * {{
            color: var(--ep-text);
        }}

        section[data-testid="stSidebar"] hr {{
            border-color: var(--ep-border) !important;
        }}

        h1, h2, h3, h4, h5, h6,
        p, label, .stMarkdown {{
            color: var(--ep-text);
        }}

        [data-testid="stCaptionContainer"],
        .stCaption {{
            color: var(--ep-muted) !important;
        }}

        /* Sidebar brand */
        .ep-sidebar-brand {{
            display: flex;
            align-items: center;
            gap: .75rem;
            margin: .25rem 0 1.35rem;
        }}

        .ep-sidebar-mark {{
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background: linear-gradient(145deg, #5A2A98, #3F1D72);
            border: 1px solid rgba(255,221,0,.55);
            color: #FFDD00;
            display: grid;
            place-items: center;
            font-size: .85rem;
            font-weight: 850;
            letter-spacing: .04em;
            box-shadow: var(--ep-shadow);
        }}

        .ep-sidebar-title {{
            color: var(--ep-text);
            font-size: 1.08rem;
            font-weight: 800;
            line-height: 1.1;
        }}

        .ep-sidebar-sub {{
            color: var(--ep-muted);
            font-size: .72rem;
            margin-top: .18rem;
        }}

        /* Main header */
        .ep-hero {{
            position: relative;
            overflow: hidden;
            border: 1px solid var(--ep-border);
            border-radius: 22px;
            background:
                radial-gradient(circle at 82% 18%, rgba(155,130,243,.22), transparent 28%),
                linear-gradient(135deg, rgba(94,58,168,.18), transparent 54%),
                var(--ep-panel);
            padding: 1.35rem 1.5rem;
            margin-bottom: 1.1rem;
            box-shadow: var(--ep-shadow);
        }}

        .ep-hero::after {{
            content: "";
            position: absolute;
            right: -72px;
            bottom: -92px;
            width: 230px;
            height: 230px;
            border-radius: 50%;
            border: 1px solid rgba(155,130,243,.22);
        }}

        .ep-hero-grid {{
            position: relative;
            z-index: 2;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.25rem;
        }}

        .ep-hero-kicker {{
            color: var(--ep-purple);
            font-size: .72rem;
            font-weight: 850;
            letter-spacing: .11em;
            text-transform: uppercase;
            margin-bottom: .36rem;
        }}

        .ep-hero-title {{
            color: var(--ep-text);
            font-size: clamp(1.65rem, 2.4vw, 2.55rem);
            font-weight: 850;
            letter-spacing: -.035em;
            line-height: 1.03;
            margin: 0;
        }}

        .ep-hero-sub {{
            color: var(--ep-muted);
            margin-top: .55rem;
            font-size: .92rem;
            line-height: 1.55;
            max-width: 760px;
        }}

        .ep-live-chip {{
            flex: 0 0 auto;
            display: inline-flex;
            align-items: center;
            gap: .5rem;
            border-radius: 999px;
            padding: .48rem .72rem;
            border: 1px solid var(--ep-border);
            background: var(--ep-soft);
            color: var(--ep-text);
            font-size: .72rem;
            font-weight: 800;
            letter-spacing: .04em;
        }}

        .ep-live-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--ep-good);
            box-shadow: 0 0 0 5px rgba(61,201,145,.12);
        }}

        /* Section labels */
        .ep-section-title {{
            color: var(--ep-text);
            font-size: 1.05rem;
            font-weight: 800;
            margin: .35rem 0 .75rem;
        }}

        .ep-section-sub {{
            color: var(--ep-muted);
            font-size: .82rem;
            margin-top: -.48rem;
            margin-bottom: .8rem;
        }}

        /* KPI cards */
        .ep-kpi {{
            min-height: 128px;
            border-radius: 18px;
            border: 1px solid var(--ep-border);
            background: linear-gradient(145deg, var(--ep-panel), var(--ep-panel-2));
            padding: 1rem 1.05rem;
            box-shadow: 0 8px 24px rgba(0,0,0,.06);
        }}

        .ep-kpi-label {{
            color: var(--ep-muted);
            font-size: .76rem;
            font-weight: 700;
            margin-bottom: .55rem;
        }}

        .ep-kpi-value {{
            color: var(--ep-text);
            font-size: 2rem;
            font-weight: 850;
            letter-spacing: -.035em;
            line-height: 1;
        }}

        .ep-kpi-note {{
            color: var(--ep-muted);
            font-size: .72rem;
            margin-top: .62rem;
        }}

        /* Generic panel */
        .ep-panel {{
            border: 1px solid var(--ep-border);
            border-radius: 18px;
            background: var(--ep-panel);
            padding: 1rem 1.05rem;
            box-shadow: 0 8px 24px rgba(0,0,0,.05);
        }}

        /* Lot cards */
        .ep-lot-card {{
            border: 1px solid var(--ep-border);
            border-radius: 16px;
            background: var(--ep-panel);
            padding: .9rem 1rem;
            margin-bottom: .65rem;
        }}

        .ep-lot-top {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
        }}

        .ep-lot-name {{
            color: var(--ep-text);
            font-size: .91rem;
            font-weight: 780;
            line-height: 1.3;
        }}

        .ep-lot-meta {{
            color: var(--ep-muted);
            font-size: .72rem;
            margin-top: .2rem;
        }}

        .ep-status {{
            border-radius: 999px;
            padding: .28rem .52rem;
            font-size: .65rem;
            font-weight: 850;
            white-space: nowrap;
            border: 1px solid var(--ep-border);
        }}

        .ep-status-good {{
            color: var(--ep-good);
            background: rgba(61,201,145,.10);
        }}

        .ep-status-warn {{
            color: var(--ep-warn);
            background: rgba(240,184,77,.10);
        }}

        .ep-status-bad {{
            color: var(--ep-bad);
            background: rgba(240,99,99,.10);
        }}

        .ep-progress {{
            height: 8px;
            border-radius: 999px;
            background: var(--ep-track);
            overflow: hidden;
            margin-top: .75rem;
        }}

        .ep-progress > span {{
            display: block;
            height: 100%;
            border-radius: 999px;
        }}

        .ep-lot-foot {{
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            margin-top: .5rem;
            color: var(--ep-muted);
            font-size: .7rem;
        }}

        /* Recommendation */
        .ep-rec {{
            border: 1px solid var(--ep-border);
            border-radius: 18px;
            background:
                linear-gradient(145deg, rgba(94,58,168,.14), transparent 65%),
                var(--ep-panel);
            padding: 1.1rem;
            box-shadow: 0 8px 24px rgba(0,0,0,.05);
        }}

        .ep-rec-label {{
            color: var(--ep-purple);
            font-size: .69rem;
            font-weight: 850;
            letter-spacing: .09em;
            text-transform: uppercase;
        }}

        .ep-rec-name {{
            color: var(--ep-text);
            font-size: 1.25rem;
            font-weight: 850;
            margin-top: .35rem;
        }}

        .ep-rec-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0,1fr));
            gap: .55rem;
            margin-top: .9rem;
        }}

        .ep-rec-stat {{
            border: 1px solid var(--ep-border);
            border-radius: 12px;
            background: var(--ep-soft);
            padding: .65rem;
        }}

        .ep-rec-stat-label {{
            color: var(--ep-muted);
            font-size: .65rem;
            font-weight: 700;
        }}

        .ep-rec-stat-value {{
            color: var(--ep-text);
            font-size: .91rem;
            font-weight: 800;
            margin-top: .2rem;
        }}

        /* Story cards */
        .ep-story {{
            border: 1px solid var(--ep-border);
            border-radius: 12px;
            background: var(--ep-panel-2);
            padding: .8rem .9rem;
            margin-bottom: .55rem;
        }}

        .ep-story-id {{
            color: var(--ep-purple);
            font-size: .66rem;
            font-weight: 850;
            letter-spacing: .06em;
            margin-bottom: .3rem;
        }}

        .ep-story-text {{
            color: var(--ep-text);
            font-size: .82rem;
            line-height: 1.48;
        }}

        /* Streamlit controls */
        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"],
        .stTextInput input,
        .stTimeInput input {{
            background: var(--ep-panel) !important;
            color: var(--ep-text) !important;
            border-color: var(--ep-border) !important;
            border-radius: 10px !important;
        }}

        div[data-baseweb="select"] span,
        div[data-baseweb="select"] input {{
            color: var(--ep-text) !important;
        }}

        [data-baseweb="popover"],
        [role="listbox"] {{
            background: var(--ep-panel) !important;
            color: var(--ep-text) !important;
        }}

        [role="option"] {{
            color: var(--ep-text) !important;
        }}

        [role="option"]:hover {{
            background: var(--ep-soft) !important;
        }}

        .stButton > button,
        .stLinkButton > a {{
            min-height: 2.7rem;
            border-radius: 11px !important;
            background: linear-gradient(135deg, var(--ep-purple-2), var(--ep-purple)) !important;
            color: #FFFFFF !important;
            border: 0 !important;
            font-weight: 800 !important;
            box-shadow: 0 8px 18px rgba(79,41,132,.18);
        }}

        .stButton > button:hover,
        .stLinkButton > a:hover {{
            filter: brightness(1.08);
            transform: translateY(-1px);
        }}

        .stButton > button:focus-visible,
        .stLinkButton > a:focus-visible,
        input:focus-visible,
        [role="radiogroup"] label:focus-within {{
            outline: 3px solid var(--ep-gold) !important;
            outline-offset: 2px;
        }}

        div[data-testid="stExpander"] {{
            border: 1px solid var(--ep-border) !important;
            border-radius: 14px !important;
            background: var(--ep-panel) !important;
            overflow: hidden;
        }}

        div[data-testid="stExpander"] summary {{
            color: var(--ep-text) !important;
            font-weight: 760;
        }}

        div[data-testid="stAlert"] {{
            border-radius: 13px !important;
            border: 1px solid var(--ep-border) !important;
        }}

        /* Map */
        .stDeckGlJsonChart {{
            min-height: 500px;
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid var(--ep-border);
            background: var(--ep-panel);
            box-shadow: 0 8px 24px rgba(0,0,0,.05);
        }}

        /* Hide some Streamlit chrome during demos */
        [data-testid="stToolbar"] {{
            opacity: .35;
        }}

        /* Responsive layout */
        @media (max-width: 980px) {{
            [data-testid="stAppViewBlockContainer"] {{
                padding: 1rem 1rem 2rem !important;
            }}

            .ep-hero {{
                border-radius: 18px;
            }}

            .ep-hero-grid {{
                align-items: flex-start;
                flex-wrap: wrap;
            }}

            .stDeckGlJsonChart {{
                min-height: 400px;
            }}
        }}

        @media (max-width: 640px) {{
            [data-testid="stAppViewBlockContainer"] {{
                padding: .65rem .65rem 1.5rem !important;
            }}

            .ep-hero {{
                padding: 1rem;
                border-radius: 15px;
            }}

            .ep-hero-title {{
                font-size: 1.5rem;
            }}

            .ep-hero-sub {{
                font-size: .84rem;
            }}

            .ep-live-chip {{
                width: fit-content;
            }}

            .ep-kpi {{
                min-height: 108px;
            }}

            .ep-rec-grid {{
                grid-template-columns: 1fr;
            }}

            .stDeckGlJsonChart {{
                min-height: 335px;
            }}
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# Sidebar brand
st.sidebar.markdown(
    """
    <div class="ep-sidebar-brand">
        <div class="ep-sidebar-mark">TTU</div>
        <div>
            <div class="ep-sidebar-title">EaglePark AI</div>
            <div class="ep-sidebar-sub">Smart campus mobility</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# Sidebar navigation
st.sidebar.markdown("### Navigation")
active_page = st.sidebar.radio(
    "Application Module",
    [
        "Overview",
        "Predictive Parking",
        "Smart Route",
        "RideShare",
        "Operations",
    ],
    label_visibility="collapsed",
)

st.sidebar.divider()
st.sidebar.markdown("### Active Profile")

selected_t_number = st.sidebar.selectbox(
    "Profile",
    options=list(INSTITUTIONAL_ACCOUNTS.keys()),
    index=0,
    format_func=lambda value: (
        f"{INSTITUTIONAL_ACCOUNTS[value]['name']} · "
        f"{INSTITUTIONAL_ACCOUNTS[value]['role']}"
    ),
)

account = INSTITUTIONAL_ACCOUNTS[selected_t_number]
user_permit = account["permit"]

permit_label = (
    f"{user_permit} permit"
    if user_permit in {"Purple", "Gold"}
    else "No campus permit"
)
st.sidebar.caption(f"Permit access: {permit_label}")

traffic_preset = st.sidebar.selectbox(
    "Traffic Scenario",
    [
        "Morning Peak (07:30 - 09:00)",
        "Midday Transition (11:00 - 13:00)",
        "Afternoon / Evening (Low Traffic)",
        "Event Saturation (Game Day)",
    ],
)

st.sidebar.divider()
st.sidebar.caption(
    "Prototype data is simulated for presentation and testing."
)

facilities_df = get_ttu_facilities(traffic_preset)
recommended_lot = recommend_lot(facilities_df, user_permit)


# Reusable UI helpers
def render_hero(title, subtitle):
    st.markdown(
        f"""
        <div class="ep-hero">
            <div class="ep-hero-grid">
                <div>
                    <div class="ep-hero-kicker">EaglePark AI · CSC 4610</div>
                    <h1 class="ep-hero-title">{title}</h1>
                    <div class="ep-hero-sub">{subtitle}</div>
                </div>
                <div class="ep-live-chip">
                    <span class="ep-live-dot"></span>
                    SIMULATION ONLINE
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label, value, note):
    st.markdown(
        f"""
        <div class="ep-kpi">
            <div class="ep-kpi-label">{label}</div>
            <div class="ep-kpi-value">{value}</div>
            <div class="ep-kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_class(status):
    if status == "AVAILABLE":
        return "ep-status-good"
    if status == "FILLING FAST":
        return "ep-status-warn"
    return "ep-status-bad"


def status_color(status):
    if status == "AVAILABLE":
        return "var(--ep-good)"
    if status == "FILLING FAST":
        return "var(--ep-warn)"
    return "var(--ep-bad)"


def lot_card(row):
    st.markdown(
        f"""
        <div class="ep-lot-card">
            <div class="ep-lot-top">
                <div>
                    <div class="ep-lot-name">{row["name"]}</div>
                    <div class="ep-lot-meta">
                        {row["permit_required"]} permit · {row["capacity"]} total spaces
                    </div>
                </div>
                <div class="ep-status {status_class(row["status"])}">
                    {row["status"]}
                </div>
            </div>

            <div class="ep-progress">
                <span style="
                    width:{min(row["pct_full"], 100):.1f}%;
                    background:{status_color(row["status"])};
                "></span>
            </div>

            <div class="ep-lot-foot">
                <span>{row["pct_full"]:.0f}% occupied</span>
                <span><strong>{row["available"]}</strong> open</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_story_traceability(feature_name):
    stories = get_stories_for_feature(feature_name)

    if not stories:
        return

    with st.expander("User story traceability", expanded=False):
        st.caption(
            "These are the CSC 4610 stories connected to this part of the prototype."
        )
        for story in stories:
            st.markdown(
                f"""
                <div class="ep-story">
                    <div class="ep-story-id">
                        {story["id"]} · Board #{story["board_number"]} · Issue #{story["github_issue"]}
                    </div>
                    <div class="ep-story-text">{story["story"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_recommendation(destination):
    if recommended_lot is None:
        st.markdown(
            """
            <div class="ep-panel">
                <div class="ep-section-title">No permitted route available</div>
                <div class="ep-section-sub">
                    This profile does not currently have Purple or Gold parking access.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    gps_link = (
        "https://www.google.com/maps/dir/?api=1"
        f"&destination={recommended_lot['lat']},{recommended_lot['lon']}"
        "&travelmode=driving"
    )

    st.markdown(
        f"""
        <div class="ep-rec">
            <div class="ep-rec-label">Recommended parking</div>
            <div class="ep-rec-name">{recommended_lot["name"]}</div>

            <div class="ep-rec-grid">
                <div class="ep-rec-stat">
                    <div class="ep-rec-stat-label">Open spaces</div>
                    <div class="ep-rec-stat-value">{recommended_lot["available"]}</div>
                </div>
                <div class="ep-rec-stat">
                    <div class="ep-rec-stat-label">Current occupancy</div>
                    <div class="ep-rec-stat-value">{recommended_lot["pct_full"]:.0f}%</div>
                </div>
                <div class="ep-rec-stat">
                    <div class="ep-rec-stat-label">Permit match</div>
                    <div class="ep-rec-stat-value">{recommended_lot["permit_required"]}</div>
                </div>
                <div class="ep-rec-stat">
                    <div class="ep-rec-stat-label">Estimated walk</div>
                    <div class="ep-rec-stat-value">~{recommended_lot["walk_mins"]} min</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.link_button(
        f"Route to {recommended_lot['short_code']}",
        url=gps_link,
        use_container_width=True,
    )

    primary_hub = facilities_df[facilities_df["id"] == "LOT-LIB"].iloc[0]
    if primary_hub["pct_full"] >= 90 and user_permit == "Purple":
        st.warning(
            f"Volpe Library Lot is {primary_hub['pct_full']:.0f}% full. "
            f"EaglePark recommends {recommended_lot['short_code']} instead."
        )


def render_map():
    satellite_tiles = pdk.Layer(
        "TileLayer",
        data=(
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        min_zoom=0,
        max_zoom=19,
        tile_size=256,
        pickable=False,
    )

    lot_nodes = pdk.Layer(
        "ScatterplotLayer",
        data=facilities_df,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius=22,
        radius_min_pixels=9,
        radius_max_pixels=15,
        pickable=True,
        auto_highlight=True,
    )

    lot_labels = pdk.Layer(
        "TextLayer",
        data=facilities_df,
        get_position=["lon", "lat"],
        get_text="map_label",
        get_color=[255, 255, 255, 255],
        get_size=11,
        get_alignment_baseline="'bottom'",
        get_pixel_offset=[0, -14],
        background=True,
        get_background_color=[12, 20, 32, 220],
        pickable=False,
    )

    building_nodes = pdk.Layer(
        "ScatterplotLayer",
        data=CAMPUS_LANDMARKS,
        get_position=["lon", "lat"],
        get_color=[78, 170, 255, 220],
        get_radius=14,
        radius_min_pixels=6,
        radius_max_pixels=8,
        pickable=True,
    )

    deck_view = pdk.ViewState(
        latitude=36.1775,
        longitude=-85.5058,
        zoom=15.6,
        pitch=0,
        bearing=0,
    )

    st.pydeck_chart(
        pdk.Deck(
            map_style=None,
            layers=[satellite_tiles, building_nodes, lot_nodes, lot_labels],
            initial_view_state=deck_view,
            tooltip={
                "text": "{name}\nStatus: {status}\nOpen spaces: {available} / {capacity}"
            },
        ),
        use_container_width=True,
    )


def render_lot_grid():
    rows = facilities_df.reset_index(drop=True)

    for start in range(0, len(rows), 2):
        cols = st.columns(2, gap="medium")
        for offset, col in enumerate(cols):
            idx = start + offset
            if idx < len(rows):
                with col:
                    lot_card(rows.iloc[idx])


# Overview
if active_page == "Overview":
    render_hero(
        "Campus mobility at a glance",
        "A single view of current parking pressure, permit-aware recommendations, "
        "and the campus conditions driving EaglePark decisions.",
    )

    total_capacity = int(facilities_df["capacity"].sum())
    total_available = int(facilities_df["available"].sum())
    campus_full_pct = (
        facilities_df["occupied"].sum() / facilities_df["capacity"].sum()
    ) * 100
    saturated_count = int((facilities_df["pct_full"] >= 90).sum())

    k1, k2, k3, k4 = st.columns(4, gap="medium")
    with k1:
        kpi_card("Campus capacity", f"{total_capacity:,}", "Tracked demo spaces")
    with k2:
        kpi_card("Open spaces", f"{total_available:,}", "Across all demo lots")
    with k3:
        kpi_card("Campus occupancy", f"{campus_full_pct:.0f}%", "Current traffic scenario")
    with k4:
        kpi_card("Saturated lots", str(saturated_count), "At or above 90%")

    st.markdown(
        '<div class="ep-section-title">Parking conditions</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ep-section-sub">Live-style presentation view using simulated occupancy data.</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.55, 1], gap="large")

    with left:
        render_lot_grid()

    with right:
        st.markdown(
            '<div class="ep-section-title">Best option for this profile</div>',
            unsafe_allow_html=True,
        )
        render_recommendation("Campus")
        st.caption(
            "Recommendation logic uses permit access, occupancy, and walking distance."
        )

    render_story_traceability("Dashboard")


# Predictive Parking
elif active_page == "Predictive Parking":
    render_hero(
        "Predictive parking",
        "Forecast-focused workspace for helping commuters avoid lots that are likely "
        "to fill before they arrive.",
    )

    st.info(
        "The current build shows the occupancy baseline. "
        "The next implementation step adds the 20-minute forecast and fill-up alert."
    )

    left, right = st.columns([1, 1.35], gap="large")

    with left:
        st.markdown(
            '<div class="ep-section-title">Current occupancy</div>',
            unsafe_allow_html=True,
        )
        render_lot_grid()

    with right:
        st.markdown(
            '<div class="ep-section-title">Campus view</div>',
            unsafe_allow_html=True,
        )
        render_map()

    render_story_traceability("Predictive Parking")


# Smart Route
elif active_page == "Smart Route":
    render_hero(
        "Smart route",
        "Permit-aware parking guidance that reacts to campus saturation and helps "
        "the driver choose a practical arrival lot.",
    )

    left, right = st.columns([.9, 1.5], gap="large")

    with left:
        st.markdown(
            '<div class="ep-section-title">Route setup</div>',
            unsafe_allow_html=True,
        )

        selected_destination = st.selectbox(
            "Campus destination",
            CAMPUS_LANDMARKS["name"].tolist(),
        )

        st.markdown(
            '<div class="ep-section-title" style="margin-top:1rem;">Recommendation</div>',
            unsafe_allow_html=True,
        )
        render_recommendation(selected_destination)

    with right:
        st.markdown(
            '<div class="ep-section-title">Campus map</div>',
            unsafe_allow_html=True,
        )
        render_map()

    st.markdown(
        '<div class="ep-section-title">All parking lots</div>',
        unsafe_allow_html=True,
    )
    render_lot_grid()

    render_story_traceability("Smart Route")


# RideShare
elif active_page == "RideShare":
    render_hero(
        "RideShare",
        "Planned commuter-matching workspace based on arrival time, destination, "
        "role, and proximity while keeping the rider in control.",
    )

    st.info(
        "RideShare matching is the next major workflow after Predictive Parking. "
        "The page is shown now so the presentation matches the project epics."
    )

    left, right = st.columns(2, gap="large")

    with left:
        st.markdown(
            '<div class="ep-section-title">Trip details</div>',
            unsafe_allow_html=True,
        )
        st.text_input("Approximate origin / area", disabled=True)
        st.time_input("Target campus arrival", disabled=True)

    with right:
        st.markdown(
            '<div class="ep-section-title">Match preferences</div>',
            unsafe_allow_html=True,
        )
        st.selectbox(
            "Ride preference",
            ["Need a ride", "Offering a ride"],
            disabled=True,
        )
        st.selectbox(
            "Match group",
            ["Students", "Faculty / Staff"],
            disabled=True,
        )

    st.caption(
        "Planned: verified driver records, timetable/proximity matching, "
        "detour estimates, and evaluation failure cases."
    )

    render_story_traceability("RideShare")


# Operations
else:
    render_hero(
        "Operations & evaluation",
        "Administrative view for lot pressure, system evaluation, and the failure "
        "cases defined in the CSC 4610 labs.",
    )

    full_90 = int((facilities_df["pct_full"] >= 90).sum())
    full_75 = int((facilities_df["pct_full"] >= 75).sum())
    total_open = int(facilities_df["available"].sum())

    k1, k2, k3 = st.columns(3, gap="medium")
    with k1:
        kpi_card("Lots ≥ 90%", str(full_90), "Immediate attention")
    with k2:
        kpi_card("Lots ≥ 75%", str(full_75), "Filling or saturated")
    with k3:
        kpi_card("Open spaces", f"{total_open:,}", "Across all demo lots")

    left, right = st.columns(2, gap="large")

    with left:
        st.markdown(
            '<div class="ep-section-title">Lab 5 evaluation</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="ep-panel">
                <strong>Planned evaluation surface</strong><br><br>
                Functional metrics, similarity-based metrics, the AI-judge
                criterion, and failure-case results will be shown here.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            '<div class="ep-section-title">Failure tests</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="ep-panel">
                <strong>1.</strong> Invalid or non-existent rideshare recommendation.<br><br>
                <strong>2.</strong> A matched participant is flagged as a no-show.<br><br>
                <strong>3.</strong> A removed rideshare user is still recommended.<br><br>
                <strong>4.</strong> Parking data is stale, unavailable, or incorrect.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="ep-section-title">Current lot pressure</div>',
        unsafe_allow_html=True,
    )
    render_lot_grid()

    render_story_traceability("Admin & Evaluation")
