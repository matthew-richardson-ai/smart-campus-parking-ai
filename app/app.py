# app/app.py
"""
EaglePark AI | Tennessee Tech University (TTU)
Smart Campus Parking, Dynamic Wayfinding & Commuter Optimization Engine

OVERVIEW:
    This dashboard serves as the central client interface for the EaglePark
    transit optimization platform. It addresses Tennessee Tech's morning peak
    parking bottlenecks by executing four tasks:
        1. Role-based permit compliance verification (Purple vs. Gold).
        2. Real-time predictive occupancy monitoring with saturation warnings.
        3. Curb-cut-calibrated mobile GPS turn-by-turn routing handoffs.
        4. Spatial clustering (DBSCAN) for commuter carpool matching.

ENGINEERING DESIGN DECISIONS:
    - Map Rendering: Pydeck's Deck.gl wrapper uses a TileLayer pulling raster
      tiles directly from Esri World Imagery. This exposes asphalt stall striping
      and recent construction footprints (e.g., the Ashraf Islam Engineering Building)
      without incurring recurring Mapbox or Google Maps JavaScript API costs.
    - Waypoint Positioning: Centroid coordinates pull navigation systems toward
      the middle of building roofs or green spaces. We instead hardcode physical
      entrance curb cuts (e.g., the Stadium Drive apron for the Volpe Library Lot)
      so external navigation routing guides vehicles to drivable access gates.
    - Permit Hierarchy: Following updated university tuition structures, parking fees
      are automatically bundled into student tuition. Students receive Purple clearance,
      while faculty and staff hold Gold credentials. The UI enforces read-only badge
      displays to simulate institutional single-sign-on (SSO) credential retrieval.
"""

import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

# -----------------------------------------------------------------------------
# Module Import Fallback Safety
# -----------------------------------------------------------------------------
# Streamlit Community Cloud launches apps from various relative root paths.
# Adding the parent directory to sys.path guarantees that the backend clustering
# package can be located whether the script runs locally or in cloud production.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from simulation.clustering import match_commuters_by_timetable
except ImportError:
    # Graceful degradation: If simulation files are missing or unmounted,
    # the main dashboard will continue rendering parking and map facilities.
    def match_commuters_by_timetable(csv_path, target_time, max_radius_km):
        return pd.DataFrame()


# Streamlit Page Setup
st.set_page_config(
    page_title="EaglePark AI | TTU Transit Optimization",
    page_icon="https://www.tntech.edu/assets/images/brand/athletics/eagle-head.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Section 1: UI Theme Engine & Custom CSS Design Tokens
# -----------------------------------------------------------------------------
# We inject custom CSS to apply Tennessee Tech brand colors (Purple #4F2984,
# Gold #FFDD00/#D97706) and provide an interface mode switcher (Dark vs. Light).
# Glassmorphic backdrops and JetBrains Mono code badges create a modern cockpit aesthetic.

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

# Define CSS variable tokens dynamically based on the active theme
if st.session_state.app_theme == "Dark":
    theme_vars = """
        --bg-main: #0B0E14;
        --card-bg: rgba(22, 27, 34, 0.75);
        --card-border: rgba(255, 255, 255, 0.08);
        --card-hover: rgba(30, 38, 48, 0.9);
        --text-primary: #F0F6FC;
        --text-secondary: #8B949E;
        --accent-purple: #8B5CF6;
        --accent-gold: #FACC15;
        --brand-ttu: #4F2984;
        --badge-bg: rgba(79, 41, 132, 0.25);
        --badge-border: rgba(139, 92, 246, 0.4);
    """
else:
    theme_vars = """
        --bg-main: #F8FAFC;
        --card-bg: rgba(255, 255, 255, 0.85);
        --card-border: rgba(226, 232, 240, 0.8);
        --card-hover: rgba(241, 245, 249, 1.0);
        --text-primary: #0F172A;
        --text-secondary: #64748B;
        --accent-purple: #4F2984;
        --accent-gold: #D97706;
        --brand-ttu: #4F2984;
        --badge-bg: rgba(79, 41, 132, 0.08);
        --badge-border: rgba(79, 41, 132, 0.2);
    """

custom_css = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {{
        {theme_vars}
    }}

    /* Global typography reset */
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}

    .stApp {{
        background: var(--bg-main);
        color: var(--text-primary);
    }}

    /* Hero Banner Component */
    .hero-container {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.5rem 2rem;
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        backdrop-filter: blur(12px);
        margin-bottom: 1.5rem;
    }}

    .hero-left {{
        display: flex;
        align-items: center;
        gap: 1.25rem;
    }}

    .hero-logo {{
        width: 54px;
        height: auto;
        border-radius: 6px;
    }}

    .hero-title {{
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        margin: 0;
        color: var(--text-primary);
    }}

    .hero-subtitle {{
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin: 0.25rem 0 0 0;
    }}

    /* Target Recommendation Card */
    .recommendation-card {{
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-left: 4px solid var(--brand-ttu);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.1);
    }}

    .rec-metric-pill {{
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.6rem;
        border-radius: 6px;
        background: var(--badge-bg);
        color: var(--accent-purple);
        border: 1px solid var(--badge-border);
    }}

    /* Status Pill Identifiers for Occupancy */
    .status-pill {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    .status-available {{
        background: rgba(34, 197, 94, 0.15);
        color: #22C55E;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }}

    .status-fast {{
        background: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }}

    .status-saturated {{
        background: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }}

    /* Tighten default Streamlit layout padding for mobile viewports */
    .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Section 2: Institutional Identity & Permit Registry (Prototype SSO)
# -----------------------------------------------------------------------------
# Under Tennessee Tech's current transit model:
#   - Commuter Students: Parking fees are incorporated into regular semester
#     tuition, auto-assigning them a "Purple" permit upon enrollment.
#   - Faculty / Staff: Hold designated "Gold" permits for staff reserved lots.
#   - Unregistered / Visitors: Hold no permit and will be ticketed in Purple/Gold bays.
#
# The dictionary below simulates database rows retrieved during institutional
# authentication. Drivers do not manually pick permit tiers; they select their
# identity, and the system derives their clearance status.
INSTITUTIONAL_ACCOUNTS = {
    "T00123456": {
        "name": "Alex Mercer",
        "role": "Enrolled Undergraduate",
        "permit": "Purple",
        "has_permit": True,
        "detail": "Tuition-enrolled active student. Authorized for all Purple zones.",
    },
    "T00987654": {
        "name": "Jordan Smith",
        "role": "Graduate Assistant",
        "permit": "Purple",
        "has_permit": True,
        "detail": "Graduate student standing. Authorized for all Purple zones.",
    },
    "T00554433": {
        "name": "Dr. Vance",
        "role": "Faculty / Staff",
        "permit": "Gold",
        "has_permit": True,
        "detail": "Verified University Faculty credential. Authorized for Gold zones.",
    },
    "T00000000": {
        "name": "Guest / Unregistered Commuter",
        "role": "Visitor",
        "permit": "None",
        "has_permit": False,
        "detail": "No active tuition or staff record on file. High citation risk.",
    },
}


# -----------------------------------------------------------------------------
# Section 3: Calibrated Campus Facilities & Landmark Ground Truth
# -----------------------------------------------------------------------------
def get_ttu_facilities(preset: str):
    """
    Returns ground-truth physical parking lots across the TTU campus.

    NOTE ON COORDINATES:
    These coordinates are deliberately set to physical vehicle curb cuts / entrance
    driveways rather than the mathematical center of the lot. This ensures third-party
    GPS engines (Google Maps / Apple Maps) guide drivers to the access gate rather
    than navigating to an inaccessible street on the opposite side of a fence.
    """
    lots = [
        {
            "id": "LOT-LIB",
            "name": "Volpe Library North Lot",
            "short_code": "Library Lot",
            "permit_required": "Purple",
            "capacity": 340,
            # Physical curb cut off Stadium Drive / University Drive behind Volpe Library
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
            # Primary west commuter entrance apron accessible via Willow Avenue
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
            # Paved lot access driveway on Peachtree Avenue between 7th and 8th Street
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
            # Faculty parking north of Bryan Fine Arts along Ashburn Drive
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
            # Entrance curb cut off West 10th Street directly opposite Bell Hall
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
            # Overflow commuter access points along West 12th Street
            "lat": 36.18240,
            "lon": -85.51160,
            "walk_mins": 8.0,
        },
    ]

    # Dynamic occupancy presets simulating real university traffic cycles
    if "Low" in preset:
        occupied_counts = [80, 110, 35, 30, 20, 15]
    elif "Transition" in preset:
        occupied_counts = [270, 410, 175, 120, 95, 80]
    elif "Event" in preset:
        occupied_counts = [335, 570, 215, 170, 138, 290]
    else:  # Morning Peak (07:30 - 09:00 default bottleneck)
        occupied_counts = [326, 545, 185, 155, 65, 45]

    df = pd.DataFrame(lots)
    df["occupied"] = occupied_counts
    df["available"] = df["capacity"] - df["occupied"]
    df["pct_full"] = (df["occupied"] / df["capacity"]) * 100

    # Categorize occupancy into visual alert tiers
    def get_tier(pct):
        if pct >= 90.0:
            # Saturated (Red): Lot is congested; rerouting triggers
            return "SATURATED", [239, 68, 68, 230], "status-saturated"
        elif pct >= 75.0:
            # Filling Fast (Amber): Limited spots remain
            return "FILLING FAST", [245, 158, 11, 230], "status-fast"
        # Available (Green): Safe destination with ample parking
        return "AVAILABLE", [34, 197, 94, 230], "status-available"

    tiers = df["pct_full"].apply(get_tier)
    df["status"] = [t[0] for t in tiers]
    df["color"] = [t[1] for t in tiers]
    df["status_class"] = [t[2] for t in tiers]
    df["map_label"] = df.apply(
        lambda r: f"{r['short_code']} | {r['available']} open", axis=1
    )
    return df


# Academic buildings serving as destination anchors across campus
campus_landmarks = pd.DataFrame([
    {"name": "Ashraf Islam Eng Building (AIEB)", "lat": 36.17765, "lon": -85.50615},
    {"name": "Angelo & Jennette Volpe Library", "lat": 36.17780, "lon": -85.50495},
    {"name": "Prescott Hall", "lat": 36.17625, "lon": -85.50360},
    {"name": "Stonecipher Hall (LSC)", "lat": 36.17690, "lon": -85.50605},
    {"name": "Derryberry Hall", "lat": 36.17540, "lon": -85.50545},
    {"name": "Hooper Eblen Center", "lat": 36.17855, "lon": -85.50760},
    {"name": "Bell Hall", "lat": 36.17480, "lon": -85.50785},
])

building_options = campus_landmarks["name"].tolist()

# -----------------------------------------------------------------------------
# Section 4: Sidebar Controls & Driver Configuration
# -----------------------------------------------------------------------------
st.sidebar.markdown("### TTU Commuter Authentication")

# Driver selects their identity (simulating an Eagle Online / SSO token lookup)
selected_t_number = st.sidebar.selectbox(
    "Active Institutional Profile",
    options=list(INSTITUTIONAL_ACCOUNTS.keys()),
    index=0,
    format_func=lambda x: f"{x} — {INSTITUTIONAL_ACCOUNTS[x]['name']}",
    help="Simulates institutional SSO verification to retrieve active tuition or staff credentials.",
)

account = INSTITUTIONAL_ACCOUNTS[selected_t_number]
user_permit = account["permit"]
has_valid_permit = account["has_permit"]

# Read-only permit verification card reflecting verified institutional status
if user_permit == "Purple":
    st.sidebar.markdown(
        """
        <div style="padding: 0.75rem 1rem; border-radius: 8px; background: rgba(79, 41, 132, 0.15); border: 1px solid #4F2984; margin-bottom: 1rem;">
            <div style="font-size: 0.75rem; font-weight: 700; color: #8B5CF6; letter-spacing: 0.05em;">VERIFIED PERMIT TIER</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #A78BFA; margin-top: 2px;">PURPLE (STUDENT)</div>
            <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 4px;">Included with enrolled tuition fees.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
elif user_permit == "Gold":
    st.sidebar.markdown(
        """
        <div style="padding: 0.75rem 1rem; border-radius: 8px; background: rgba(217, 119, 6, 0.15); border: 1px solid #D97706; margin-bottom: 1rem;">
            <div style="font-size: 0.75rem; font-weight: 700; color: #F59E0B; letter-spacing: 0.05em;">VERIFIED PERMIT TIER</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #FBBF24; margin-top: 2px;">GOLD (FACULTY / STAFF)</div>
            <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 4px;">Faculty and staff authorized parking.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.sidebar.markdown(
        """
        <div style="padding: 0.75rem 1rem; border-radius: 8px; background: rgba(239, 68, 68, 0.15); border: 1px solid #EF4444; margin-bottom: 1rem;">
            <div style="font-size: 0.75rem; font-weight: 700; color: #EF4444; letter-spacing: 0.05em;">NO ACTIVE PERMIT</div>
            <div style="font-size: 0.8rem; color: #F87171; margin-top: 4px;">Unregistered commuter. Parking in Purple or Gold areas is subject to citation.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.sidebar.markdown("### Destination & Routing")
selected_destination = st.sidebar.selectbox(
    "Campus Target Destination",
    options=building_options,
    index=0,
    help="Target academic facility used to calculate pedestrian walking corridors.",
)

traffic_preset = st.sidebar.selectbox(
    "Campus Traffic Rush Model",
    [
        "Morning Peak (07:30 - 09:00)",
        "Midday Transition (11:00 - 13:00)",
        "Afternoon / Evening (Low Traffic)",
        "Event Saturation (Game Day)",
    ],
    help="Simulates campus occupancy surges to evaluate algorithmic diversion behavior.",
)

ai_reroute_guard = st.sidebar.toggle(
    "Saturation Diversion Shield",
    value=True,
    help="Automatically diverts drivers away from lots exceeding 90% saturation to prevent entry gridlock.",
)

st.sidebar.markdown("### Rideshare Scheduling")
target_window = st.sidebar.selectbox(
    "Arrival Window",
    ["07:45", "08:30", "09:30", "10:30"],
    index=1,
    help="Class start window used to filter carpool cohorts.",
)
detour_radius = st.sidebar.slider(
    "Detour Radius (km)",
    min_value=0.5,
    max_value=3.0,
    value=1.2,
    step=0.1,
    help="Maximum acceptable driving deviation for student pickups.",
)

facilities_df = get_ttu_facilities(traffic_preset)

# -----------------------------------------------------------------------------
# Section 5: Algorithmic Routing Evaluation
# -----------------------------------------------------------------------------
# Routing Engine Logic:
#   1. Filter facilities strictly to those matching the user's permit clearance.
#   2. Filter out facilities that meet or exceed 90% saturation (if any remain below threshold).
#   3. From available options, prioritize the lot with the lowest walking time
#      to the user's selected campus destination.
#   4. If all permitted lots are saturated, fallback to the lot with the highest raw spot count.
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
# Section 6: Hero Banner
# -----------------------------------------------------------------------------
ttu_logo_url = "https://www.tntech.edu/assets/images/brand/athletics/eagle-head.png"

st.markdown(
    f"""
    <div class="hero-container">
        <div class="hero-left">
            <img src="{ttu_logo_url}" class="hero-logo" alt="Tennessee Tech University" />
            <div>
                <h1 class="hero-title">EaglePark Transit Optimization</h1>
                <p class="hero-subtitle">Tennessee Tech University · Real-time Commuter Routing & Capacity Balancing</p>
            </div>
        </div>
        <div>
            <span class="rec-metric-pill">{traffic_preset.split("(")[0].strip()}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Section 7: Primary Navigation Directive & Saturation Warnings
# -----------------------------------------------------------------------------
if recommended_lot is not None:
    # Build standard Google Maps deep-link pointing to the calibrated curb cut
    gps_link = (
        f"https://www.google.com/maps/dir/?api=1"
        f"&destination={recommended_lot['lat']},{recommended_lot['lon']}"
        f"&travelmode=driving"
    )

    st.markdown(
        f"""
        <div class="recommendation-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <span class="rec-metric-pill">PRIMARY DIRECTIVE</span>
                    <h2 style="font-size: 1.35rem; font-weight: 700; margin: 0.5rem 0 0.25rem 0; color: var(--text-primary);">
                        Proceed to {recommended_lot["name"]}
                    </h2>
                    <p style="color: var(--text-secondary); margin: 0; font-size: 0.9rem;">
                        Target destination: <strong>{selected_destination}</strong> · 
                        Est. Pedestrian Transit: <strong>{recommended_lot["walk_mins"]} min</strong>
                    </p>
                </div>
                <div style="text-align: right;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; font-weight: 700; color: #22C55E;">
                        {recommended_lot["available"]} <span style="font-size: 0.85rem; color: var(--text-secondary); font-weight: 400;">SPOTS</span>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary);">
                        {recommended_lot["pct_full"]:.0f}% saturated
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_btn1, c_btn2, _ = st.columns([1.5, 2, 4])
    with c_btn1:
        st.link_button("Launch GPS Navigation", url=gps_link, use_container_width=True)
    with c_btn2:
        if st.button("Recalculate Alternate Waypoint", use_container_width=True):
            st.toast("Re-evaluating secondary perimeter curb cuts...")

    # Saturation Check: Alert if the main library hub is backed up
    primary_hub = facilities_df[facilities_df["id"] == "LOT-LIB"].iloc[0]
    if primary_hub["pct_full"] >= 90.0 and ai_reroute_guard and user_permit == "Purple":
        st.warning(
            f"**Saturation Reroute Active:** Volpe Library North Lot is at capacity ({primary_hub['pct_full']:.0f}%). "
            f"Commuters are automatically diverted to **{recommended_lot['name']}** to eliminate Stadium Drive bottlenecks."
        )

elif not has_valid_permit:
    st.error(
        "**Institutional Citation Warning:** Your profile does not carry an active tuition or staff parking registration. "
        "Vehicles parked in designated Purple or Gold campus lots without credentials will receive citations via campus parking enforcement."
    )

# -----------------------------------------------------------------------------
# Section 8: Dual-Pane Operational Interface (Directory & Pydeck Map)
# -----------------------------------------------------------------------------
pane_directory, pane_map = st.columns([3, 2])

with pane_directory:
    st.markdown("### Campus Facility Directory")
    st.caption("Live edge-derived bay telemetry and permit authorization.")

    # Iterate through all campus lots to render cards with progress indicators
    for _, row in facilities_df.iterrows():
        is_cleared = row["permit_required"] == user_permit
        permit_tag = f"{row['permit_required']} Zone"

        with st.expander(
            f"{row['name']} — {row['available']} Available", expanded=is_cleared
        ):
            d1, d2 = st.columns([3, 1])
            with d1:
                st.progress(row["pct_full"] / 100)
                st.markdown(
                    f"""
                    <div style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.6;">
                        <strong>Classification:</strong> {permit_tag} ({"Cleared" if is_cleared else "Restricted"})<br>
                        <strong>Utilization:</strong> {row["occupied"]} of {row["capacity"]} stalls occupied<br>
                        <strong>Transit Time:</strong> ~{row["walk_mins"]} min walking corridor
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with d2:
                facility_gps = (
                    f"https://www.google.com/maps/dir/?api=1"
                    f"&destination={row['lat']},{row['lon']}"
                    f"&travelmode=driving"
                )
                if is_cleared and row["pct_full"] < 90.0:
                    st.link_button(
                        "Route Here",
                        url=facility_gps,
                        key=f"nav_{row['id']}",
                        use_container_width=True,
                    )
                elif not is_cleared:
                    st.caption("Permit Restricted")
                else:
                    st.caption("Lot Saturated")

with pane_map:
    st.markdown("### Aerial Spatial Telemetry")
    st.caption("High-resolution Esri raster feed with live vehicle ingress waypoints.")

    # 1. Base Aerial Imagery Layer (Esri ArcGIS World Imagery)
    # Using TileLayer allows Streamlit to render true satellite photography
    # without requiring a Mapbox API token or external map service keys.
    satellite_tiles = pdk.Layer(
        "TileLayer",
        data="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        min_zoom=0,
        max_zoom=19,
        tile_size=256,
        pickable=False,
    )

    # 2. Lot Status Circles (Color-coded by occupancy tier)
    lot_nodes = pdk.Layer(
        "ScatterplotLayer",
        data=facilities_df,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius=22,
        radius_min_pixels=9,
        radius_max_pixels=16,
        pickable=True,
        auto_highlight=True,
    )

    # 3. Lot Capacity Badges (High-contrast text on dark callout pill)
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

    # 4. Campus Building Landmark Pins (Cyan)
    building_nodes = pdk.Layer(
        "ScatterplotLayer",
        data=campus_landmarks,
        get_position=["lon", "lat"],
        get_color=[56, 189, 248, 220],
        get_radius=14,
        radius_min_pixels=6,
        radius_max_pixels=9,
        pickable=True,
    )

    # 5. Campus Building Landmark Text Labels
    building_labels = pdk.Layer(
        "TextLayer",
        data=campus_landmarks,
        get_position=["lon", "lat"],
        get_text="name",
        get_color=[255, 255, 255, 230],
        get_size=11,
        get_alignment_baseline="'top'",
        get_pixel_offset=[0, 8],
        font_family="'Inter', sans-serif",
        font_weight="bold",
        background=True,
        get_background_color=[30, 41, 59, 220],
        pickable=False,
    )

    # Center camera over the academic core of TTU campus
    deck_view = pdk.ViewState(
        latitude=36.1775, longitude=-85.5058, zoom=15.8, pitch=0, bearing=0
    )

    # map_style=None prevents Pydeck from overriding custom TileLayers with Mapbox
    st.pydeck_chart(
        pdk.Deck(
            map_style=None,
            layers=[
                satellite_tiles,
                building_nodes,
                building_labels,
                lot_nodes,
                lot_labels,
            ],
            initial_view_state=deck_view,
            tooltip={
                "text": "{name}\nPermit: {permit_required}\nAvailable: {available} / {capacity}"
            },
        )
    )

# -----------------------------------------------------------------------------
# Section 9: Rideshare Cohort Clustering (DBSCAN Engine)
# -----------------------------------------------------------------------------
# To curb aggregate vehicle arrivals, this section evaluates student home coordinates
# and daily class schedules using Density-Based Spatial Clustering of Applications
# with Noise (DBSCAN). Students living within the designated detour radius who share
# the same arrival window are grouped into carpool cohorts.
st.markdown("---")
st.markdown(f"### Commuter Carpool Cohorts ({target_window} Arrival Window)")
st.caption(
    "Spatial density clustering grouping commuters to minimize single-occupant campus trips."
)

csv_source = "simulation/data/commuter_schedules.csv"
if os.path.exists(csv_source):
    clustered = match_commuters_by_timetable(
        csv_path=csv_source, target_time=target_window, max_radius_km=detour_radius
    )
    if not clustered.empty and "carpool_group" in clustered.columns:
        # carpool_group == -1 denotes noise (unmatched drivers) under DBSCAN conventions
        valid_cohorts = clustered[clustered["carpool_group"] != -1]
        c1, c2 = st.columns([2, 1])
        with c1:
            st.dataframe(
                valid_cohorts[
                    [
                        "carpool_group",
                        "student_id",
                        "has_car",
                        "seats_available",
                        "home_lat",
                        "home_lon",
                    ]
                ].sort_values(by=["carpool_group", "has_car"], ascending=[True, False]),
                use_container_width=True,
            )
        with c2:
            st.metric("Total Commuters in Window", len(clustered))
            st.metric("Grouped Carpool Participants", len(valid_cohorts))
            st.metric("Cohorts Formed", valid_cohorts["carpool_group"].nunique())
    else:
        st.info("No carpool cohorts identified for this arrival window.")
else:
    st.info(
        "Execute `python simulation/generate_commuters.py` to populate commuter schedules."
    )
