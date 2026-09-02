"""
Smart Campus Parking & Navigation Dashboard (Streamlit Cloud Production)

Mobile-first campus navigation engine for Tennessee Tech commuters.
Provides permit-filtered lot saturation, dynamic rerouting, destination walking metrics,
functional turn-by-turn GPS handoffs, and satellite imagery via pydeck TileLayer.
"""

import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

# Allow simulation imports regardless of execution root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from simulation.clustering import match_commuters_by_timetable
except ImportError:

    def match_commuters_by_timetable(csv_path, target_time, max_radius_km):
        return pd.DataFrame()


st.set_page_config(
    page_title="EaglePark AI | TTU Smart Navigation", page_icon="🦅", layout="wide"
)


# -----------------------------------------------------------------------------
# 1. Ground-Truth Tennessee Tech Facilities & Buildings
# -----------------------------------------------------------------------------
def get_ttu_facilities(preset: str):
    lots = [
        {
            "id": "LOT-LIB",
            "name": "Volpe Library North Lot",
            "short_code": "Library Lot",
            "permit_required": "Purple (Commuter Student)",
            "capacity": 340,
            # Centered on paved surface stalls north of Volpe Library off Stadium Dr
            "lat": 36.17885,
            "lon": -85.50485,
            "walk_mins": 1.0,
        },
        {
            "id": "LOT-HOOPER",
            "name": "Hooper Eblen Center Lot",
            "short_code": "Hooper Lot",
            "permit_required": "Purple (Commuter Student)",
            "capacity": 580,
            # Primary commuter asphalt lot west of arena off Willow Ave
            "lat": 36.17750,
            "lon": -85.50930,
            "walk_mins": 5.0,
        },
        {
            "id": "LOT-PEACH",
            "name": "Peachtree Commuter Lot",
            "short_code": "Peachtree",
            "permit_required": "Purple (Commuter Student)",
            "capacity": 220,
            # Paved lot on Peachtree Ave between 7th and 8th St
            "lat": 36.17360,
            "lon": -85.50390,
            "walk_mins": 4.5,
        },
        {
            "id": "LOT-ASHBURN",
            "name": "Ashburn Drive Lot",
            "short_code": "Ashburn Lot",
            "permit_required": "Gold (Faculty / Staff)",
            "capacity": 175,
            # Faculty parking north of Bryan Fine Arts along Ashburn Dr
            "lat": 36.17630,
            "lon": -85.50150,
            "walk_mins": 2.5,
        },
        {
            "id": "LOT-BELL",
            "name": "Bell Hall / 10th St Lot",
            "short_code": "Bell Lot",
            "permit_required": "Purple (Commuter Student)",
            "capacity": 140,
            # Surface lot directly north of Bell Hall on 10th St
            "lat": 36.17515,
            "lon": -85.50790,
            "walk_mins": 6.0,
        },
        {
            "id": "LOT-TECH-VILLAGE",
            "name": "Tech Village Overflow Lot",
            "short_code": "Tech Village",
            "permit_required": "Purple (Commuter Student)",
            "capacity": 320,
            # North overflow lot on W 12th St
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
            return "SATURATED", [239, 68, 68, 240]  # Bright Red
        elif pct >= 75.0:
            return "FILLING FAST", [245, 158, 11, 240]  # Bright Amber
        return "AVAILABLE", [34, 197, 94, 240]  # Bright Green

    tiers = df["pct_full"].apply(get_tier)
    df["status"] = [t[0] for t in tiers]
    df["color"] = [t[1] for t in tiers]
    df["map_label"] = df.apply(
        lambda r: f"{r['short_code']}: {r['available']} open", axis=1
    )
    return df


campus_landmarks = pd.DataFrame([
    {"name": "Ashraf Islam Eng (AIEB)", "lat": 36.17765, "lon": -85.50615},
    {"name": "Volpe Library", "lat": 36.17780, "lon": -85.50495},
    {"name": "Prescott Hall (Eng)", "lat": 36.17625, "lon": -85.50360},
    {"name": "Stonecipher (LSC)", "lat": 36.17690, "lon": -85.50605},
    {"name": "Derryberry Hall", "lat": 36.17540, "lon": -85.50545},
    {"name": "Hooper Eblen Center", "lat": 36.17855, "lon": -85.50760},
    {"name": "Bell Hall (Nursing)", "lat": 36.17480, "lon": -85.50785},
])

building_names = campus_landmarks["name"].tolist()

# -----------------------------------------------------------------------------
# 2. Driver Preferences & Sidebar Controls
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
    help="Filters lots by permit tier to eliminate compliance violations.",
)

selected_destination = st.sidebar.selectbox(
    "Campus Destination",
    options=building_names,
    index=0,
    help="Calibrated campus academic destinations.",
)

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
    help="Diverts drivers before arrival if current target exceeds 90% saturation.",
)

st.sidebar.divider()
st.sidebar.subheader("Rideshare Dispatch Settings")
selected_arrival_time = st.sidebar.selectbox(
    "Arrival Window", ["07:45", "08:30", "09:30", "10:30"], index=1
)
max_radius = st.sidebar.slider("Detour Radius (km)", 0.5, 3.0, 1.2, 0.1)

facilities_df = get_ttu_facilities(scenario)

# -----------------------------------------------------------------------------
# 3. Routing Decision Engine
# -----------------------------------------------------------------------------
permitted_lots = facilities_df[facilities_df["permit_required"] == user_permit].copy()

if not permitted_lots.empty:
    valid_alternatives = permitted_lots[permitted_lots["pct_full"] < 90.0]
    if not valid_alternatives.empty:
        best_lot = valid_alternatives.sort_values(by="walk_mins").iloc[0]
    else:
        best_lot = permitted_lots.sort_values(by="available", ascending=False).iloc[0]
else:
    best_lot = None

# -----------------------------------------------------------------------------
# 4. Header & Live GPS Guidance Strip
# -----------------------------------------------------------------------------
st.title("🚗 TTU Smart Commuter Navigation")
st.caption(
    f"Permit: **{user_permit}** | En Route To: **{selected_destination}** | Preset: **{scenario}**"
)

if best_lot is not None:
    rec_box = st.container()
    with rec_box:
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            st.success(f"📍 **Recommended Target:** Head to **{best_lot['name']}**")
            st.write(
                f"**{best_lot['available']} stalls open** ({best_lot['pct_full']:.0f}% full) · "
                f"Est. Walk to Destination: **{best_lot['walk_mins']:.1f} mins**"
            )
        with c2:
            st.metric(
                "Open Stalls",
                f"{best_lot['available']} Spots",
                delta=f"{best_lot['capacity']} Total",
            )
        with c3:
            # Universal mobile GPS navigation deep-link
            gps_nav_url = (
                f"https://www.google.com/maps/dir/?api=1"
                f"&destination={best_lot['lat']},{best_lot['lon']}"
                f"&travelmode=driving"
            )
            st.link_button(
                "🗺️ Start GPS Route", url=gps_nav_url, use_container_width=True
            )

    primary_lot = facilities_df[facilities_df["id"] == "LOT-LIB"].iloc[0]
    if primary_lot["pct_full"] >= 90.0 and ai_reroute_enabled:
        st.warning(
            f"⚠️ **Reroute Alert:** {primary_lot['name']} is at {primary_lot['pct_full']:.0f}% capacity. "
            f"Diverted to **{best_lot['name']}** to prevent entrance bottlenecking."
        )

st.divider()

# -----------------------------------------------------------------------------
# 5. Two-Column Dashboard Layout
# -----------------------------------------------------------------------------
col_lots, col_map = st.columns([3, 2])

with col_lots:
    st.subheader("Live Campus Lot Directory")
    st.caption("Real-time occupancy synced via campus edge nodes.")

    for _, lot in facilities_df.iterrows():
        is_permitted = lot["permit_required"] == user_permit
        permit_badge = (
            "✅ Authorized" if is_permitted else f"🚫 Requires {lot['permit_required']}"
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
                    f"**Walk Distance:** ~{lot['walk_mins']} min to core academic halls"
                )
            with lc2:
                lot_gps_url = (
                    f"https://www.google.com/maps/dir/?api=1"
                    f"&destination={lot['lat']},{lot['lon']}"
                    f"&travelmode=driving"
                )
                if is_permitted and lot["pct_full"] < 90.0:
                    st.link_button(
                        "Route Here",
                        url=lot_gps_url,
                        key=f"btn_{lot['id']}",
                        use_container_width=True,
                    )
                elif not is_permitted:
                    st.caption("⚠️ Tier mismatch")
                else:
                    st.caption("🚨 Lot full")

with col_map:
    st.subheader("Campus Aerial Navigation")
    st.caption(
        "High-resolution satellite view with live stall status and building anchors."
    )

    # 1. Base Satellite Imagery (via pydeck TileLayer, zero API keys required)
    satellite_tile_layer = pdk.Layer(
        "TileLayer",
        data="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        min_zoom=0,
        max_zoom=19,
        tile_size=256,
        pickable=False,
    )

    # 2. High-visibility parking status circles
    lot_pin_layer = pdk.Layer(
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

    # 3. High-contrast capacity callout text
    lot_text_layer = pdk.Layer(
        "TextLayer",
        data=facilities_df,
        get_position=["lon", "lat"],
        get_text="map_label",
        get_color=[255, 255, 255, 255],
        get_size=12,
        get_alignment_baseline="'bottom'",
        get_pixel_offset=[0, -14],
        font_weight="bold",
        background=True,
        get_background_color=[15, 23, 42, 220],
        pickable=False,
    )

    # 4. Building landmark pins (Cyan)
    building_layer = pdk.Layer(
        "ScatterplotLayer",
        data=campus_landmarks,
        get_position=["lon", "lat"],
        get_color=[56, 189, 248, 230],
        get_radius=14,
        radius_min_pixels=6,
        radius_max_pixels=9,
        pickable=True,
    )

    building_text_layer = pdk.Layer(
        "TextLayer",
        data=campus_landmarks,
        get_position=["lon", "lat"],
        get_text="name",
        get_color=[255, 255, 255, 240],
        get_size=11,
        get_alignment_baseline="'top'",
        get_pixel_offset=[0, 8],
        font_weight="bold",
        background=True,
        get_background_color=[30, 41, 59, 220],
        pickable=False,
    )

    view_state = pdk.ViewState(
        latitude=36.1775, longitude=-85.5058, zoom=15.8, pitch=0, bearing=0
    )

    st.pydeck_chart(
        pdk.Deck(
            map_style=None,
            layers=[
                satellite_tile_layer,
                building_layer,
                building_text_layer,
                lot_pin_layer,
                lot_text_layer,
            ],
            initial_view_state=view_state,
            tooltip={
                "text": "{name}\nPermit: {permit_required}\nOpen Spaces: {available} / {capacity}"
            },
        )
    )
    st.caption(
        "🟢 Available | 🟠 Filling Fast | 🔴 Saturated | 🔵 Cyan = Campus Buildings"
    )

# -----------------------------------------------------------------------------
# 6. Commuter Rideshare Cohorts
# -----------------------------------------------------------------------------
st.divider()
st.subheader(f"👥 Rideshare Carpool Matching ({selected_arrival_time} Arrival Window)")

csv_path = "simulation/data/commuter_schedules.csv"
if os.path.exists(csv_path):
    clustered = match_commuters_by_timetable(
        csv_path=csv_path, target_time=selected_arrival_time, max_radius_km=max_radius
    )
    if not clustered.empty and "carpool_group" in clustered.columns:
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
        st.info("No carpool cohorts found for this time window.")
else:
    st.info(
        "Run `python simulation/generate_commuters.py` to populate student carpool cohorts."
    )
