# app/app.py
"""
EaglePark AI - CSC 4610 prototype.

This app demonstrates our parking, routing, rideshare,
and evaluation user stories in one Streamlit interface.
"""

import os
import sys
import streamlit as st
import pandas as pd
import pydeck as pdk

# Project imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

try:
    from user_stories import (
        USER_STORIES,
        FEATURE_STORY_MAP,
        get_stories_for_feature,
    )
except ImportError:
    USER_STORIES = []
    FEATURE_STORY_MAP = {}

    def get_stories_for_feature(feature_name):
        return []


try:
    from simulation.clustering import match_commuters_by_timetable
except ImportError:
    def match_commuters_by_timetable(csv_path, target_time, max_radius_km):
        return pd.DataFrame()


# Basic Streamlit page settings
st.set_page_config(
    page_title="EaglePark AI | TTU Transit Optimization",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Light and dark theme settings
if "app_theme" not in st.session_state:
    st.session_state.app_theme = "Dark"

theme_choice = st.sidebar.radio(
    "Interface Mode",
    ["Dark", "Light"],
    horizontal=True,
    index=0 if st.session_state.app_theme == "Dark" else 1,
)
st.session_state.app_theme = theme_choice

if st.session_state.app_theme == "Dark":
    theme_vars = """
        --bg-main: #0B0E14;
        --card-bg: rgba(22, 27, 34, 0.88);
        --card-border: rgba(255, 255, 255, 0.10);
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
        --card-bg: rgba(255, 255, 255, 0.96);
        --card-border: rgba(226, 232, 240, 0.9);
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

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        -webkit-tap-highlight-color: transparent;
    }}

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

    .block-container {{
        padding: 1rem 0.75rem 2rem 0.75rem !important;
        max-width: 100% !important;
    }}

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
        border: 1px solid #FFDD00;
    }}

    .mobile-header-title {{
        font-size: 1.25rem;
        font-weight: 700;
        margin: 0;
        color: var(--text-primary);
        line-height: 1.2;
    }}

    .mobile-header-subtitle {{
        font-size: 0.8rem;
        color: var(--text-secondary);
        margin-top: 0.2rem;
    }}

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
        font-size: 0.70rem;
        font-weight: 600;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        background: var(--badge-bg);
        color: var(--accent-purple);
        border: 1px solid var(--badge-border);
        display: inline-block;
        margin-bottom: 0.5rem;
    }}

    .story-card {{
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 10px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
    }}

    .stDeckGlJsonChart {{
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--card-border);
    }}
</style>
"""
st.markdown(mobile_optimized_css, unsafe_allow_html=True)


# Show which user stories each page supports
def render_story_traceability(feature_name: str):
    """Show the user stories connected to this page."""
    stories = get_stories_for_feature(feature_name)

    with st.expander("📋 CSC 4610 User Stories Demonstrated", expanded=False):
        if not stories:
            st.info(
                "User-story data is not loaded. Put user_stories.py in the repository root."
            )
            return

        for story in stories:
            st.markdown(
                f"""
                <div class="story-card">
                    <span class="pill-tag">
                        BOARD #{story["board_number"]} · ISSUE #{story["github_issue"]} · {story["id"]}
                    </span>
                    <div style="font-size:0.92rem; line-height:1.45;">
                        {story["story"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_header(module_name: str, subtitle: str):
    st.markdown(
        f"""
        <div class="mobile-header">
            <div class="ttu-crest-badge">TTU</div>
            <div>
                <h1 class="mobile-header-title">EaglePark AI · {module_name}</h1>
                <div class="mobile-header-subtitle">{subtitle}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Demo user profiles and permit types
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
        "detail": "No active Purple/Gold permit.",
    },
}


# Simulated TTU parking lot data
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
    else:
        occupied_counts = [326, 545, 185, 155, 65, 45]

    df = pd.DataFrame(lots)
    df["occupied"] = occupied_counts
    df["available"] = df["capacity"] - df["occupied"]
    df["pct_full"] = (df["occupied"] / df["capacity"]) * 100

    def get_tier(pct):
        if pct >= 90.0:
            return "SATURATED", [239, 68, 68, 230]
        if pct >= 75.0:
            return "FILLING FAST", [245, 158, 11, 230]
        return "AVAILABLE", [34, 197, 94, 230]

    tiers = df["pct_full"].apply(get_tier)
    df["status"] = [tier[0] for tier in tiers]
    df["color"] = [tier[1] for tier in tiers]
    df["map_label"] = df.apply(
        lambda row: f"{row['short_code']} ({row['available']} open)", axis=1
    )
    return df


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


# Parking recommendation and map functions
def recommend_lot(facilities_df, permit):
    if permit not in {"Purple", "Gold"}:
        return None

    permitted = facilities_df[
        facilities_df["permit_required"] == permit
    ].copy()

    if permitted.empty:
        return None

    not_saturated = permitted[permitted["pct_full"] < 90.0]
    if not not_saturated.empty:
        return not_saturated.sort_values(
            by=["walk_mins", "pct_full"], ascending=[True, True]
        ).iloc[0]

    return permitted.sort_values(by="available", ascending=False).iloc[0]


def render_recommendation(recommended_lot, selected_destination, user_permit, facilities_df):
    if recommended_lot is None:
        if user_permit == "None":
            st.info(
                "Visitor parking support is a planned user-story feature. "
                "This Step 2 build does not yet route visitors into Purple/Gold zones."
            )
        else:
            st.warning("No permitted parking recommendation is currently available.")
        return

    gps_link = (
        "https://www.google.com/maps/dir/?api=1"
        f"&destination={recommended_lot['lat']},{recommended_lot['lon']}"
        "&travelmode=driving"
    )

    st.markdown(
        f"""
        <div class="rec-card">
            <span class="pill-tag">AI PARKING RECOMMENDATION</span>
            <h2 style="font-size:1.25rem; margin:0 0 0.25rem 0;">
                {recommended_lot["name"]}
            </h2>
            <div style="font-size:0.9rem; color:var(--text-secondary); line-height:1.45;">
                Open spots: <strong>{recommended_lot["available"]}</strong><br>
                Current occupancy: <strong>{recommended_lot["pct_full"]:.0f}%</strong><br>
                Estimated walk to {selected_destination}: <strong>~{recommended_lot["walk_mins"]} min</strong><br>
                Permit match: <strong>{recommended_lot["permit_required"]}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.link_button(
        "🗺️ Launch Mobile Turn-by-Turn GPS",
        url=gps_link,
        use_container_width=True,
    )

    primary_hub = facilities_df[facilities_df["id"] == "LOT-LIB"].iloc[0]
    if primary_hub["pct_full"] >= 90.0 and user_permit == "Purple":
        st.warning(
            f"⚠️ Reroute Notice: Volpe Library Lot is "
            f"{primary_hub['pct_full']:.0f}% full. "
            f"EaglePark recommends {recommended_lot['name']}."
        )


def render_map(facilities_df):
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
        font_family="'JetBrains Mono', monospace",
        font_weight="bold",
        background=True,
        get_background_color=[15, 23, 42, 220],
        pickable=False,
    )

    building_nodes = pdk.Layer(
        "ScatterplotLayer",
        data=CAMPUS_LANDMARKS,
        get_position=["lon", "lat"],
        get_color=[56, 189, 248, 220],
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
                "text": "{name}\nStatus: {status}\nOpen Stalls: {available} / {capacity}"
            },
        )
    )


def render_lot_directory(facilities_df, user_permit):
    for _, row in facilities_df.iterrows():
        is_cleared = row["permit_required"] == user_permit

        if row["status"] == "AVAILABLE":
            status_emoji = "🟢"
        elif row["status"] == "FILLING FAST":
            status_emoji = "🟠"
        else:
            status_emoji = "🔴"

        with st.expander(
            f"{status_emoji} {row['name']} — {row['available']} open",
            expanded=False,
        ):
            st.progress(min(max(row["pct_full"] / 100, 0.0), 1.0))
            st.write(
                f"**Permit Requirement:** {row['permit_required']} Zone  \n"
                f"**Occupancy:** {row['occupied']} / {row['capacity']} stalls occupied  \n"
                f"**Walking Estimate:** ~{row['walk_mins']} min to central academic area"
            )

            row_gps = (
                "https://www.google.com/maps/dir/?api=1"
                f"&destination={row['lat']},{row['lon']}"
                "&travelmode=driving"
            )

            if is_cleared and row["pct_full"] < 90.0:
                st.link_button(
                    "Route to this Lot",
                    url=row_gps,
                    use_container_width=True,
                )
            elif not is_cleared:
                st.caption("This lot does not match the active profile's permit.")


# Sidebar navigation and demo controls
st.sidebar.markdown("## 🦅 EaglePark AI")
active_page = st.sidebar.radio(
    "Application Module",
    [
        "Dashboard",
        "Predictive Parking",
        "Smart Route",
        "RideShare",
        "Admin & Evaluation",
    ],
)

st.sidebar.divider()
st.sidebar.markdown("### Profile Authentication")

selected_t_number = st.sidebar.selectbox(
    "Active Profile",
    options=list(INSTITUTIONAL_ACCOUNTS.keys()),
    index=0,
    format_func=lambda value: (
        f"{value} — {INSTITUTIONAL_ACCOUNTS[value]['name']}"
    ),
)

account = INSTITUTIONAL_ACCOUNTS[selected_t_number]
user_permit = account["permit"]

if user_permit == "Purple":
    st.sidebar.success("🟣 Permit Tier: PURPLE")
elif user_permit == "Gold":
    st.sidebar.warning("🟡 Permit Tier: GOLD")
else:
    st.sidebar.info("⚪ Visitor / No Purple-Gold Permit")

traffic_preset = st.sidebar.selectbox(
    "Simulated Campus Traffic State",
    [
        "Morning Peak (07:30 - 09:00)",
        "Midday Transition (11:00 - 13:00)",
        "Afternoon / Evening (Low Traffic)",
        "Event Saturation (Game Day)",
    ],
)

facilities_df = get_ttu_facilities(traffic_preset)


# Dashboard page
if active_page == "Dashboard":
    render_header(
        "Dashboard",
        "CSC 4610 Prototype · Parking, Routing, RideShare & Evaluation",
    )
    render_story_traceability("Dashboard")

    total_capacity = int(facilities_df["capacity"].sum())
    total_available = int(facilities_df["available"].sum())
    campus_full_pct = (
        100.0 * facilities_df["occupied"].sum() / facilities_df["capacity"].sum()
    )
    saturated_count = int((facilities_df["pct_full"] >= 90.0).sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Campus Capacity", f"{total_capacity:,}")
    c2.metric("Open Stalls", f"{total_available:,}")
    c3.metric("Campus Occupancy", f"{campus_full_pct:.0f}%")
    c4.metric("Saturated Lots", saturated_count)

    st.caption(
        "Presentation prototype: occupancy values are simulated from selectable "
        "traffic presets and are not represented as live TTU sensor data."
    )

    st.markdown("### Current Lot Snapshot")
    dashboard_table = facilities_df[
        ["short_code", "permit_required", "available", "pct_full", "status"]
    ].copy()
    dashboard_table.columns = [
        "Lot",
        "Permit",
        "Open",
        "% Full",
        "Status",
    ]
    dashboard_table["% Full"] = dashboard_table["% Full"].round(1)
    st.dataframe(dashboard_table, use_container_width=True, hide_index=True)

    st.markdown("### Prototype Roadmap")
    st.info(
        "**Implemented now:** occupancy simulation, permit-aware recommendations, "
        "map telemetry, route launch, saturation reroute notice.\n\n"
        "**Next:** 20-minute parking forecast and projected-fill alert.\n\n"
        "**Then:** RideShare matching and Lab 5 evaluation/failure-case dashboard."
    )


# Predictive Parking page
elif active_page == "Predictive Parking":
    render_header(
        "Predictive Parking",
        "Epic 1 · Predictive Lot Occupancy & Forecasting",
    )
    render_story_traceability("Predictive Parking")

    st.markdown("### Current Occupancy Baseline")
    st.write(
        "This page is now explicitly tied to the five Predictive Lot Occupancy "
        "user stories. In Step 3 we will add the actual 20-minute forecast and "
        "projected-fill notification logic."
    )

    display_df = facilities_df[
        ["name", "permit_required", "capacity", "occupied", "available", "pct_full", "status"]
    ].copy()
    display_df["pct_full"] = display_df["pct_full"].round(1)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("### Aerial Map Telemetry")
    render_map(facilities_df)


# Smart Route page
elif active_page == "Smart Route":
    render_header(
        "Smart Route",
        "Epic 2 · Intelligent Routing & Dynamic Navigation",
    )
    render_story_traceability("Smart Route")

    selected_destination = st.selectbox(
        "Campus Destination",
        options=CAMPUS_LANDMARKS["name"].tolist(),
        index=0,
    )

    recommended_lot = recommend_lot(facilities_df, user_permit)

    st.markdown("### Parking Recommendation")
    render_recommendation(
        recommended_lot,
        selected_destination,
        user_permit,
        facilities_df,
    )

    st.markdown("### Aerial Map Telemetry")
    render_map(facilities_df)

    st.markdown("### Live Campus Lots")
    render_lot_directory(facilities_df, user_permit)


# RideShare page
elif active_page == "RideShare":
    render_header(
        "RideShare",
        "Epic 3 · Smart Carpooling & Commuter Coordination",
    )
    render_story_traceability("RideShare")

    st.info(
        "The RideShare user stories are now part of the application structure. "
        "The matching workflow will be implemented after Predictive Parking so "
        "we can reuse arrival-time and destination data."
    )

    st.markdown("### Planned RideShare Inputs")
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Approximate Origin / Area", disabled=True)
        st.time_input("Target Campus Arrival", disabled=True)
    with c2:
        st.selectbox(
            "Ride Preference",
            ["Need a Ride", "Offering a Ride"],
            disabled=True,
        )
        st.selectbox(
            "Match Group",
            ["Students", "Faculty / Staff"],
            disabled=True,
        )

    st.caption(
        "Next implementation will add verified driver records, timetable/proximity "
        "matching, detour estimates, and the Lab 5 rideshare failure cases."
    )


# Admin and Evaluation page
else:
    render_header(
        "Admin & Evaluation",
        "Epic 4 · Administrative Privileges & Law Enforcement + Lab 5 Evaluation",
    )
    render_story_traceability("Admin & Evaluation")

    st.markdown("### Current Operational Snapshot")
    a1, a2, a3 = st.columns(3)
    a1.metric(
        "Lots ≥ 90% Full",
        int((facilities_df["pct_full"] >= 90.0).sum()),
    )
    a2.metric(
        "Lots ≥ 75% Full",
        int((facilities_df["pct_full"] >= 75.0).sum()),
    )
    a3.metric(
        "Total Open Stalls",
        int(facilities_df["available"].sum()),
    )

    st.markdown("### Lab 5 Evaluation Integration")
    st.info(
        "This module will become the presentation surface for functional metrics, "
        "similarity-based metrics, the AI-judge criterion, and failure-case tests. "
        "We will add those after the user-facing predictive and RideShare workflows."
    )

    st.markdown("#### Failure cases already identified for later implementation")
    st.write(
        "1. A recommended rideshare references a non-existent or invalid driver/rider.\n"
        "2. A rideshare participant is predicted/flagged as a no-show.\n"
        "3. A previously removed rideshare user is still recommended.\n"
        "4. Parking data is incorrect, stale, or unavailable."
    )
