# app/app.py
"""
EaglePark AI - CSC 4610 prototype.

Desktop-first Streamlit interface for parking, routing,
rideshare, and evaluation user stories.
"""

import os
import sys
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSET_DIR = PROJECT_ROOT / "assets"
LOGO_PATH = ASSET_DIR / "ttu_logo.png"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

try:
    from user_stories import get_stories_for_feature
except ImportError:

    def get_stories_for_feature(feature_name):
        return []


# Streamlit page settings
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
    },
    "T00987654": {
        "name": "Jordan Smith",
        "role": "Graduate Assistant",
        "permit": "Purple",
    },
    "T00554433": {
        "name": "Dr. Vance",
        "role": "Faculty / Staff",
        "permit": "Gold",
    },
    "T00000000": {
        "name": "Visitor / Guest",
        "role": "Unregistered Commuter",
        "permit": "None",
    },
}


# Campus buildings used by the route demo
CAMPUS_LANDMARKS = pd.DataFrame([
    {"name": "Ashraf Islam Eng Building (AIEB)", "lat": 36.17765, "lon": -85.50615},
    {"name": "Volpe Library", "lat": 36.17780, "lon": -85.50495},
    {"name": "Prescott Hall", "lat": 36.17625, "lon": -85.50360},
    {"name": "Stonecipher Hall (LSC)", "lat": 36.17690, "lon": -85.50605},
    {"name": "Derryberry Hall", "lat": 36.17540, "lon": -85.50545},
    {"name": "Hooper Eblen Center", "lat": 36.17855, "lon": -85.50760},
    {"name": "Bell Hall", "lat": 36.17480, "lon": -85.50785},
])


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

    def get_status(pct):
        if pct >= 90:
            return "SATURATED"
        if pct >= 75:
            return "FILLING FAST"
        return "AVAILABLE"

    def get_map_color(pct):
        if pct >= 90:
            return [239, 92, 92, 235]
        if pct >= 75:
            return [236, 171, 54, 235]
        return [47, 190, 132, 235]

    df["status"] = df["pct_full"].apply(get_status)
    df["color"] = df["pct_full"].apply(get_map_color)
    df["map_label"] = df.apply(
        lambda row: f"{row['short_code']} · {row['available']} open", axis=1
    )

    return df


def recommend_lot(facilities_df, permit):
    if permit not in {"Purple", "Gold"}:
        return None

    permitted = facilities_df[facilities_df["permit_required"] == permit].copy()

    if permitted.empty:
        return None

    usable = permitted[permitted["pct_full"] < 90]

    if not usable.empty:
        return usable.sort_values(
            ["walk_mins", "pct_full"],
            ascending=[True, True],
        ).iloc[0]

    return permitted.sort_values(
        "available",
        ascending=False,
    ).iloc[0]


# Theme toggle comes before CSS so the entire page rerenders together.
if "app_theme" not in st.session_state:
    st.session_state.app_theme = "Dark"

light_mode = st.sidebar.toggle(
    "Light mode",
    value=st.session_state.app_theme == "Light",
    help="Switch the entire EaglePark interface between light and dark mode.",
)
st.session_state.app_theme = "Light" if light_mode else "Dark"


# Every visible color comes from one theme dictionary.
if st.session_state.app_theme == "Dark":
    theme = {
        "scheme": "dark",
        "bg": "#08111D",
        "sidebar": "#0C1725",
        "panel": "#101D2C",
        "panel_alt": "#142337",
        "soft": "#1A2B40",
        "border": "#2B3E55",
        "text": "#F7FAFE",
        "muted": "#AAB8CA",
        "purple": "#AA8BFF",
        "purple_strong": "#7957D5",
        "gold": "#F6D34D",
        "green": "#49D39E",
        "amber": "#F2BC54",
        "red": "#FF7474",
        "input": "#122136",
        "input_text": "#F7FAFE",
        "track": "#22344A",
        "shadow": "0 18px 48px rgba(0,0,0,.30)",
    }
else:
    theme = {
        "scheme": "light",
        "bg": "#F4F7FB",
        "sidebar": "#FFFFFF",
        "panel": "#FFFFFF",
        "panel_alt": "#F8FAFD",
        "soft": "#EEF3F8",
        "border": "#D7E0EA",
        "text": "#172033",
        "muted": "#66768A",
        "purple": "#6540AF",
        "purple_strong": "#4F2984",
        "gold": "#806000",
        "green": "#14764E",
        "amber": "#925A00",
        "red": "#B42318",
        "input": "#FFFFFF",
        "input_text": "#172033",
        "track": "#E4EAF1",
        "shadow": "0 14px 36px rgba(18,35,58,.09)",
    }


# Apply one complete theme to custom HTML and Streamlit controls.
st.markdown(
    f"""
    <style>
        :root {{
            color-scheme: {theme["scheme"]};
            --ep-bg: {theme["bg"]};
            --ep-sidebar: {theme["sidebar"]};
            --ep-panel: {theme["panel"]};
            --ep-panel-alt: {theme["panel_alt"]};
            --ep-soft: {theme["soft"]};
            --ep-border: {theme["border"]};
            --ep-text: {theme["text"]};
            --ep-muted: {theme["muted"]};
            --ep-purple: {theme["purple"]};
            --ep-purple-strong: {theme["purple_strong"]};
            --ep-gold: {theme["gold"]};
            --ep-green: {theme["green"]};
            --ep-amber: {theme["amber"]};
            --ep-red: {theme["red"]};
            --ep-input: {theme["input"]};
            --ep-input-text: {theme["input_text"]};
            --ep-track: {theme["track"]};
            --ep-shadow: {theme["shadow"]};
        }}

        html, body, .stApp,
        [data-testid="stAppViewContainer"] {{
            background: var(--ep-bg) !important;
            color: var(--ep-text) !important;
        }}

        html, body, [class*="css"] {{
            font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont,
                         "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}

        [data-testid="stHeader"] {{
            background: transparent !important;
        }}

        [data-testid="stAppViewBlockContainer"] {{
            width: min(100%, 1500px) !important;
            max-width: 1500px !important;
            padding: 1.3rem 2rem 3rem !important;
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
        p, label, .stMarkdown,
        [data-testid="stMarkdownContainer"] {{
            color: var(--ep-text);
        }}

        [data-testid="stCaptionContainer"],
        .stCaption {{
            color: var(--ep-muted) !important;
        }}

        /* Sidebar logo stays readable in either theme. */
        .ep-logo-shell {{
            border-radius: 16px;
            border: 1px solid var(--ep-border);
            background: #FFDD00;
            overflow: hidden;
            padding: .35rem;
            margin: .4rem 0 .7rem;
            box-shadow: var(--ep-shadow);
        }}

        .ep-brand-copy {{
            margin-bottom: 1.25rem;
        }}

        .ep-brand-title {{
            color: var(--ep-text);
            font-size: 1.15rem;
            font-weight: 850;
            line-height: 1.15;
        }}

        .ep-brand-subtitle {{
            color: var(--ep-muted);
            font-size: .75rem;
            margin-top: .25rem;
        }}

        /* Main page hero */
        .ep-hero {{
            border: 1px solid var(--ep-border);
            border-radius: 22px;
            background:
                radial-gradient(circle at 88% 8%, rgba(121,87,213,.24), transparent 30%),
                linear-gradient(135deg, rgba(121,87,213,.14), transparent 58%),
                var(--ep-panel);
            padding: 1.35rem 1.5rem;
            margin-bottom: 1.15rem;
            box-shadow: var(--ep-shadow);
        }}

        .ep-hero-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
        }}

        .ep-kicker {{
            color: var(--ep-purple);
            font-size: .71rem;
            font-weight: 850;
            letter-spacing: .12em;
            text-transform: uppercase;
            margin-bottom: .38rem;
        }}

        .ep-title {{
            color: var(--ep-text);
            font-size: clamp(1.75rem, 2.5vw, 2.55rem);
            font-weight: 850;
            line-height: 1.04;
            letter-spacing: -.035em;
            margin: 0;
        }}

        .ep-subtitle {{
            color: var(--ep-muted);
            max-width: 780px;
            margin-top: .55rem;
            font-size: .92rem;
            line-height: 1.55;
        }}

        .ep-live {{
            flex: 0 0 auto;
            display: inline-flex;
            align-items: center;
            gap: .5rem;
            border: 1px solid var(--ep-border);
            border-radius: 999px;
            background: var(--ep-soft);
            color: var(--ep-text);
            padding: .48rem .72rem;
            font-size: .7rem;
            font-weight: 800;
            letter-spacing: .05em;
        }}

        .ep-live-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--ep-green);
        }}

        .ep-section-title {{
            color: var(--ep-text);
            font-size: 1.05rem;
            font-weight: 820;
            margin: .4rem 0 .75rem;
        }}

        .ep-section-subtitle {{
            color: var(--ep-muted);
            font-size: .8rem;
            margin-top: -.45rem;
            margin-bottom: .8rem;
        }}

        /* KPI cards */
        .ep-kpi {{
            min-height: 124px;
            border: 1px solid var(--ep-border);
            border-radius: 18px;
            background: linear-gradient(145deg, var(--ep-panel), var(--ep-panel-alt));
            padding: 1rem 1.05rem;
            box-shadow: 0 8px 24px rgba(0,0,0,.05);
        }}

        .ep-kpi-label {{
            color: var(--ep-muted);
            font-size: .75rem;
            font-weight: 720;
        }}

        .ep-kpi-value {{
            color: var(--ep-text);
            font-size: 2rem;
            font-weight: 850;
            letter-spacing: -.035em;
            margin-top: .45rem;
            line-height: 1;
        }}

        .ep-kpi-note {{
            color: var(--ep-muted);
            font-size: .7rem;
            margin-top: .65rem;
        }}

        /* Lot cards */
        .ep-lot-card {{
            border: 1px solid var(--ep-border);
            border-radius: 16px;
            background: var(--ep-panel);
            padding: .95rem 1rem;
            margin-bottom: .65rem;
            box-shadow: 0 6px 20px rgba(0,0,0,.04);
        }}

        .ep-lot-head {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: .75rem;
        }}

        .ep-lot-name {{
            color: var(--ep-text);
            font-size: .9rem;
            font-weight: 820;
            line-height: 1.28;
        }}

        .ep-lot-meta {{
            color: var(--ep-muted);
            font-size: .71rem;
            margin-top: .28rem;
        }}

        .ep-badge {{
            flex: 0 0 auto;
            border: 1px solid var(--ep-border);
            border-radius: 999px;
            padding: .28rem .5rem;
            font-size: .63rem;
            font-weight: 850;
            white-space: nowrap;
        }}

        .ep-badge-good {{
            color: var(--ep-green);
            background: color-mix(in srgb, var(--ep-green) 10%, transparent);
        }}

        .ep-badge-warn {{
            color: var(--ep-amber);
            background: color-mix(in srgb, var(--ep-amber) 10%, transparent);
        }}

        .ep-badge-bad {{
            color: var(--ep-red);
            background: color-mix(in srgb, var(--ep-red) 10%, transparent);
        }}

        .ep-progress {{
            height: 8px;
            border-radius: 999px;
            background: var(--ep-track);
            overflow: hidden;
            margin-top: .75rem;
        }}

        .ep-progress-fill {{
            height: 100%;
            border-radius: 999px;
        }}

        .ep-lot-foot {{
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            color: var(--ep-muted);
            font-size: .69rem;
            margin-top: .5rem;
        }}

        /* Recommendation card */
        .ep-rec {{
            border: 1px solid var(--ep-border);
            border-radius: 18px;
            background:
                linear-gradient(145deg, rgba(121,87,213,.14), transparent 65%),
                var(--ep-panel);
            padding: 1.05rem;
            box-shadow: 0 8px 24px rgba(0,0,0,.05);
        }}

        .ep-rec-label {{
            color: var(--ep-purple);
            font-size: .68rem;
            font-weight: 850;
            letter-spacing: .09em;
            text-transform: uppercase;
        }}

        .ep-rec-name {{
            color: var(--ep-text);
            font-size: 1.2rem;
            font-weight: 850;
            margin-top: .38rem;
        }}

        .ep-rec-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
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
            font-size: .64rem;
            font-weight: 720;
        }}

        .ep-rec-stat-value {{
            color: var(--ep-text);
            font-size: .9rem;
            font-weight: 820;
            margin-top: .2rem;
        }}

        /* User story traceability */
        .ep-story {{
            border: 1px solid var(--ep-border);
            border-radius: 12px;
            background: var(--ep-panel-alt);
            padding: .8rem .9rem;
            margin-bottom: .55rem;
        }}

        .ep-story-id {{
            color: var(--ep-purple);
            font-size: .65rem;
            font-weight: 850;
            letter-spacing: .05em;
            margin-bottom: .3rem;
        }}

        .ep-story-text {{
            color: var(--ep-text);
            font-size: .81rem;
            line-height: 1.5;
        }}

        /* Native Streamlit controls */
        section[data-testid="stSidebar"] [data-baseweb="select"] > div,
        section[data-testid="stSidebar"] [data-baseweb="base-input"],
        section[data-testid="stSidebar"] input,
        [data-testid="stMain"] [data-baseweb="select"] > div,
        [data-testid="stMain"] [data-baseweb="base-input"],
        [data-testid="stMain"] input {{
            background: var(--ep-input) !important;
            border-color: var(--ep-border) !important;
            color: var(--ep-input-text) !important;
        }}

        section[data-testid="stSidebar"] [data-baseweb="select"] *,
        [data-testid="stMain"] [data-baseweb="select"] * {{
            color: var(--ep-input-text) !important;
        }}

        section[data-testid="stSidebar"] input,
        [data-testid="stMain"] input {{
            -webkit-text-fill-color: var(--ep-input-text) !important;
            opacity: 1 !important;
        }}

        section[data-testid="stSidebar"] svg,
        [data-testid="stMain"] [data-baseweb="select"] svg {{
            fill: var(--ep-muted) !important;
            color: var(--ep-muted) !important;
        }}

        div[data-baseweb="popover"],
        div[data-baseweb="menu"],
        [role="listbox"] {{
            background: var(--ep-panel) !important;
            color: var(--ep-text) !important;
        }}

        [role="option"],
        [role="option"] * {{
            background: var(--ep-panel) !important;
            color: var(--ep-text) !important;
        }}

        [role="option"]:hover,
        [role="option"]:hover * {{
            background: var(--ep-soft) !important;
        }}

        div[data-testid="stExpander"] {{
            border: 1px solid var(--ep-border) !important;
            border-radius: 14px !important;
            background: var(--ep-panel) !important;
            overflow: hidden;
        }}

        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary * {{
            color: var(--ep-text) !important;
        }}

        div[data-testid="stAlert"] {{
            border-radius: 13px !important;
            border: 1px solid var(--ep-border) !important;
        }}

        .stLinkButton > a {{
            min-height: 2.7rem;
            border-radius: 11px !important;
            background: linear-gradient(
                135deg,
                var(--ep-purple-strong),
                var(--ep-purple)
            ) !important;
            color: #FFFFFF !important;
            border: 0 !important;
            font-weight: 800 !important;
            box-shadow: 0 8px 18px rgba(79,41,132,.18);
        }}

        .stLinkButton > a:hover {{
            filter: brightness(1.08);
        }}

        .stLinkButton > a:focus-visible,
        input:focus-visible,
        [role="radiogroup"] label:focus-within {{
            outline: 3px solid var(--ep-gold) !important;
            outline-offset: 2px;
        }}

        /* Map */
        .stDeckGlJsonChart {{
            min-height: 510px;
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid var(--ep-border);
            background: var(--ep-panel);
            box-shadow: 0 8px 24px rgba(0,0,0,.05);
        }}

        [data-testid="stToolbar"] {{
            opacity: .35;
        }}

        /* Responsive breakpoints */
        @media (max-width: 980px) {{
            [data-testid="stAppViewBlockContainer"] {{
                padding: 1rem 1rem 2rem !important;
            }}

            .ep-hero-row {{
                align-items: flex-start;
                flex-wrap: wrap;
            }}

            .stDeckGlJsonChart {{
                min-height: 400px;
            }}
        }}

        @media (max-width: 640px) {{
            [data-testid="stAppViewBlockContainer"] {{
                padding: .7rem .65rem 1.5rem !important;
            }}

            .ep-hero {{
                border-radius: 16px;
                padding: 1rem;
            }}

            .ep-title {{
                font-size: 1.5rem;
            }}

            .ep-subtitle {{
                font-size: .84rem;
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


# Small helper: remove newlines so Markdown never prints HTML as code.
def render_html(html):
    compact = " ".join(line.strip() for line in html.splitlines())
    st.markdown(compact, unsafe_allow_html=True)


# Sidebar branding
if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), use_container_width=True)
else:
    render_html(
        """
        <div class="ep-logo-shell">
            <div style="color:#4F2984;font-size:1.4rem;font-weight:900;text-align:center;">
                TENNESSEE TECH
            </div>
        </div>
        """
    )

st.sidebar.markdown(
    """
    <div class="ep-brand-copy">
        <div class="ep-brand-title">EaglePark AI</div>
        <div class="ep-brand-subtitle">Smart campus mobility prototype</div>
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

permit_text = (
    f"{user_permit} permit" if user_permit in {"Purple", "Gold"} else "No campus permit"
)

st.sidebar.caption(f"Permit access: {permit_text}")

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
st.sidebar.caption("Prototype values are simulated for demonstration.")

facilities_df = get_ttu_facilities(traffic_preset)
recommended_lot = recommend_lot(facilities_df, user_permit)


# Reusable UI helpers
def render_hero(title, subtitle):
    render_html(
        f"""
        <div class="ep-hero">
            <div class="ep-hero-row">
                <div>
                    <div class="ep-kicker">EaglePark AI · CSC 4610</div>
                    <h1 class="ep-title">{title}</h1>
                    <div class="ep-subtitle">{subtitle}</div>
                </div>
                <div class="ep-live">
                    <span class="ep-live-dot"></span>
                    SIMULATION ONLINE
                </div>
            </div>
        </div>
        """
    )


def render_kpi(label, value, note):
    render_html(
        f"""
        <div class="ep-kpi">
            <div class="ep-kpi-label">{label}</div>
            <div class="ep-kpi-value">{value}</div>
            <div class="ep-kpi-note">{note}</div>
        </div>
        """
    )


def status_class(status):
    if status == "AVAILABLE":
        return "ep-badge-good"
    if status == "FILLING FAST":
        return "ep-badge-warn"
    return "ep-badge-bad"


def status_fill(status):
    if status == "AVAILABLE":
        return "var(--ep-green)"
    if status == "FILLING FAST":
        return "var(--ep-amber)"
    return "var(--ep-red)"


def render_lot_card(row):
    width = min(float(row["pct_full"]), 100.0)

    render_html(
        f"""
        <div class="ep-lot-card">
            <div class="ep-lot-head">
                <div>
                    <div class="ep-lot-name">{row["name"]}</div>
                    <div class="ep-lot-meta">
                        {row["permit_required"]} permit · {int(row["capacity"])} total spaces
                    </div>
                </div>
                <div class="ep-badge {status_class(row["status"])}">
                    {row["status"]}
                </div>
            </div>
            <div class="ep-progress">
                <div class="ep-progress-fill"
                     style="width:{width:.1f}%;background:{status_fill(row["status"])};">
                </div>
            </div>
            <div class="ep-lot-foot">
                <span>{row["pct_full"]:.0f}% occupied</span>
                <span><strong>{int(row["available"])}</strong> open</span>
            </div>
        </div>
        """
    )


def render_story_traceability(feature_name):
    stories = get_stories_for_feature(feature_name)

    if not stories:
        return

    with st.expander("User story traceability", expanded=False):
        st.caption(
            "These CSC 4610 user stories are connected to this part of the prototype."
        )

        for story in stories:
            render_html(
                f"""
                <div class="ep-story">
                    <div class="ep-story-id">
                        {story["id"]} · Board #{story["board_number"]} ·
                        Issue #{story["github_issue"]}
                    </div>
                    <div class="ep-story-text">{story["story"]}</div>
                </div>
                """
            )


def render_recommendation():
    if recommended_lot is None:
        st.info("This profile does not currently have Purple or Gold parking access.")
        return

    gps_link = (
        "https://www.google.com/maps/dir/?api=1"
        f"&destination={recommended_lot['lat']},{recommended_lot['lon']}"
        "&travelmode=driving"
    )

    render_html(
        f"""
        <div class="ep-rec">
            <div class="ep-rec-label">Recommended parking</div>
            <div class="ep-rec-name">{recommended_lot["name"]}</div>
            <div class="ep-rec-grid">
                <div class="ep-rec-stat">
                    <div class="ep-rec-stat-label">Open spaces</div>
                    <div class="ep-rec-stat-value">{int(recommended_lot["available"])}</div>
                </div>
                <div class="ep-rec-stat">
                    <div class="ep-rec-stat-label">Occupancy</div>
                    <div class="ep-rec-stat-value">{recommended_lot["pct_full"]:.0f}%</div>
                </div>
                <div class="ep-rec-stat">
                    <div class="ep-rec-stat-label">Permit</div>
                    <div class="ep-rec-stat-value">{recommended_lot["permit_required"]}</div>
                </div>
                <div class="ep-rec-stat">
                    <div class="ep-rec-stat-label">Walk estimate</div>
                    <div class="ep-rec-stat-value">~{recommended_lot["walk_mins"]} min</div>
                </div>
            </div>
        </div>
        """
    )

    st.link_button(
        f"Route to {recommended_lot['short_code']}",
        url=gps_link,
        use_container_width=True,
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
            layers=[
                satellite_tiles,
                building_nodes,
                lot_nodes,
                lot_labels,
            ],
            initial_view_state=deck_view,
            tooltip={
                "text": (
                    "{name}\nStatus: {status}\nOpen spaces: {available} / {capacity}"
                )
            },
        ),
        use_container_width=True,
    )


def render_two_column_lot_grid():
    rows = facilities_df.reset_index(drop=True)

    for start in range(0, len(rows), 2):
        columns = st.columns(2, gap="medium")

        for offset, column in enumerate(columns):
            index = start + offset

            if index < len(rows):
                with column:
                    render_lot_card(rows.iloc[index])


def render_lot_list():
    for _, row in facilities_df.iterrows():
        render_lot_card(row)


# Overview
if active_page == "Overview":
    render_hero(
        "Campus mobility at a glance",
        "Current parking pressure, permit-aware recommendations, and the "
        "conditions driving EaglePark decisions.",
    )

    total_capacity = int(facilities_df["capacity"].sum())
    total_available = int(facilities_df["available"].sum())
    campus_full_pct = (
        facilities_df["occupied"].sum() / facilities_df["capacity"].sum()
    ) * 100
    saturated_count = int((facilities_df["pct_full"] >= 90).sum())

    k1, k2, k3, k4 = st.columns(4, gap="medium")

    with k1:
        render_kpi("Campus capacity", f"{total_capacity:,}", "Tracked demo spaces")
    with k2:
        render_kpi("Open spaces", f"{total_available:,}", "Across all demo lots")
    with k3:
        render_kpi("Campus occupancy", f"{campus_full_pct:.0f}%", "Selected scenario")
    with k4:
        render_kpi("Saturated lots", str(saturated_count), "At or above 90%")

    main_left, main_right = st.columns([1.55, 1], gap="large")

    with main_left:
        render_html('<div class="ep-section-title">Parking conditions</div>')
        render_two_column_lot_grid()

    with main_right:
        render_html('<div class="ep-section-title">Best option for this profile</div>')
        render_recommendation()
        st.caption(
            "Recommendation uses permit access, occupancy, and walking distance."
        )

    render_story_traceability("Dashboard")


# Predictive Parking
elif active_page == "Predictive Parking":
    render_hero(
        "Predictive parking",
        "A forecast workspace designed to help commuters avoid lots that are "
        "likely to fill before they arrive.",
    )

    st.info(
        "This build shows the current occupancy baseline. "
        "The next feature adds the 20-minute forecast and projected-fill alert."
    )

    left, right = st.columns([0.9, 1.55], gap="large")

    with left:
        render_html('<div class="ep-section-title">Current occupancy</div>')
        render_lot_list()

    with right:
        render_html('<div class="ep-section-title">Campus view</div>')
        render_map()

    render_story_traceability("Predictive Parking")


# Smart Route
elif active_page == "Smart Route":
    render_hero(
        "Smart route",
        "Permit-aware parking guidance that reacts to campus saturation "
        "and suggests a practical arrival lot.",
    )

    left, right = st.columns([0.85, 1.55], gap="large")

    with left:
        render_html('<div class="ep-section-title">Route setup</div>')

        selected_destination = st.selectbox(
            "Campus destination",
            CAMPUS_LANDMARKS["name"].tolist(),
        )

        render_html('<div class="ep-section-title">Recommendation</div>')
        render_recommendation()

    with right:
        render_html('<div class="ep-section-title">Campus map</div>')
        render_map()

    render_html('<div class="ep-section-title">All parking lots</div>')
    render_two_column_lot_grid()

    render_story_traceability("Smart Route")


# RideShare
elif active_page == "RideShare":
    render_hero(
        "RideShare",
        "Planned commuter matching based on arrival time, destination, "
        "role, and proximity while keeping the user in control.",
    )

    st.info(
        "RideShare matching follows Predictive Parking in the build sequence. "
        "The page remains visible so the application matches the project epics."
    )

    left, right = st.columns(2, gap="large")

    with left:
        render_html('<div class="ep-section-title">Trip details</div>')
        st.text_input("Approximate origin / area", disabled=True)
        st.time_input("Target campus arrival", disabled=True)

    with right:
        render_html('<div class="ep-section-title">Match preferences</div>')
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
        "Planned: verified drivers, timetable/proximity matching, "
        "detour estimates, and Lab 5 failure tests."
    )

    render_story_traceability("RideShare")


# Operations
else:
    render_hero(
        "Operations & evaluation",
        "Administrative view for parking pressure, system evaluation, "
        "and the failure cases defined in the CSC 4610 labs.",
    )

    full_90 = int((facilities_df["pct_full"] >= 90).sum())
    full_75 = int((facilities_df["pct_full"] >= 75).sum())
    total_open = int(facilities_df["available"].sum())

    k1, k2, k3 = st.columns(3, gap="medium")

    with k1:
        render_kpi("Lots ≥ 90%", str(full_90), "Immediate attention")
    with k2:
        render_kpi("Lots ≥ 75%", str(full_75), "Filling or saturated")
    with k3:
        render_kpi("Open spaces", f"{total_open:,}", "Across all demo lots")

    left, right = st.columns(2, gap="large")

    with left:
        render_html('<div class="ep-section-title">Lab 5 evaluation</div>')
        st.info(
            "This area will display functional metrics, similarity metrics, "
            "the AI-judge criterion, and failure-case results."
        )

    with right:
        render_html('<div class="ep-section-title">Failure tests</div>')
        st.markdown(
            """
            1. Invalid or non-existent rideshare recommendation.
            2. A matched participant is flagged as a no-show.
            3. A removed rideshare user is still recommended.
            4. Parking data is stale, unavailable, or incorrect.
            """
        )

    render_html('<div class="ep-section-title">Current lot pressure</div>')
    render_two_column_lot_grid()

    render_story_traceability("Admin & Evaluation")
