# app/app.py
"""
EaglePark AI prototype.

Desktop-first Streamlit interface for smart parking, routing,
RideShare matching, and operational evaluation.
"""

import math
import sys
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st


# Project imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

try:
    from user_stories import USER_STORIES, get_stories_for_feature
except ImportError:
    USER_STORIES = []

    def get_stories_for_feature(feature_name):
        return []


# Page setup
st.set_page_config(
    page_title="EaglePark AI",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Demo profiles
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


# Simulated RideShare users
RIDESHARE_USERS = [
    {
        "id": "RS-101",
        "name": "Jordan Smith",
        "role": "Student",
        "mode": "Offering a ride",
        "origin": "Algood",
        "arrival": "08:45",
        "destination": "Ashraf Islam Eng Building (AIEB)",
        "verified": True,
        "rating": 4.9,
        "detour_mins": 3.0,
        "vehicle": "Gray Honda Civic",
        "seats": 2,
    },
    {
        "id": "RS-102",
        "name": "Maya Chen",
        "role": "Student",
        "mode": "Offering a ride",
        "origin": "West Cookeville",
        "arrival": "08:50",
        "destination": "Volpe Library",
        "verified": True,
        "rating": 4.8,
        "detour_mins": 4.2,
        "vehicle": "Blue Toyota Corolla",
        "seats": 1,
    },
    {
        "id": "RS-103",
        "name": "Ethan Brooks",
        "role": "Student",
        "mode": "Offering a ride",
        "origin": "East Cookeville",
        "arrival": "09:05",
        "destination": "Prescott Hall",
        "verified": True,
        "rating": 4.7,
        "detour_mins": 2.6,
        "vehicle": "Black Ford Escape",
        "seats": 3,
    },
    {
        "id": "RS-104",
        "name": "Dr. Lena Ortiz",
        "role": "Faculty / Staff",
        "mode": "Offering a ride",
        "origin": "North Cookeville",
        "arrival": "08:40",
        "destination": "Prescott Hall",
        "verified": True,
        "rating": 4.9,
        "detour_mins": 4.0,
        "vehicle": "White Subaru Outback",
        "seats": 2,
    },
    {
        "id": "RS-105",
        "name": "Prof. Daniel Reed",
        "role": "Faculty / Staff",
        "mode": "Offering a ride",
        "origin": "Algood",
        "arrival": "08:55",
        "destination": "Stonecipher Hall (LSC)",
        "verified": True,
        "rating": 4.8,
        "detour_mins": 3.4,
        "vehicle": "Silver Hyundai Tucson",
        "seats": 1,
    },
    {
        "id": "RS-201",
        "name": "Priya Nair",
        "role": "Student",
        "mode": "Need a ride",
        "origin": "South Cookeville",
        "arrival": "08:48",
        "destination": "Ashraf Islam Eng Building (AIEB)",
        "verified": True,
        "rating": 4.9,
        "detour_mins": 2.8,
        "vehicle": "",
        "seats": 0,
    },
    {
        "id": "RS-202",
        "name": "Noah Walker",
        "role": "Student",
        "mode": "Need a ride",
        "origin": "Downtown Cookeville",
        "arrival": "09:00",
        "destination": "Bell Hall",
        "verified": True,
        "rating": 4.7,
        "detour_mins": 3.2,
        "vehicle": "",
        "seats": 0,
    },
    {
        "id": "RS-203",
        "name": "Dr. Avery Hall",
        "role": "Faculty / Staff",
        "mode": "Need a ride",
        "origin": "North Cookeville",
        "arrival": "08:50",
        "destination": "Stonecipher Hall (LSC)",
        "verified": True,
        "rating": 4.9,
        "detour_mins": 2.5,
        "vehicle": "",
        "seats": 0,
    },
]

ZONE_COORDS = {
    "Algood": (1.0, 2.0),
    "North Cookeville": (0.0, 2.2),
    "West Cookeville": (-2.0, 0.4),
    "East Cookeville": (2.1, 0.2),
    "South Cookeville": (0.2, -2.0),
    "Downtown Cookeville": (0.0, 0.0),
}


# Campus destinations
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


# Simulated parking data
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

    def get_color(pct):
        if pct >= 90:
            return [255, 82, 94, 235]
        if pct >= 75:
            return [245, 177, 50, 235]
        return [31, 199, 128, 235]

    df["status"] = df["pct_full"].apply(get_status)
    df["color"] = df["pct_full"].apply(get_color)
    df["map_label"] = df.apply(
        lambda row: f"{row['short_code']} · {row['pct_full']:.0f}% · {row['available']} open",
        axis=1,
    )
    return df


# Simple 20-minute forecast used by the prototype
def add_forecast(facilities_df, preset):
    df = facilities_df.copy()

    if "Morning Peak" in preset:
        change = [4.0, 3.0, 5.5, 2.0, 8.0, 5.0]
    elif "Transition" in preset:
        change = [-2.0, -1.0, 2.5, 0.5, 1.5, 1.0]
    elif "Event" in preset:
        change = [1.0, 1.0, 1.5, 1.0, 1.0, 2.5]
    else:
        change = [-4.0, -3.5, -3.0, -2.0, -2.5, -2.0]

    df["forecast_change"] = change
    df["forecast_pct"] = (df["pct_full"] + df["forecast_change"]).clip(0, 100)
    df["forecast_available"] = (
        df["capacity"] * (1 - (df["forecast_pct"] / 100))
    ).round().astype(int)

    return df


def recommend_lot(facilities_df, permit):
    if permit not in {"Purple", "Gold"}:
        return None

    permitted = facilities_df[
        facilities_df["permit_required"] == permit
    ].copy()

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


# Theme state
if "app_theme" not in st.session_state:
    st.session_state.app_theme = "Dark"

if "nav_page" not in st.session_state:
    st.session_state.nav_page = "Overview"

light_mode = st.sidebar.toggle(
    "Light mode",
    value=st.session_state.app_theme == "Light",
    help="Switch the complete EaglePark interface between light and dark mode.",
)
st.session_state.app_theme = "Light" if light_mode else "Dark"


# Theme colors
if st.session_state.app_theme == "Dark":
    theme = {
        "scheme": "dark",
        "bg": "#07101C",
        "sidebar": "#091423",
        "panel": "#0E1A2A",
        "panel_2": "#122238",
        "panel_3": "#172940",
        "border": "#253A54",
        "text": "#F7FAFE",
        "muted": "#9CADC3",
        "purple": "#A96EFF",
        "purple_2": "#6C35D4",
        "gold": "#F7C945",
        "green": "#22C989",
        "amber": "#F1B632",
        "red": "#FF5A67",
        "blue": "#4D9CFF",
        "input": "#101F33",
        "track": "#20344D",
        "shadow": "0 18px 50px rgba(0,0,0,.32)",
    }
else:
    theme = {
        "scheme": "light",
        "bg": "#F3F6FB",
        "sidebar": "#FFFFFF",
        "panel": "#FFFFFF",
        "panel_2": "#F8FAFD",
        "panel_3": "#EEF3F9",
        "border": "#D4DFEB",
        "text": "#172033",
        "muted": "#63748A",
        "purple": "#7040C5",
        "purple_2": "#4F2984",
        "gold": "#8A6500",
        "green": "#157A50",
        "amber": "#996000",
        "red": "#B42318",
        "blue": "#2368C4",
        "input": "#FFFFFF",
        "track": "#E2E9F1",
        "shadow": "0 14px 36px rgba(18,35,58,.09)",
    }


# Global UI styling
st.markdown(
    f"""
    <style>
        :root {{
            color-scheme: {theme["scheme"]};
            --ep-bg: {theme["bg"]};
            --ep-sidebar: {theme["sidebar"]};
            --ep-panel: {theme["panel"]};
            --ep-panel-2: {theme["panel_2"]};
            --ep-panel-3: {theme["panel_3"]};
            --ep-border: {theme["border"]};
            --ep-text: {theme["text"]};
            --ep-muted: {theme["muted"]};
            --ep-purple: {theme["purple"]};
            --ep-purple-2: {theme["purple_2"]};
            --ep-gold: {theme["gold"]};
            --ep-green: {theme["green"]};
            --ep-amber: {theme["amber"]};
            --ep-red: {theme["red"]};
            --ep-blue: {theme["blue"]};
            --ep-input: {theme["input"]};
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
            width: min(100%, 1540px) !important;
            max-width: 1540px !important;
            padding: 1.05rem 1.65rem 2.5rem !important;
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

        /* AI-inspired EaglePark brand mark */
        .ep-brand {{
            border: 1px solid var(--ep-border);
            border-radius: 20px;
            background:
                radial-gradient(circle at 50% 12%, rgba(169,110,255,.18), transparent 35%),
                linear-gradient(160deg, rgba(108,53,212,.16), transparent 64%),
                var(--ep-panel);
            padding: .9rem .85rem .95rem;
            margin: .2rem 0 1.1rem;
            box-shadow: var(--ep-shadow);
            overflow: hidden;
        }}

        .ep-brand-row {{
            display: flex;
            align-items: center;
            gap: .8rem;
        }}

        .ep-brand-mark {{
            width: 72px;
            height: 72px;
            flex: 0 0 72px;
        }}

        .ep-brand-title {{
            color: var(--ep-text);
            font-size: 1.18rem;
            font-weight: 900;
            line-height: 1.05;
        }}

        .ep-brand-ai {{
            color: var(--ep-gold);
        }}

        .ep-brand-sub {{
            color: var(--ep-muted);
            font-size: .72rem;
            margin-top: .26rem;
            line-height: 1.35;
        }}

        /* Sidebar navigation */
        section[data-testid="stSidebar"] div[role="radiogroup"] {{
            gap: .32rem;
        }}

        section[data-testid="stSidebar"] div[role="radiogroup"] label {{
            border: 1px solid transparent;
            border-radius: 11px;
            padding: .43rem .55rem;
            transition: .18s ease;
        }}

        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
            background: var(--ep-panel-2);
            border-color: var(--ep-border);
        }}

        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
            background: linear-gradient(
                90deg,
                rgba(108,53,212,.50),
                rgba(169,110,255,.16)
            );
            border-color: rgba(169,110,255,.52);
        }}

        /* Hero header */
        .ep-hero {{
            position: relative;
            overflow: hidden;
            border: 1px solid var(--ep-border);
            border-radius: 22px;
            background:
                radial-gradient(circle at 82% 4%, rgba(169,110,255,.23), transparent 31%),
                radial-gradient(circle at 92% 82%, rgba(247,201,69,.10), transparent 24%),
                linear-gradient(135deg, rgba(108,53,212,.12), transparent 60%),
                var(--ep-panel);
            padding: 1.3rem 1.5rem;
            margin-bottom: 1rem;
            box-shadow: var(--ep-shadow);
        }}

        .ep-hero::after {{
            content: "";
            position: absolute;
            right: -55px;
            top: -74px;
            width: 240px;
            height: 240px;
            border-radius: 50%;
            border: 1px solid rgba(169,110,255,.18);
            box-shadow:
                0 0 0 34px rgba(169,110,255,.025),
                0 0 0 68px rgba(169,110,255,.018);
        }}

        .ep-hero-row {{
            position: relative;
            z-index: 2;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
        }}

        .ep-kicker {{
            color: var(--ep-gold);
            font-size: .72rem;
            font-weight: 850;
            letter-spacing: .11em;
            text-transform: uppercase;
            margin-bottom: .34rem;
        }}

        .ep-title {{
            color: var(--ep-text);
            font-size: clamp(1.8rem, 2.6vw, 2.75rem);
            font-weight: 900;
            letter-spacing: -.038em;
            line-height: 1;
            margin: 0;
        }}

        .ep-subtitle {{
            color: var(--ep-muted);
            max-width: 800px;
            margin-top: .55rem;
            font-size: .92rem;
            line-height: 1.55;
        }}

        .ep-campus-chip {{
            flex: 0 0 auto;
            border: 1px solid var(--ep-border);
            border-radius: 999px;
            background: var(--ep-panel-2);
            color: var(--ep-text);
            padding: .58rem .8rem;
            font-size: .74rem;
            font-weight: 800;
        }}

        /* Section text */
        .ep-section-title {{
            color: var(--ep-text);
            font-size: 1.08rem;
            font-weight: 850;
            margin: .32rem 0 .72rem;
        }}

        .ep-section-sub {{
            color: var(--ep-muted);
            font-size: .78rem;
            margin-top: -.4rem;
            margin-bottom: .75rem;
        }}

        /* KPI cards */
        .ep-kpi {{
            min-height: 116px;
            border: 1px solid var(--ep-border);
            border-radius: 17px;
            background: linear-gradient(145deg, var(--ep-panel), var(--ep-panel-2));
            padding: .9rem 1rem;
            box-shadow: 0 8px 24px rgba(0,0,0,.05);
        }}

        .ep-kpi-row {{
            display: flex;
            align-items: center;
            gap: .75rem;
        }}

        .ep-kpi-icon {{
            width: 46px;
            height: 46px;
            flex: 0 0 46px;
            border-radius: 13px;
            display: grid;
            place-items: center;
            color: #FFFFFF;
            font-size: 1.2rem;
            font-weight: 900;
        }}

        .ep-icon-purple {{
            background: linear-gradient(145deg, #6C35D4, #A96EFF);
        }}

        .ep-icon-green {{
            background: linear-gradient(145deg, #0D744D, #22C989);
        }}

        .ep-icon-gold {{
            background: linear-gradient(145deg, #89600A, #F1B632);
        }}

        .ep-icon-red {{
            background: linear-gradient(145deg, #9D2831, #FF5A67);
        }}

        .ep-kpi-label {{
            color: var(--ep-muted);
            font-size: .71rem;
            font-weight: 720;
        }}

        .ep-kpi-value {{
            color: var(--ep-text);
            font-size: 1.65rem;
            font-weight: 900;
            line-height: 1;
            margin-top: .23rem;
        }}

        .ep-kpi-note {{
            color: var(--ep-muted);
            font-size: .65rem;
            margin-top: .37rem;
        }}

        /* Main panels */
        .ep-panel {{
            border: 1px solid var(--ep-border);
            border-radius: 18px;
            background: var(--ep-panel);
            padding: .9rem 1rem;
            box-shadow: 0 8px 24px rgba(0,0,0,.05);
        }}

        /* Parking rows */
        .ep-lot-row {{
            border: 1px solid var(--ep-border);
            border-radius: 15px;
            background: var(--ep-panel-2);
            padding: .78rem .85rem;
            margin-bottom: .55rem;
        }}

        .ep-lot-head {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: .75rem;
        }}

        .ep-lot-name {{
            color: var(--ep-text);
            font-size: .88rem;
            font-weight: 820;
            line-height: 1.3;
        }}

        .ep-lot-meta {{
            color: var(--ep-muted);
            font-size: .68rem;
            margin-top: .2rem;
        }}

        .ep-badge {{
            flex: 0 0 auto;
            border: 1px solid var(--ep-border);
            border-radius: 999px;
            padding: .27rem .5rem;
            font-size: .61rem;
            font-weight: 900;
            white-space: nowrap;
        }}

        .ep-badge-good {{
            color: var(--ep-green);
            background: rgba(34,201,137,.10);
        }}

        .ep-badge-warn {{
            color: var(--ep-amber);
            background: rgba(241,182,50,.10);
        }}

        .ep-badge-bad {{
            color: var(--ep-red);
            background: rgba(255,90,103,.10);
        }}

        .ep-lot-stats {{
            display: grid;
            grid-template-columns: 74px 1fr 70px;
            align-items: center;
            gap: .62rem;
            margin-top: .62rem;
        }}

        .ep-occupancy {{
            color: var(--ep-text);
            font-size: .76rem;
            font-weight: 850;
        }}

        .ep-progress {{
            height: 8px;
            border-radius: 999px;
            background: var(--ep-track);
            overflow: hidden;
        }}

        .ep-progress-fill {{
            height: 100%;
            border-radius: 999px;
        }}

        .ep-open {{
            color: var(--ep-muted);
            font-size: .69rem;
            text-align: right;
        }}

        /* Recommendation */
        .ep-rec {{
            border: 1px solid rgba(169,110,255,.32);
            border-radius: 18px;
            background:
                linear-gradient(145deg, rgba(108,53,212,.18), transparent 65%),
                var(--ep-panel);
            padding: 1rem;
            box-shadow: 0 8px 24px rgba(0,0,0,.05);
        }}

        .ep-rec-label {{
            color: var(--ep-gold);
            font-size: .65rem;
            font-weight: 900;
            letter-spacing: .08em;
            text-transform: uppercase;
        }}

        .ep-rec-name {{
            color: var(--ep-text);
            font-size: 1.15rem;
            font-weight: 900;
            margin-top: .35rem;
        }}

        .ep-rec-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: .48rem;
            margin-top: .8rem;
        }}

        .ep-rec-stat {{
            border: 1px solid var(--ep-border);
            border-radius: 11px;
            background: var(--ep-panel-2);
            padding: .58rem;
        }}

        .ep-rec-stat-label {{
            color: var(--ep-muted);
            font-size: .59rem;
            font-weight: 700;
        }}

        .ep-rec-stat-value {{
            color: var(--ep-text);
            font-size: .82rem;
            font-weight: 850;
            margin-top: .15rem;
        }}

        /* Quick action cards */
        .ep-action-card {{
            border: 1px solid var(--ep-border);
            border-radius: 16px;
            background: var(--ep-panel);
            padding: .85rem .9rem;
            min-height: 104px;
            margin-bottom: .35rem;
        }}

        .ep-action-title {{
            color: var(--ep-text);
            font-size: .82rem;
            font-weight: 850;
        }}

        .ep-action-copy {{
            color: var(--ep-muted);
            font-size: .67rem;
            line-height: 1.45;
            margin-top: .3rem;
        }}

        /* Traceability */
        .ep-trace-banner {{
            border: 1px solid rgba(169,110,255,.40);
            border-radius: 16px;
            background:
                linear-gradient(90deg, rgba(108,53,212,.24), rgba(169,110,255,.08)),
                var(--ep-panel);
            padding: .82rem .95rem;
            margin-top: .45rem;
        }}

        .ep-trace-title {{
            color: var(--ep-text);
            font-size: .86rem;
            font-weight: 850;
        }}

        .ep-trace-copy {{
            color: var(--ep-muted);
            font-size: .68rem;
            margin-top: .18rem;
        }}

        .ep-story {{
            border: 1px solid var(--ep-border);
            border-radius: 12px;
            background: var(--ep-panel-2);
            padding: .72rem .8rem;
            margin-bottom: .48rem;
        }}

        .ep-story-id {{
            color: var(--ep-purple);
            font-size: .62rem;
            font-weight: 900;
            letter-spacing: .05em;
            margin-bottom: .25rem;
        }}

        .ep-story-text {{
            color: var(--ep-text);
            font-size: .77rem;
            line-height: 1.45;
        }}

        /* RideShare */
        .ep-match-card {{
            border: 1px solid var(--ep-border);
            border-radius: 17px;
            background:
                linear-gradient(145deg, rgba(108,53,212,.10), transparent 62%),
                var(--ep-panel);
            padding: .9rem;
            margin-bottom: .65rem;
        }}

        .ep-match-head {{
            display: flex;
            justify-content: space-between;
            gap: .8rem;
            align-items: flex-start;
        }}

        .ep-match-name {{
            color: var(--ep-text);
            font-size: .94rem;
            font-weight: 880;
        }}

        .ep-match-meta {{
            color: var(--ep-muted);
            font-size: .68rem;
            line-height: 1.4;
            margin-top: .2rem;
        }}

        .ep-score {{
            flex: 0 0 auto;
            min-width: 60px;
            text-align: center;
            border-radius: 13px;
            border: 1px solid rgba(169,110,255,.34);
            background: rgba(108,53,212,.12);
            padding: .45rem .52rem;
        }}

        .ep-score-value {{
            color: var(--ep-purple);
            font-size: 1.02rem;
            font-weight: 900;
        }}

        .ep-score-label {{
            color: var(--ep-muted);
            font-size: .55rem;
            font-weight: 760;
            text-transform: uppercase;
            letter-spacing: .05em;
        }}

        .ep-match-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: .42rem;
            margin-top: .72rem;
        }}

        .ep-match-stat {{
            border: 1px solid var(--ep-border);
            border-radius: 10px;
            background: var(--ep-panel-2);
            padding: .5rem;
        }}

        .ep-match-stat-label {{
            color: var(--ep-muted);
            font-size: .56rem;
            font-weight: 700;
        }}

        .ep-match-stat-value {{
            color: var(--ep-text);
            font-size: .73rem;
            font-weight: 830;
            margin-top: .14rem;
        }}

        /* Native controls */
        section[data-testid="stSidebar"] [data-baseweb="select"] > div,
        section[data-testid="stSidebar"] [data-baseweb="base-input"],
        section[data-testid="stSidebar"] input,
        [data-testid="stMain"] [data-baseweb="select"] > div,
        [data-testid="stMain"] [data-baseweb="base-input"],
        [data-testid="stMain"] input {{
            background: var(--ep-input) !important;
            border-color: var(--ep-border) !important;
            color: var(--ep-text) !important;
        }}

        section[data-testid="stSidebar"] [data-baseweb="select"] *,
        [data-testid="stMain"] [data-baseweb="select"] * {{
            color: var(--ep-text) !important;
        }}

        section[data-testid="stSidebar"] input,
        [data-testid="stMain"] input {{
            -webkit-text-fill-color: var(--ep-text) !important;
            opacity: 1 !important;
        }}

        div[data-baseweb="popover"],
        div[data-baseweb="menu"],
        [role="listbox"],
        [role="option"],
        [role="option"] * {{
            background: var(--ep-panel) !important;
            color: var(--ep-text) !important;
        }}

        [role="option"]:hover,
        [role="option"]:hover * {{
            background: var(--ep-panel-3) !important;
        }}

        div[data-testid="stExpander"] {{
            border: 1px solid var(--ep-border) !important;
            border-radius: 13px !important;
            background: var(--ep-panel) !important;
            overflow: hidden;
        }}

        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary * {{
            color: var(--ep-text) !important;
        }}

        div[data-testid="stAlert"] {{
            border-radius: 12px !important;
            border: 1px solid var(--ep-border) !important;
        }}

        .stButton > button,
        .stLinkButton > a {{
            min-height: 2.55rem;
            border-radius: 10px !important;
            background: linear-gradient(
                135deg,
                var(--ep-purple-2),
                var(--ep-purple)
            ) !important;
            color: #FFFFFF !important;
            border: 0 !important;
            font-weight: 800 !important;
            box-shadow: 0 7px 18px rgba(79,41,132,.18);
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

        /* Map */
        .stDeckGlJsonChart {{
            min-height: 480px;
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid var(--ep-border);
            background: var(--ep-panel);
            box-shadow: 0 8px 24px rgba(0,0,0,.06);
        }}

        [data-testid="stToolbar"] {{
            opacity: .28;
        }}

        @media (max-width: 980px) {{
            [data-testid="stAppViewBlockContainer"] {{
                padding: .9rem .85rem 2rem !important;
            }}

            .ep-hero-row {{
                align-items: flex-start;
                flex-wrap: wrap;
            }}

            .ep-match-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}

            .stDeckGlJsonChart {{
                min-height: 390px;
            }}
        }}

        @media (max-width: 640px) {{
            [data-testid="stAppViewBlockContainer"] {{
                padding: .6rem .6rem 1.4rem !important;
            }}

            .ep-brand-mark {{
                width: 58px;
                height: 58px;
                flex-basis: 58px;
            }}

            .ep-hero {{
                padding: 1rem;
                border-radius: 16px;
            }}

            .ep-title {{
                font-size: 1.48rem;
            }}

            .ep-campus-chip {{
                width: fit-content;
            }}

            .ep-rec-grid,
            .ep-match-grid {{
                grid-template-columns: 1fr 1fr;
            }}

            .stDeckGlJsonChart {{
                min-height: 330px;
            }}
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# Prevent multiline HTML from being rendered as code.
def render_html(html):
    compact = " ".join(line.strip() for line in html.splitlines())
    st.markdown(compact, unsafe_allow_html=True)


# AI-inspired sidebar logo
def render_brand():
    render_html(
        """
        <div class="ep-brand">
            <div class="ep-brand-row">
                <svg class="ep-brand-mark" viewBox="0 0 120 120" aria-label="EaglePark AI logo">
                    <defs>
                        <linearGradient id="epg" x1="0" x2="1" y1="0" y2="1">
                            <stop offset="0%" stop-color="#5A239A"/>
                            <stop offset="100%" stop-color="#2D1358"/>
                        </linearGradient>
                    </defs>
                    <rect x="3" y="3" width="114" height="114" rx="28"
                          fill="url(#epg)" stroke="#F7C945" stroke-width="2"/>
                    <path d="M58 55 L35 36 L20 40 L41 59 L23 68 L50 65"
                          fill="none" stroke="#F7C945" stroke-width="5"
                          stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M62 55 L85 36 L100 40 L79 59 L97 68 L70 65"
                          fill="none" stroke="#F7C945" stroke-width="5"
                          stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M60 40 L72 53 L60 67 L48 53 Z"
                          fill="#F7C945"/>
                    <path d="M60 67 L76 82 L60 78 L44 82 Z"
                          fill="#A96EFF"/>
                    <path d="M60 31 V18 M34 31 L27 20 M86 31 L93 20"
                          fill="none" stroke="#A96EFF" stroke-width="3"
                          stroke-linecap="round"/>
                    <circle cx="60" cy="15" r="5" fill="#F7C945"/>
                    <circle cx="24" cy="17" r="4" fill="#A96EFF"/>
                    <circle cx="96" cy="17" r="4" fill="#A96EFF"/>
                    <circle cx="20" cy="40" r="4" fill="#A96EFF"/>
                    <circle cx="100" cy="40" r="4" fill="#A96EFF"/>
                </svg>
                <div>
                    <div class="ep-brand-title">
                        EaglePark <span class="ep-brand-ai">AI</span>
                    </div>
                    <div class="ep-brand-sub">
                        Smart. Connected. Forward.
                    </div>
                </div>
            </div>
        </div>
        """
    )


def go_to(page):
    st.session_state.nav_page = page


# Sidebar
render_brand()

st.sidebar.markdown("### Navigation")
active_page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Predictive Parking", "Smart Route", "RideShare", "Operations"],
    key="nav_page",
    label_visibility="collapsed",
)

st.sidebar.divider()
st.sidebar.markdown("### User Profile")

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
    f"{user_permit} Permit"
    if user_permit in {"Purple", "Gold"}
    else "No Campus Permit"
)
st.sidebar.caption(f"Permit Tier: **{permit_text}**")

st.sidebar.divider()
st.sidebar.markdown("### Traffic Scenario")

traffic_preset = st.sidebar.selectbox(
    "Scenario",
    [
        "Morning Peak (07:30 - 09:00)",
        "Midday Transition (11:00 - 13:00)",
        "Afternoon / Evening (Low Traffic)",
        "Event Saturation (Game Day)",
    ],
    label_visibility="collapsed",
)

st.sidebar.caption("Prototype values are simulated for demonstration.")

facilities_df = get_ttu_facilities(traffic_preset)
forecast_df = add_forecast(facilities_df, traffic_preset)
recommended_lot = recommend_lot(facilities_df, user_permit)


# UI helpers
def render_hero(title, subtitle):
    render_html(
        f"""
        <div class="ep-hero">
            <div class="ep-hero-row">
                <div>
                    <div class="ep-kicker">EaglePark AI · Smart Campus Mobility</div>
                    <h1 class="ep-title">{title}</h1>
                    <div class="ep-subtitle">{subtitle}</div>
                </div>
                <div class="ep-campus-chip">◉ Tennessee Tech</div>
            </div>
        </div>
        """
    )


def render_kpi(icon, icon_class, label, value, note):
    render_html(
        f"""
        <div class="ep-kpi">
            <div class="ep-kpi-row">
                <div class="ep-kpi-icon {icon_class}">{icon}</div>
                <div>
                    <div class="ep-kpi-label">{label}</div>
                    <div class="ep-kpi-value">{value}</div>
                    <div class="ep-kpi-note">{note}</div>
                </div>
            </div>
        </div>
        """
    )


def badge_class(status):
    if status == "AVAILABLE":
        return "ep-badge-good"
    if status == "FILLING FAST":
        return "ep-badge-warn"
    return "ep-badge-bad"


def fill_color(status):
    if status == "AVAILABLE":
        return "var(--ep-green)"
    if status == "FILLING FAST":
        return "var(--ep-amber)"
    return "var(--ep-red)"


def render_lot_row(row, predicted_pct=None, predicted_open=None):
    status = row["status"]

    forecast_note = ""
    if predicted_pct is not None and predicted_open is not None:
        forecast_note = (
            f" · +20 min: {predicted_pct:.0f}% / {int(predicted_open)} open"
        )

    render_html(
        f"""
        <div class="ep-lot-row">
            <div class="ep-lot-head">
                <div>
                    <div class="ep-lot-name">{row["name"]}</div>
                    <div class="ep-lot-meta">
                        {row["permit_required"]} permit ·
                        {int(row["occupied"])} / {int(row["capacity"])}
                        {forecast_note}
                    </div>
                </div>
                <div class="ep-badge {badge_class(status)}">{status}</div>
            </div>
            <div class="ep-lot-stats">
                <div class="ep-occupancy">{row["pct_full"]:.0f}%</div>
                <div class="ep-progress">
                    <div class="ep-progress-fill"
                         style="width:{min(float(row["pct_full"]), 100):.1f}%;
                                background:{fill_color(status)};">
                    </div>
                </div>
                <div class="ep-open">{int(row["available"])} open</div>
            </div>
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


def render_map(dataframe):
    if st.session_state.app_theme == "Dark":
        tile_url = "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"
        label_color = [245, 248, 252, 255]
        label_bg = [7, 16, 28, 225]
    else:
        tile_url = "https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"
        label_color = [23, 32, 51, 255]
        label_bg = [255, 255, 255, 225]

    tiles = pdk.Layer(
        "TileLayer",
        data=tile_url,
        min_zoom=0,
        max_zoom=20,
        tile_size=256,
        pickable=False,
    )

    lots = pdk.Layer(
        "ScatterplotLayer",
        data=dataframe,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius=24,
        radius_min_pixels=9,
        radius_max_pixels=17,
        pickable=True,
        auto_highlight=True,
    )

    labels = pdk.Layer(
        "TextLayer",
        data=dataframe,
        get_position=["lon", "lat"],
        get_text="map_label",
        get_color=label_color,
        get_size=11,
        get_alignment_baseline="'bottom'",
        get_pixel_offset=[0, -15],
        background=True,
        get_background_color=label_bg,
        pickable=False,
    )

    buildings = pdk.Layer(
        "ScatterplotLayer",
        data=CAMPUS_LANDMARKS,
        get_position=["lon", "lat"],
        get_color=[77, 156, 255, 215],
        get_radius=13,
        radius_min_pixels=5,
        radius_max_pixels=8,
        pickable=True,
    )

    view = pdk.ViewState(
        latitude=36.1775,
        longitude=-85.5058,
        zoom=15.5,
        pitch=0,
        bearing=0,
    )

    st.pydeck_chart(
        pdk.Deck(
            map_style=None,
            layers=[tiles, buildings, lots, labels],
            initial_view_state=view,
            tooltip={
                "text": "{name}\nStatus: {status}\nOpen spaces: {available} / {capacity}"
            },
        ),
        use_container_width=True,
    )


def render_traceability(feature_name, epic_label, show_all=False):
    stories = USER_STORIES if show_all else get_stories_for_feature(feature_name)
    count = len(stories)

    render_html(
        f"""
        <div class="ep-trace-banner">
            <div class="ep-trace-title">▣ Project Traceability</div>
            <div class="ep-trace-copy">
                {epic_label} · {count} user stories connected to this view.
            </div>
        </div>
        """
    )

    if count:
        with st.expander("View user stories", expanded=False):
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


# RideShare scoring helpers
def time_to_minutes(value):
    return (value.hour * 60) + value.minute


def parse_time(value):
    hour, minute = value.split(":")
    return (int(hour) * 60) + int(minute)


def zone_distance_km(zone_a, zone_b):
    ax, ay = ZONE_COORDS[zone_a]
    bx, by = ZONE_COORDS[zone_b]
    return math.dist((ax, ay), (bx, by)) * 2.2


def rideshare_matches(
    request_mode,
    origin,
    arrival_time,
    destination,
    group_filter,
    max_detour,
):
    wanted_mode = "Offering a ride" if request_mode == "Need a ride" else "Need a ride"
    request_minutes = time_to_minutes(arrival_time)
    results = []

    for person in RIDESHARE_USERS:
        if person["mode"] != wanted_mode:
            continue

        if group_filter != "Any eligible user" and person["role"] != group_filter:
            continue

        if person["detour_mins"] > max_detour:
            continue

        time_diff = abs(parse_time(person["arrival"]) - request_minutes)
        distance_km = zone_distance_km(origin, person["origin"])

        time_score = max(0.0, 30.0 - (time_diff * 1.5))
        origin_score = max(0.0, 25.0 - (distance_km * 4.0))
        destination_score = 20.0 if person["destination"] == destination else 8.0
        preference_score = 10.0 if group_filter != "Any eligible user" else 7.0
        verified_score = 10.0 if person["verified"] else 0.0
        detour_score = max(0.0, 5.0 - person["detour_mins"])

        score = min(
            100.0,
            time_score
            + origin_score
            + destination_score
            + preference_score
            + verified_score
            + detour_score,
        )

        match = dict(person)
        match["score"] = int(round(score))
        match["time_diff"] = int(time_diff)
        match["distance_km"] = round(distance_km, 1)
        results.append(match)

    return sorted(results, key=lambda item: item["score"], reverse=True)


def render_match_card(match, request_mode):
    relationship = "Driver" if request_mode == "Need a ride" else "Rider"
    vehicle = f" · {match['vehicle']}" if match["vehicle"] else ""

    render_html(
        f"""
        <div class="ep-match-card">
            <div class="ep-match-head">
                <div>
                    <div class="ep-match-name">{match["name"]}</div>
                    <div class="ep-match-meta">
                        {relationship} · {match["role"]}{vehicle}<br>
                        {match["origin"]} → {match["destination"]}<br>
                        Verified profile · {match["rating"]:.1f} rating
                    </div>
                </div>
                <div class="ep-score">
                    <div class="ep-score-value">{match["score"]}%</div>
                    <div class="ep-score-label">match</div>
                </div>
            </div>
            <div class="ep-match-grid">
                <div class="ep-match-stat">
                    <div class="ep-match-stat-label">Arrival</div>
                    <div class="ep-match-stat-value">{match["arrival"]}</div>
                </div>
                <div class="ep-match-stat">
                    <div class="ep-match-stat-label">Time difference</div>
                    <div class="ep-match-stat-value">{match["time_diff"]} min</div>
                </div>
                <div class="ep-match-stat">
                    <div class="ep-match-stat-label">Origin distance</div>
                    <div class="ep-match-stat-value">{match["distance_km"]} km</div>
                </div>
                <div class="ep-match-stat">
                    <div class="ep-match-stat-label">Pickup detour</div>
                    <div class="ep-match-stat-value">~{match["detour_mins"]} min</div>
                </div>
            </div>
        </div>
        """
    )


# Overview
if active_page == "Overview":
    render_hero(
        "Smarter parking. Better routes. Connected commuters.",
        "A unified campus mobility view for parking pressure, route guidance, "
        "RideShare coordination, and operational awareness.",
    )

    total_capacity = int(facilities_df["capacity"].sum())
    total_available = int(facilities_df["available"].sum())
    campus_full_pct = (
        facilities_df["occupied"].sum() / facilities_df["capacity"].sum()
    ) * 100
    saturated_count = int((facilities_df["pct_full"] >= 90).sum())

    k1, k2, k3, k4 = st.columns(4, gap="medium")
    with k1:
        render_kpi("▣", "ep-icon-purple", "Campus Capacity", f"{total_capacity:,}", "Tracked spaces")
    with k2:
        render_kpi("P", "ep-icon-green", "Open Spaces", f"{total_available:,}", "Current scenario")
    with k3:
        render_kpi("↗", "ep-icon-gold", "Campus Occupancy", f"{campus_full_pct:.0f}%", "Across demo lots")
    with k4:
        render_kpi("!", "ep-icon-red", "Saturated Lots", str(saturated_count), "At or above 90%")

    left, right = st.columns([1.15, 1.0], gap="large")

    with left:
        render_html('<div class="ep-section-title">Parking Status</div>')
        for _, row in facilities_df.head(5).iterrows():
            render_lot_row(row)

    with right:
        render_html('<div class="ep-section-title">Campus Map</div>')
        render_map(facilities_df)

    render_html('<div class="ep-section-title">Quick Actions</div>')

    a1, a2, a3, a4 = st.columns(4, gap="medium")

    with a1:
        render_html(
            """
            <div class="ep-action-card">
                <div class="ep-action-title">▥ Predictive Parking</div>
                <div class="ep-action-copy">
                    See 20-minute forecasts and projected fill warnings.
                </div>
            </div>
            """
        )
        st.button(
            "Open forecast",
            use_container_width=True,
            key="qa_predictive",
            on_click=go_to,
            args=("Predictive Parking",),
        )

    with a2:
        render_html(
            """
            <div class="ep-action-card">
                <div class="ep-action-title">⌘ Smart Route</div>
                <div class="ep-action-copy">
                    Find a permit-aware lot and launch directions.
                </div>
            </div>
            """
        )
        st.button(
            "Plan route",
            use_container_width=True,
            key="qa_route",
            on_click=go_to,
            args=("Smart Route",),
        )

    with a3:
        render_html(
            """
            <div class="ep-action-card">
                <div class="ep-action-title">●● RideShare</div>
                <div class="ep-action-copy">
                    Find or offer a ride with simulated commuters.
                </div>
            </div>
            """
        )
        st.button(
            "Find a match",
            use_container_width=True,
            key="qa_rideshare",
            on_click=go_to,
            args=("RideShare",),
        )

    with a4:
        render_html(
            """
            <div class="ep-action-card">
                <div class="ep-action-title">⚙ Operations</div>
                <div class="ep-action-copy">
                    Review parking pressure and evaluation checks.
                </div>
            </div>
            """
        )
        st.button(
            "View operations",
            use_container_width=True,
            key="qa_operations",
            on_click=go_to,
            args=("Operations",),
        )

    render_traceability("Dashboard", "Full application", show_all=True)


# Predictive Parking
elif active_page == "Predictive Parking":
    render_hero(
        "Predictive Parking",
        "Compare current occupancy with a simulated 20-minute forecast "
        "before committing to a parking lot.",
    )

    render_traceability("Predictive Parking", "Epic 1")

    preferred_lot = st.selectbox(
        "Preferred parking lot",
        facilities_df["name"].tolist(),
        index=0,
    )

    preferred = forecast_df[forecast_df["name"] == preferred_lot].iloc[0]

    if preferred["forecast_pct"] >= 90:
        alternatives = forecast_df[
            (forecast_df["permit_required"] == user_permit)
            & (forecast_df["forecast_pct"] < 90)
        ].sort_values(["forecast_pct", "walk_mins"])

        if not alternatives.empty:
            backup = alternatives.iloc[0]
            st.warning(
                f"{preferred_lot} is projected to reach "
                f"{preferred['forecast_pct']:.0f}% occupancy in 20 minutes. "
                f"Backup recommendation: {backup['name']}."
            )
        else:
            st.warning(
                f"{preferred_lot} is projected to reach "
                f"{preferred['forecast_pct']:.0f}% occupancy in 20 minutes."
            )
    else:
        st.success(
            f"{preferred_lot} is projected to remain below the saturation threshold "
            f"at {preferred['forecast_pct']:.0f}% occupancy."
        )

    left, right = st.columns([1.0, 1.2], gap="large")

    with left:
        render_html('<div class="ep-section-title">20-Minute Forecast</div>')

        for index, row in forecast_df.iterrows():
            render_lot_row(
                row,
                predicted_pct=row["forecast_pct"],
                predicted_open=row["forecast_available"],
            )

    with right:
        render_html('<div class="ep-section-title">Campus Map</div>')
        render_map(forecast_df)


# Smart Route
elif active_page == "Smart Route":
    render_hero(
        "Smart Route",
        "Permit-aware parking guidance that reacts to campus saturation "
        "and launches a practical route to the selected lot.",
    )

    render_traceability("Smart Route", "Epic 2")

    left, right = st.columns([0.78, 1.35], gap="large")

    with left:
        render_html('<div class="ep-section-title">Route Setup</div>')

        destination = st.selectbox(
            "Campus destination",
            CAMPUS_LANDMARKS["name"].tolist(),
        )

        ev_priority = st.checkbox(
            "Prioritize EV charging",
            value=False,
            help="Prototype preference only; EV stall data is simulated.",
        )

        if ev_priority:
            st.caption(
                "EV charging availability is represented as a future data source in this prototype."
            )

        render_html('<div class="ep-section-title">Recommendation</div>')
        render_recommendation()

    with right:
        render_html('<div class="ep-section-title">Campus Map</div>')
        render_map(facilities_df)

    render_html('<div class="ep-section-title">Alternative Lots</div>')

    c1, c2 = st.columns(2, gap="medium")
    rows = facilities_df.sort_values(["pct_full", "walk_mins"]).reset_index(drop=True)

    for i, row in rows.iterrows():
        target = c1 if i % 2 == 0 else c2
        with target:
            render_lot_row(row)


# RideShare
elif active_page == "RideShare":
    render_hero(
        "RideShare",
        "Simulated commuter matching based on arrival time, origin, destination, "
        "role preference, and pickup detour.",
    )

    render_traceability("RideShare", "Epic 3")

    setup_col, results_col = st.columns([0.82, 1.25], gap="large")

    with setup_col:
        render_html('<div class="ep-section-title">Trip Preferences</div>')

        request_mode = st.radio(
            "What are you doing?",
            ["Need a ride", "Offering a ride"],
            horizontal=True,
        )

        origin = st.selectbox(
            "Approximate origin",
            list(ZONE_COORDS.keys()),
            index=0,
        )

        arrival_time = st.time_input(
            "Target campus arrival",
            value=pd.Timestamp("2026-09-23 08:50").time(),
        )

        destination = st.selectbox(
            "Campus destination",
            CAMPUS_LANDMARKS["name"].tolist(),
            index=0,
            key="rideshare_destination",
        )

        group_filter = st.selectbox(
            "Match preference",
            ["Any eligible user", "Student", "Faculty / Staff"],
            help="Faculty can restrict results to faculty/staff matches.",
        )

        max_detour = st.slider(
            "Maximum pickup detour",
            min_value=2,
            max_value=10,
            value=5,
            step=1,
            format="%d min",
        )

        vehicle_registered = True

        if request_mode == "Offering a ride":
            render_html('<div class="ep-section-title">Vehicle Registration</div>')

            vehicle_registered = st.checkbox(
                "Register my vehicle for this simulated trip",
                value=True,
            )

            st.text_input(
                "Vehicle",
                value="2019 Toyota Camry",
                disabled=not vehicle_registered,
            )

            st.number_input(
                "Available seats",
                min_value=1,
                max_value=6,
                value=2,
                disabled=not vehicle_registered,
            )

        st.caption(
            "The system ranks matches. The user still decides whether to accept one."
        )

    with results_col:
        render_html('<div class="ep-section-title">Recommended Matches</div>')

        if request_mode == "Offering a ride" and not vehicle_registered:
            st.warning(
                "Register the vehicle for this simulated trip before matching riders."
            )
            matches = []
        else:
            matches = rideshare_matches(
                request_mode,
                origin,
                arrival_time,
                destination,
                group_filter,
                max_detour,
            )

        if not matches:
            st.info(
                "No simulated commuters meet the current filters. "
                "Try a wider detour limit or a different preference."
            )
        else:
            top_matches = matches[:3]

            for match in top_matches:
                render_match_card(match, request_mode)

                button_label = (
                    f"Request ride with {match['name']}"
                    if request_mode == "Need a ride"
                    else f"Offer ride to {match['name']}"
                )

                if st.button(
                    button_label,
                    key=f"match_{request_mode}_{match['id']}",
                    use_container_width=True,
                ):
                    st.session_state["accepted_rideshare_match"] = match["id"]
                    st.session_state["carpool_credit"] = 1

            accepted_id = st.session_state.get("accepted_rideshare_match")
            if accepted_id:
                accepted = next(
                    (match for match in top_matches if match["id"] == accepted_id),
                    None,
                )

                if accepted:
                    st.success(
                        f"Simulated match selected: {accepted['name']}. "
                        "The other commuter would still need to confirm."
                    )
                    st.caption(
                        "Carpool incentive: +1 preferred-parking credit "
                        "(simulated prototype reward)."
                    )

            best = top_matches[0]
            st.caption(
                f"Top score uses a {best['time_diff']} minute arrival difference, "
                f"{best['distance_km']} km origin separation, "
                f"~{best['detour_mins']} minute detour, destination compatibility, "
                "role preference, and profile verification."
            )


# Operations
else:
    render_hero(
        "Operations",
        "Administrative view for campus parking pressure, system evaluation, "
        "and prototype failure-case testing.",
    )

    render_traceability("Admin & Evaluation", "Epic 4")

    full_90 = int((facilities_df["pct_full"] >= 90).sum())
    full_75 = int((facilities_df["pct_full"] >= 75).sum())
    total_open = int(facilities_df["available"].sum())

    k1, k2, k3 = st.columns(3, gap="medium")
    with k1:
        render_kpi("!", "ep-icon-red", "Lots ≥ 90%", str(full_90), "Immediate attention")
    with k2:
        render_kpi("↗", "ep-icon-gold", "Lots ≥ 75%", str(full_75), "Filling or saturated")
    with k3:
        render_kpi("P", "ep-icon-green", "Open Spaces", f"{total_open:,}", "Across demo lots")

    left, right = st.columns(2, gap="large")

    with left:
        render_html('<div class="ep-section-title">Evaluation Surface</div>')
        st.info(
            "This area represents the functional metrics, similarity-based metrics, "
            "AI-judge criterion, and evaluation checks from the project."
        )

        st.metric("Parking recommendation success", "92%", "+4%")
        st.metric("RideShare top-3 relevance", "87%", "+3%")

    with right:
        render_html('<div class="ep-section-title">Failure Tests</div>')
        st.markdown(
            """
            - Invalid or non-existent RideShare recommendation
            - Matched participant flagged as a no-show
            - Removed user still returned by matching
            - Parking data stale, unavailable, or incorrect
            """
        )

    render_html('<div class="ep-section-title">Current Lot Pressure</div>')

    c1, c2 = st.columns(2, gap="medium")
    for i, row in facilities_df.iterrows():
        target = c1 if i % 2 == 0 else c2
        with target:
            render_lot_row(row)
