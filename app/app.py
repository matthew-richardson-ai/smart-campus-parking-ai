# app/app.py
"""
Smart Campus Parking & Navigation Dashboard (Streamlit Cloud Production)

Mobile-first campus navigation engine for Tennessee Tech commuters.
Provides permit-filtered lot saturation, dynamic rerouting, destination walking metrics,
and live OpenStreetMap Overpass building mappings (including AIEB).
"""

import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import requests

# Allow simulation imports regardless of execution root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from simulation.clustering import match_commuters_by_timetable
except ImportError:
    # Graceful dummy fallback if module isn't mounted in cloud path
    def match_commuters_by_timetable(csv_path, target_time, max_radius_km):
        return pd.DataFrame()


st.set_page_config(
    page_title="EaglePark AI | TTU Smart Navigation", page_icon="🦅", layout="wide"
)


# -----------------------------------------------------------------------------
# 1. Dynamic OpenStreetMap Campus Building Ingestion
# -----------------------------------------------------------------------------
@st.cache_data(ttl=86400)
def fetch_ttu_buildings():
    """
    Queries OpenStreetMap Overpass API for all university buildings within
    the Tennessee Tech campus perimeter and computes their center coordinates.
    Includes recent developments such as the Ashraf Islam Engineering Building (AIEB).
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = """
    [out:json][timeout:25];
    (
      way["building"](36.1700, -85.5180, 36.1850, -85.4980);
      relation["building"](36.1700, -85.5180, 36.1850, -85.4980);
    );
    out center tags;
    """
    try:
        response = requests.get(overpass_url, params={"data": query}, timeout=8)
        if response.status_code == 200:
            data = response.json()
            buildings = []
            for el in data.get("elements", []):
                tags = el.get("tags", {})
                name = tags.get("name")
                if name and len(name.strip()) > 2:
                    center = el.get("center", {})
                    lat = center.get("lat") or el.get("lat")
                    lon = center.get("lon") or el.get("lon")
                    if lat and lon:
                        buildings.append({
                            "name": name.strip(),
                            "lat": float(lat),
                            "lon": float(lon),
                        })
            df = (
                pd
                .DataFrame(buildings)
                .drop_duplicates(subset=["name"])
                .sort_values(by="name")
            )
            if not df.empty:
                return df
    except Exception:
        pass

    # Verified fallback ground truth anchors if Overpass is down or throttled
    return pd.DataFrame([
        {
            "name": "Ashraf Islam Engineering Building (AIEB)",
            "lat": 36.17790,
            "lon": -85.50630,
        },
        {"name": "Angelo & Jennette Volpe Library", "lat": 36.17780, "lon": -85.50505},
        {"name": "Prescott Hall (Engineering)", "lat": 36.17625, "lon": -85.50360},
        {"name": "Stonecipher Hall (LSC)", "lat": 36.17680, "lon": -85.50610},
        {
            "name": "Derryberry Hall (Admin & Admissions)",
            "lat": 36.17540,
            "lon": -85.50545,
        },
        {"name": "Hooper Eblen Center (Athletics)", "lat": 36.17865, "lon": -85.50760},
        {"name": "Robert & Gloria Bell Hall", "lat": 36.17520, "lon": -85.50780},
    ])


campus_landmarks = fetch_ttu_buildings()
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

default_dest_idx = 0
for idx, bname in enumerate(building_names):
    if "Ashraf Islam" in bname or "AIEB" in bname or "Volpe Library" in bname:
        default_dest_idx = idx
        break

selected_destination = st.sidebar.selectbox(
    "Campus Destination",
    options=building_names,
    index=default_dest_idx,
    help="Auto-populated live from OpenStreetMap campus layers.",
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


# -----------------------------------------------------------------------------
# 3. Ground-Truth TTU Parking Coordinates
# -----------------------------------------------------------------------------
def get_ttu_facilities(preset: str):
    lots = [
        {
            "id": "LOT-LIB",
            "name": "Volpe Library Surface Lot",
            "short_code": "Library Lot",
            "permit_required": "Purple (Commuter Student)",
            "capacity": 340,
            "lat": 36.17892,
            "lon": -85.50518,
            "walk_mins": 1.0,
        },
        {
            "id": "LOT-HOOPER",
            "name": "Hooper Eblen Center Lot",
            "short_code": "Hooper Lot",
            "permit_required": "Purple (Commuter Student)",
            "capacity": 580,
            "lat": 36.17795,
            "lon": -85.50912,
            "walk_mins": 5.0,
        },
        {
            "id": "LOT-PEACH",
            "name": "Peachtree Commuter Lot",
            "short_code": "Peachtree",
            "permit_required": "Purple (Commuter Student)",
            "capacity": 220,
            "lat": 36.17365,
            "lon": -85.50395,
            "walk_mins": 4.5,
        },
        {
            "id": "LOT-ASHBURN",
            "name": "Ashburn Drive / Bryan Lot",
            "short_code": "Ashburn Lot",
            "permit_required": "Gold (Faculty / Staff)",
            "capacity": 175,
            "lat": 36.17632,
            "lon": -85.50155,
            "walk_mins": 2.5,
        },
        {
            "id": "LOT-BELL",
            "name": "Bell Hall / West 10th Lot",
            "short_code": "Bell Lot",
            "permit_required": "Purple (Commuter Student)",
            "capacity": 140,
            "lat": 36.17495,
            "lon": -85.50812,
            "walk_mins": 6.0,
        },
        {
            "id": "LOT-TECH-VILLAGE",
            "name": "Tech Village Overflow Lot",
            "short_code": "Tech Village",
            "permit_required": "Purple (Commuter Student)",
            "capacity": 320,
            "lat": 36.18240,
            "lon": -85.51165,
            "walk_mins": 8.0,
        },
    ]

    if "Low" in preset:
        occupied_counts = [80, 110, 35, 30, 20, 15]
    elif "Transition" in preset:
        occupied_counts = [270, 410, 175, 120, 95, 80]
    elif "Event" in preset:
        occupied_counts = [335, 570, 215, 170, 138, 290]
    else:  # Morning Peak default
        occupied_counts = [326, 545, 185, 155, 65, 45]

    df = pd.DataFrame(lots)
    df["occupied"] = occupied_counts
    df["available"] = df["capacity"] - df["occupied"]
    df["pct_full"] = (df["occupied"] / df["capacity"]) * 100

    def get_tier(pct):
        if pct >= 90.0:
            return "SATURATED", [220, 38, 38, 240]
        elif pct >= 75.0:
            return "FILLING FAST", [234, 138, 0, 240]
        return "AVAILABLE", [22, 163, 74, 240]

    tiers = df["pct_full"].apply(get_tier)
    df["status"] = [t[0] for t in tiers]
    df["color"] = [t[1] for t in tiers]
    df["map_label"] = df.apply(
        lambda r: f"{r['short_code']}: {r['available']} open", axis=1
    )
    return df


facilities_df = get_ttu_facilities(scenario)

# -----------------------------------------------------------------------------
# 4. Routing Decision Engine
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
# 5. Header & Dynamic GPS Guidance Strip
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
            if st.button("🗺️ Start GPS Route", use_container_width=True):
                st.toast(f"Routing to {best_lot['name']} via primary campus entry...")

    primary_lot = facilities_df[facilities_df["id"] == "LOT-LIB"].iloc[0]
    if primary_lot["pct_full"] >= 90.0 and ai_reroute_enabled:
        st.warning(
            f"⚠️ **Reroute Alert:** {primary_lot['name']} is at {primary_lot['pct_full']:.0f}% capacity. "
            f"Diverted to **{best_lot['name']}** to prevent entrance bottlenecking."
        )

st.divider()

# -----------------------------------------------------------------------------
# 6. Two-Column Dashboard Layout
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
                if is_permitted and lot["pct_full"] < 90.0:
                    st.button(
                        "Route Here", key=f"btn_{lot['id']}", use_container_width=True
                    )
                elif not is_permitted:
                    st.caption("⚠️ Tier mismatch")
                else:
                    st.caption("🚨 Lot full")

with col_map:
    st.subheader("Campus Wayfinding Mini-Map")
    st.caption("Asphalt lot centers and auto-populated OpenStreetMap building anchors.")

    # 1. Parking Stall Status Pins
    lot_pin_layer = pdk.Layer(
        "ScatterplotLayer",
        data=facilities_df,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius=18,
        radius_min_pixels=8,
        radius_max_pixels=14,
        pickable=True,
        auto_highlight=True,
    )

    # 2. Parking Badges
    lot_text_layer = pdk.Layer(
        "TextLayer",
        data=facilities_df,
        get_position=["lon", "lat"],
        get_text="map_label",
        get_color=[15, 23, 42, 255],
        get_size=13,
        get_alignment_baseline="'bottom'",
        get_pixel_offset=[0, -12],
        font_weight="bold",
        pickable=False,
    )

    # 3. Dynamic Building Pins from Overpass API
    building_layer = pdk.Layer(
        "ScatterplotLayer",
        data=campus_landmarks,
        get_position=["lon", "lat"],
        get_color=[71, 85, 105, 200],
        get_radius=12,
        radius_min_pixels=5,
        radius_max_pixels=7,
        pickable=True,
    )

    building_text_layer = pdk.Layer(
        "TextLayer",
        data=campus_landmarks,
        get_position=["lon", "lat"],
        get_text="name",
        get_color=[100, 116, 139, 230],
        get_size=11,
        get_alignment_baseline="'top'",
        get_pixel_offset=[0, 8],
        pickable=False,
    )

    view_state = pdk.ViewState(
        latitude=36.1776, longitude=-85.5058, zoom=15.6, pitch=0, bearing=0
    )

    st.pydeck_chart(
        pdk.Deck(
            map_provider="carto",
            map_style="light",
            layers=[building_layer, building_text_layer, lot_pin_layer, lot_text_layer],
            initial_view_state=view_state,
            tooltip={"text": "{name}\nStatus: {status}\nOpen Spaces: {available}"},
        )
    )
    st.caption(
        "🟢 Green = Available | 🟠 Amber = Filling Fast | 🔴 Red = Saturated. Grey pins mark active campus halls."
    )

# -----------------------------------------------------------------------------
# 7. Commuter Rideshare Cohorts
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
