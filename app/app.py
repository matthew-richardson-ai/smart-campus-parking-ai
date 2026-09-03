# app/app.py
"""
EaglePark AI | Tennessee Tech University (TTU)
Smart Campus Parking, Dynamic Wayfinding & Commuter Optimization Engine

Mobile-first responsive architecture calibrated for iOS/Android viewports.
Eliminates Safari bottom-overflow whitespace, replaces external asset blocks with
clean SVG institutional marks, and provides native single-column auto-stacking.
"""

import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

# Path safety for simulation module access
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from simulation.clustering import match_commuters_by_timetable
except ImportError:

    def match_commuters_by_timetable(csv_path, target_time, max_radius_km):
        return pd.DataFrame()


# Streamlit Page Setup
st.set_page_config(
    page_title="EaglePark AI | TTU Transit Optimization",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# Section 1: Mobile-First Theme & CSS Optimization (iOS Safe)
# -----------------------------------------------------------------------------
if "app_theme" not in st.session_state:
    st.session_state.app_theme = "Dark"

theme_choice = st.sidebar.radio(
    "Interface Mode",
    ["Dark", "Light"],
    horizontal=True,
    index=0 if st.session_state.app_theme == "Dark" else 1,
    help="Toggle high-contrast dark cockpit styling or crisp light campus styling.",
)
st.session_state.app_theme = theme_choice

if st.session_state.app_theme == "Dark":
    theme_vars = """
        --bg-main: #0B0E14;
        --card-bg: rgba(22, 27, 34, 0.85);
        --card-border: rgba(255, 255, 255, 0.1);
        --text-primary: #F0F6FC;
        --text-secondary: #94A3B8;
        --accent-purple: #8B5CF6;
        --accent-gold: #FACC15;
        --brand-ttu: #4F2984;
        --badge-bg: rgba(79, 41, 132, 0.25);
        --badge-border: rgba(139, 92, 246, 0.4);
    """
else:
    theme_vars = """
        --bg-main: #F8FAFC;
        --card-bg: rgba(255, 255, 255, 0.95);
        --card-border: rgba(226, 232, 240, 0.8);
        --text-primary: #0F172A;
        --text-secondary: #64748B;
        --accent-purple: #4F2984;
        --accent-gold: #D97706;
        --brand-ttu: #4F2984;
        --badge-bg: rgba(79, 41, 132, 0.08);
        --badge-border: rgba(79, 41, 132, 0.2);
    """

mobile_optimized_css = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');

    :root {{
        {theme_vars}
    }}

    /* Global Typography & Viewport Height Constraints */
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        -webkit-tap-highlight-color: transparent;
    }}

    /* Fix iOS Safari dynamic address bar white blank space */
    html, body {{
        background-color: var(--bg-main) !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow-x: hidden;
    }}

    .stApp {{
        background-color: var(--bg-main) !important;
        color: var(--text-primary);
        min-height: 100% !important;
        height: auto !important;
    }}

    /* Eliminate unnecessary desktop margins on small screens */
    .block-container {{
        padding: 1rem 0.75rem 2rem 0.75rem !important;
        max-width: 100% !important;
    }}

    /* Responsive Mobile Header Card */
    .mobile-header {{
        display: flex;
        align-items: center;
        gap: 0.875rem;
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }}

    .ttu-crest-badge {{
        background: #4F2984;
        color: #FFDD00;
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        font-size: 1.1rem;
        border-radius: 8px;
        width: 44px;
        height: 44px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
        border: 1px solid #FFDD00;
    }}

    .mobile-header-text {{
        display: flex;
        flex-direction: column;
    }}

    .mobile-header-title {{
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0;
        color: var(--text-primary);
        line-height: 1.2;
    }}

    .mobile-header-subtitle {{
        font-size: 0.8rem;
        color: var(--text-secondary);
        margin-top: 0.2rem;
    }}

    /* Recommendation Alert Card */
    .rec-card {{
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-left: 4px solid var(--brand-ttu);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }}

    .pill-tag {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        background: var(--badge-bg);
        color: var(--accent-purple);
        border: 1px solid var(--badge-border);
        display: inline-block;
        margin-bottom: 0.5rem;
    }}

    /* Map container optimization */
    .stDeckGlJsonChart {{
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--card-border);
    }}
</style>
"""
st.markdown(mobile_optimized_css, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Section 2: Identity & Clearance Layer (Purple vs Gold)
# -----------------------------------------------------------------------------
INSTITUTIONAL_ACCOUNTS = {
    "T00123456": {
        "name": "Alex Mercer",
        "role": "Enrolled Student",
        "permit": "Purple",
        "has_permit": True,
        "detail": "Tuition-Included Active Student Permit",
    },
    "T00987654": {
        "name": "Jordan Smith",
        "role": "Graduate Assistant",
        "permit": "Purple",
        "has_permit": True,
        "detail": "Tuition-Included Active Student Permit",
    },
    "T00554433": {
        "name": "Dr. Vance",
        "role": "Faculty / Staff",
        "permit": "Gold",
        "has_permit": True,
        "detail": "Authorized Annual Faculty/Staff Clearance",
    },
    "T00000000": {
        "name": "Visitor / Guest Commuter",
        "role": "Unregistered Commuter",
        "permit": "None",
        "has_permit": False,
        "detail": "No active permit. Parking in Purple or Gold risks immediate citation.",
    },
}


# -----------------------------------------------------------------------------
# Section 3: Ground-Truth Facilities
# -----------------------------------------------------------------------------
def get_ttu_facilities(preset: str):
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
        occupied_counts = [80, 110, 35, 30, 20, 15]
    elif "Transition" in preset:
        occupied_counts = [270, 410, 175, 120, 95, 80]
    elif "Event" in preset:
        occupied_counts = [335, 570, 215, 170, 138, 290]
    else:  # Morning Peak
        occupied_counts = [326, 545, 185, 155, 65, 45]

    df = pd.DataFrame(lots)
    df["occupied"] = occupied_counts
    df["available"] = df["capacity"] - df["occupied"]
    df["pct_full"] = (df["occupied"] / df["capacity"]) * 100

    def get_tier(pct):
        if pct >= 90.0:
            return "SATURATED", [239, 68, 68, 230]
        elif pct >= 75.0:
            return "FILLING FAST", [245, 158, 11, 230]
        return "AVAILABLE", [34, 197, 94, 230]

    tiers = df["pct_full"].apply(get_tier)
    df["status"] = [t[0] for t in tiers]
    df["color"] = [t[1] for t in tiers]
    df["map_label"] = df.apply(
        lambda r: f"{r['short_code']} ({r['available']} open)", axis=1
    )
    return df


campus_landmarks = pd.DataFrame([
    {"name": "Ashraf Islam Eng Building (AIEB)", "lat": 36.17765, "lon": -85.50615},
    {"name": "Volpe Library", "lat": 36.17780, "lon": -85.50495},
    {"name": "Prescott Hall", "lat": 36.17625, "lon": -85.50360},
    {"name": "Stonecipher Hall (LSC)", "lat": 36.17690, "lon": -85.50605},
    {"name": "Derryberry Hall", "lat": 36.17540, "lon": -85.50545},
    {"name": "Hooper Eblen Center", "lat": 36.17855, "lon": -85.50760},
    {"name": "Bell Hall", "lat": 36.17480, "lon": -85.50785},
])

# -----------------------------------------------------------------------------
# Section 4: Sidebar Controls
# -----------------------------------------------------------------------------
st.sidebar.markdown("### Profile Authentication")

selected_t_number = st.sidebar.selectbox(
    "Active Profile",
    options=list(INSTITUTIONAL_ACCOUNTS.keys()),
    index=0,
    format_func=lambda x: f"{x} — {INSTITUTIONAL_ACCOUNTS[x]['name']}",
)

account = INSTITUTIONAL_ACCOUNTS[selected_t_number]
user_permit = account["permit"]
has_valid_permit = account["has_permit"]

if user_permit == "Purple":
    st.sidebar.success("🟣 **Permit Tier: PURPLE** (Student Tuition-Enrolled)")
elif user_permit == "Gold":
    st.sidebar.warning("🟡 **Permit Tier: GOLD** (Faculty / Staff)")
else:
    st.sidebar.error("⚪ **NO ACTIVE PERMIT** (Visitor / Unregistered)")

st.sidebar.markdown("### Route Configuration")
selected_destination = st.sidebar.selectbox(
    "Destination", options=campus_landmarks["name"].tolist(), index=0
)

traffic_preset = st.sidebar.selectbox(
    "Campus Traffic State",
    [
        "Morning Peak (07:30 - 09:00)",
        "Midday Transition (11:00 - 13:00)",
        "Afternoon / Evening (Low Traffic)",
        "Event Saturation (Game Day)",
    ],
)

facilities_df = get_ttu_facilities(traffic_preset)

# -----------------------------------------------------------------------------
# Section 5: Target Evaluation Engine
# -----------------------------------------------------------------------------
if has_valid_permit:
    permitted_lots = facilities_df[
        facilities_df["permit_required"] == user_permit
    ].copy()
    if not permitted_lots.empty:
        valid_lots = permitted_lots[permitted_lots["pct_full"] < 90.0]
        if not valid_lots.empty:
            recommended_lot = valid_lots.sort_values(by="walk_mins").iloc[0]
        else:
            recommended_lot = permitted_lots.sort_values(
                by="available", ascending=False
            ).iloc[0]
    else:
        recommended_lot = None
else:
    recommended_lot = None

# -----------------------------------------------------------------------------
# Section 6: Responsive Header
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="mobile-header">
        <div class="ttu-crest-badge">TTU</div>
        <div class="mobile-header-text">
            <h1 class="mobile-header-title">EaglePark AI</h1>
            <span class="mobile-header-subtitle">Tennessee Tech · Live Ingress Wayfinding</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Section 7: Primary Recommendation Strip
# -----------------------------------------------------------------------------
if recommended_lot is not None:
    gps_link = (
        f"https://www.google.com/maps/dir/?api=1"
        f"&destination={recommended_lot['lat']},{recommended_lot['lon']}"
        f"&travelmode=driving"
    )

    st.markdown(
        f"""
        <div class="rec-card">
            <span class="pill-tag">RECOMMENDED ARRIVAL GATE</span>
            <h2 style="font-size: 1.25rem; font-weight: 700; margin: 0 0 0.25rem 0; color: var(--text-primary);">
                {recommended_lot["name"]}
            </h2>
            <div style="font-size: 0.9rem; color: var(--text-secondary); line-height: 1.4;">
                Open Spots: <strong style="color: #22C55E;">{recommended_lot["available"]}</strong> 
                ({recommended_lot["pct_full"]:.0f}% saturated)<br>
                Walk to {selected_destination}: <strong>~{recommended_lot["walk_mins"]} min</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.link_button(
        "🗺️ Launch Mobile Turn-by-Turn GPS", url=gps_link, use_container_width=True
    )

    # Saturation Alert Check
    primary_hub = facilities_df[facilities_df["id"] == "LOT-LIB"].iloc[0]
    if primary_hub["pct_full"] >= 90.0 and user_permit == "Purple":
        st.warning(
            f"⚠️ **Reroute Notice:** Volpe Library Lot is full ({primary_hub['pct_full']:.0f}%). "
            f"Diverted to {recommended_lot['name']} to bypass Stadium Drive backups."
        )

elif not has_valid_permit:
    st.error(
        "🚨 **No Permit on File:** Unregistered vehicles are cited in campus Purple/Gold zones."
    )

# -----------------------------------------------------------------------------
# Section 8: Stacked Mobile View (Map First, Then Directory)
# -----------------------------------------------------------------------------
st.markdown("### Aerial Map Telemetry")

satellite_tiles = pdk.Layer(
    "TileLayer",
    data="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
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
    font_family="'JetBrains Mono', monospace",
    font_weight="bold",
    background=True,
    get_background_color=[15, 23, 42, 220],
    pickable=False,
)

building_nodes = pdk.Layer(
    "ScatterplotLayer",
    data=campus_landmarks,
    get_position=["lon", "lat"],
    get_color=[56, 189, 248, 220],
    get_radius=14,
    radius_min_pixels=6,
    radius_max_pixels=8,
    pickable=True,
)

deck_view = pdk.ViewState(
    latitude=36.1775, longitude=-85.5058, zoom=15.6, pitch=0, bearing=0
)

st.pydeck_chart(
    pdk.Deck(
        map_style=None,
        layers=[satellite_tiles, building_nodes, lot_nodes, lot_labels],
        initial_view_state=deck_view,
        tooltip={
            "text": "{name}\nStatus: {status}\nOpen Stalls: {available} / {capacity}"
        },
    )
)

st.markdown("### Live Campus Lots")

for _, row in facilities_df.iterrows():
    is_cleared = row["permit_required"] == user_permit
    status_emoji = (
        "🟢"
        if row["status"] == "AVAILABLE"
        else ("🟠" if row["status"] == "FILLING FAST" else "🔴")
    )

    with st.expander(
        f"{status_emoji} {row['name']} — {row['available']} open", expanded=False
    ):
        st.progress(row["pct_full"] / 100)
        st.write(
            f"**Permit Requirement:** {row['permit_required']} Zone  \n"
            f"**Occupancy:** {row['occupied']} / {row['capacity']} stalls occupied  \n"
            f"**Walking Distance:** ~{row['walk_mins']} min walk to central academic hall"
        )
        row_gps = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&destination={row['lat']},{row['lon']}"
            f"&travelmode=driving"
        )
        if is_cleared and row["pct_full"] < 90.0:
            st.link_button("Route to this Lot", url=row_gps, use_container_width=True)
