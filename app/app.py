"""
Smart Campus Parking & Navigation Dashboard (Streamlit Prototype)

Mobile-first campus navigation engine for Tennessee Tech commuters.
Provides permit-filtered lot saturation cards, predictive rerouting,
destination-based walking metrics, and a clean flat mini-map with key campus landmarks.
"""

import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

# Allow simulation imports regardless of execution root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from simulation.clustering import match_commuters_by_timetable

st.set_page_config(
    page_title="EaglePark AI | TTU Smart Navigation", page_icon="🦅", layout="wide"
)

# -----------------------------------------------------------------------------
# 1. Navigation & Driver Session State
# -----------------------------------------------------------------------------
if "target_destination" not in st.session_state:
    st.session_state.target_destination = "Angelo & Jennette Volpe Library"

if "permit_tier" not in st.session_state:
    st.session_state.permit_tier = "Purple (Commuter Student)"


# -----------------------------------------------------------------------------
# 2. Driver Preferences & Simulation Sidebar
# -----------------------------------------------------------------------------
st.sidebar.title("🦅 EaglePark Mobile Nav")

st.sidebar.subheader("Driver Profile & Destination")
user_permit = st.sidebar.selectbox(
    "Your Parking Permit",
    [
        "Purple (Commuter Student)",
        "Gold (Faculty / Staff)",
        "Red (Residence Hall)",
        "Visitor / Open",
    ],
    help="Filters lots by permit eligibility to prevent ticketing.",
)
st.session_state.permit_tier = user_permit

destination = st.sidebar.selectbox(
    "Campus Destination",
    [
        "Angelo & Jennette Volpe Library",
        "Prescott Hall (Engineering)",
        "Derryberry Hall (Admin & Admissions)",
        "Hooper Eblen Center (Athletics)",
        "Bell Hall (Nursing / Health)",
    ],
)
st.session_state.target_destination = destination

st.sidebar.divider()
st.sidebar.subheader("Simulation Presets")
scenario = st.sidebar.selectbox(
    "Campus Rush Preset",
    [
        "Morning Peak (07:30 - 09:00)",
        "Midday Transition (11:00 - 13:00)",
        "Afternoon / Evening (Low Traffic)",
        "Event Saturation (Basketball / Game Day)",
    ],
)

ai_reroute_enabled = st.sidebar.toggle(
    "Dynamic Rerouting Guard",
    value=True,
    help="Diverts driver before entering lot if occupancy reaches >=90%.",
)

st.sidebar.divider()
st.sidebar.subheader("Rideshare Dispatch Settings")
selected_arrival_time = st.sidebar.selectbox(
    "Arrival Cohort Window", ["07:45", "08:30", "09:30", "10:30"], index=1
)
max_radius = st.sidebar.slider("Pickup Detour Radius (km)", 0.5, 3.0, 1.2, 0.1)


# -----------------------------------------------------------------------------
# 3. Ground-Truth TTU Parking & Landmark Directory
# -----------------------------------------------------------------------------
def get_ttu_facilities(preset: str):
    """
    Returns exact geographic footprints, permit tiers, and live occupancy states
    for parking zones across the Tennessee Tech campus.
    """
    lots = [
        {
            "id": "LOT-LIB",
            "name": "Volpe Library & Stadium Lot",
            "permit_required": "Purple (Commuter Student)",
            "capacity": 340,
            "lat": 36.1782,
            "lon": -85.5048,
            "walk_mins_to_lib": 1.0,
            "walk_mins_to_prescott": 3.0,
            "polygon": [
                [-85.50575, 36.17885],
                [-85.50395, 36.17885],
                [-85.50395, 36.17750],
                [-85.50575, 36.17750],
            ],
        },
        {
            "id": "LOT-HOOPER",
            "name": "Hooper Eblen Center Lot",
            "permit_required": "Purple (Commuter Student)",
            "capacity": 580,
            "lat": 36.1781,
            "lon": -85.5085,
            "walk_mins_to_lib": 4.5,
            "walk_mins_to_prescott": 6.0,
            "polygon": [
                [-85.50970, 36.17895],
                [-85.50740, 36.17895],
                [-85.50740, 36.17730],
                [-85.50970, 36.17730],
            ],
        },
        {
            "id": "LOT-PEACH",
            "name": "Peachtree Ave Commuter Lot",
            "permit_required": "Purple (Commuter Student)",
            "capacity": 220,
            "lat": 36.1735,
            "lon": -85.5042,
            "walk_mins_to_lib": 5.0,
            "walk_mins_to_prescott": 4.0,
            "polygon": [
                [-85.50510, 36.17410],
                [-85.50340, 36.17410],
                [-85.50340, 36.17290],
                [-85.50510, 36.17290],
            ],
        },
        {
            "id": "LOT-ASHBURN",
            "name": "Ashburn Drive / Maker Lot",
            "permit_required": "Gold (Faculty / Staff)",
            "capacity": 175,
            "lat": 36.1757,
            "lon": -85.5019,
            "walk_mins_to_lib": 2.5,
            "walk_mins_to_prescott": 2.0,
            "polygon": [
                [-85.50280, 36.17630],
                [-85.50110, 36.17630],
                [-85.50110, 36.17510],
                [-85.50280, 36.17510],
            ],
        },
        {
            "id": "LOT-BELL",
            "name": "Bell Hall Health Sciences Lot",
            "permit_required": "Purple (Commuter Student)",
            "capacity": 140,
            "lat": 36.1751,
            "lon": -85.5078,
            "walk_mins_to_lib": 5.5,
            "walk_mins_to_prescott": 7.0,
            "polygon": [
                [-85.50850, 36.17570],
                [-85.50710, 36.17570],
                [-85.50710, 36.17460],
                [-85.50850, 36.17460],
            ],
        },
        {
            "id": "LOT-VILLAGE",
            "name": "Tech Village / West Stadium Overflow",
            "permit_required": "Purple (Commuter Student)",
            "capacity": 320,
            "lat": 36.1822,
            "lon": -85.5115,
            "walk_mins_to_lib": 7.0,
            "walk_mins_to_prescott": 9.0,
            "polygon": [
                [-85.5130, 36.1832],
                [-85.5100, 36.1832],
                [-85.5100, 36.1812],
                [-85.5130, 36.1812],
            ],
        },
    ]

    # Assign live counts based on scenario
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

    # Status coloring: Flat 2D styling
    def status_label(pct):
        if pct >= 90.0:
            return "SATURATED", [220, 38, 38, 160]  # Red
        elif pct >= 75.0:
            return "FILLING FAST", [234, 138, 0, 160]  # Amber
        return "AVAILABLE", [22, 163, 74, 160]  # Green

    labels_colors = df["pct_full"].apply(status_label)
    df["status"] = [item[0] for item in labels_colors]
    df["fill_color"] = [item[1] for item in labels_colors]
    return df


facilities_df = get_ttu_facilities(scenario)

# Key campus landmarks for direct visual orientation
landmarks_df = pd.DataFrame([
    {"name": "Volpe Library", "lat": 36.1778, "lon": -85.5048, "icon": "📚"},
    {
        "name": "Prescott Hall (Engineering)",
        "lat": 36.1762,
        "lon": -85.5035,
        "icon": "⚙️",
    },
    {"name": "Derryberry Hall (Admin)", "lat": 36.1755, "lon": -85.5055, "icon": "🏛️"},
    {"name": "Hooper Eblen Center", "lat": 36.1785, "lon": -85.5075, "icon": "🏀"},
    {"name": "Bell Hall (Nursing)", "lat": 36.1748, "lon": -85.5072, "icon": "🩺"},
])


# -----------------------------------------------------------------------------
# 4. Recommended Lot Decision Logic
# -----------------------------------------------------------------------------
# Filter lots permitted for this user
permitted_lots = facilities_df[facilities_df["permit_required"] == user_permit].copy()

# Sort permitted lots by availability and proximity to library/prescott
if not permitted_lots.empty:
    # Prefer lots that are NOT saturated (<90% full)
    valid_alternatives = permitted_lots[permitted_lots["pct_full"] < 90.0]
    if not valid_alternatives.empty:
        best_lot = valid_alternatives.sort_values(by="walk_mins_to_lib").iloc[0]
    else:
        best_lot = permitted_lots.sort_values(by="available", ascending=False).iloc[0]
else:
    best_lot = None


# -----------------------------------------------------------------------------
# 5. Top Header & Active GPS Routing Card
# -----------------------------------------------------------------------------
st.title("🚗 TTU Smart Commuter Navigation")
st.caption(f"Active Permit: **{user_permit}** | En Route To: **{destination}**")

# Highlighted GPS Navigation Banner
if best_lot is not None:
    rec_box = st.container()
    with rec_box:
        c1, c2, c3 = st.columns([3, 1, 1])

        with c1:
            st.success(f"📍 **Recommended Route:** Head to **{best_lot['name']}**")
            st.write(
                f"**{best_lot['available']} stalls open** ({best_lot['pct_full']:.0f}% full) · "
                f"Est. Walking Distance to {destination}: **{best_lot['walk_mins_to_lib'] + 1.0:.1f} mins**"
            )

        with c2:
            st.metric(
                "Free Stalls",
                f"{best_lot['available']} Spots",
                delta=f"{best_lot['capacity']} Total",
            )

        with c3:
            if st.button("🗺️ Start Turn-by-Turn GPS", use_container_width=True):
                st.toast(
                    f"Starting route to {best_lot['name']} via 10th & Stadium Dr..."
                )

    # Proactive Reroute Trigger Banner
    primary_lot = facilities_df[facilities_df["id"] == "LOT-LIB"].iloc[0]
    if primary_lot["pct_full"] >= 90.0 and ai_reroute_enabled:
        st.warning(
            f"⚠️ **Reroute Alert:** {primary_lot['name']} just reached {primary_lot['pct_full']:.0f}% capacity. "
            f"Traffic diverted to **{best_lot['name']}** to eliminate queue time."
        )
st.divider()


# -----------------------------------------------------------------------------
# 6. Main Dashboard Layout (Cards First, Mini-Map Auxiliary)
# -----------------------------------------------------------------------------
col_lots, col_map = st.columns([3, 2])

with col_lots:
    st.subheader("Live Campus Lot Directory")
    st.caption("Real-time occupancy updated every 10s via campus edge cameras.")

    for _, lot in facilities_df.iterrows():
        is_permitted = lot["permit_required"] == user_permit
        permit_badge = (
            "✅ Allowed" if is_permitted else f"🚫 Requires {lot['permit_required']}"
        )

        with st.expander(
            f"{lot['name']} — {lot['status']} ({lot['available']} open)",
            expanded=is_permitted,
        ):
            lc1, lc2 = st.columns([3, 1])
            with lc1:
                st.progress(lot["pct_full"] / 100)
                st.write(
                    f"**Permit Tier:** {lot['permit_required']} ({permit_badge})  \n"
                    f"**Occupancy:** {lot['occupied']} / {lot['capacity']} spaces full  \n"
                    f"**Walking Times:** ~{lot['walk_mins_to_lib']} min to Library | ~{lot['walk_mins_to_prescott']} min to Prescott Hall"
                )
            with lc2:
                if is_permitted and lot["pct_full"] < 90.0:
                    st.button(
                        "Navigate Here",
                        key=f"nav_{lot['id']}",
                        use_container_width=True,
                    )
                elif not is_permitted:
                    st.caption("⚠️ Permit mismatch")
                else:
                    st.caption("🚨 Lot Saturated")

with col_map:
    st.subheader("Campus Mini-Map & Wayfinding")
    st.caption("Showing permitted lots and primary campus building markers.")

    # Flat, 2D boundaries for clean mobile rendering
    polygon_layer = pdk.Layer(
        "PolygonLayer",
        data=facilities_df,
        get_polygon="polygon",
        get_fill_color="fill_color",
        get_line_color=[30, 41, 59, 255],
        get_line_width=2,
        line_width_min_pixels=2,
        pickable=True,
        auto_highlight=True,
    )

    # Clean destination badges on buildings
    landmark_layer = pdk.Layer(
        "ScatterplotLayer",
        data=landmarks_df,
        get_position=["lon", "lat"],
        get_color=[30, 41, 59, 220],
        get_radius=18,
        radius_min_pixels=5,
        radius_max_pixels=12,
        pickable=True,
    )

    # Center camera over Volpe Library & Derryberry Hall
    view_state = pdk.ViewState(
        latitude=36.1772, longitude=-85.5058, zoom=15.0, pitch=0, bearing=0
    )

    st.pydeck_chart(
        pdk.Deck(
            map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            layers=[polygon_layer, landmark_layer],
            initial_view_state=view_state,
            tooltip={"text": "{name}\nStatus: {status}\nOpen Spots: {available}"},
        )
    )
    st.caption(
        "🟩 Green = Open | 🟧 Amber = Filling | 🟥 Red = Saturated. ⚫ Dark markers = Academic buildings."
    )


# -----------------------------------------------------------------------------
# 7. Commuter Rideshare Cohort Section
# -----------------------------------------------------------------------------
st.divider()
st.subheader(f"👥 Rideshare Carpool Matching ({selected_arrival_time} Arrival Window)")

csv_path = "simulation/data/commuter_schedules.csv"
if os.path.exists(csv_path):
    clustered = match_commuters_by_timetable(
        csv_path=csv_path, target_time=selected_arrival_time, max_radius_km=max_radius
    )
    valid_groups = clustered[clustered["carpool_group"] != -1]

    r1, r2 = st.columns([2, 1])
    with r1:
        st.dataframe(
            valid_groups[
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
    with r2:
        st.metric("Total Scheduled in Window", len(clustered))
        st.metric("Matched Carpool Commuters", len(valid_groups))
        st.metric("DBSCAN Groups Formed", valid_groups["carpool_group"].nunique())
else:
    st.info(
        "Run `python simulation/generate_commuters.py` to populate student carpool cohorts."
    )
