"""
Smart Campus Parking & Navigation Dashboard (Streamlit Prototype)

This module serves as the primary GUI and simulation sandbox for demonstrating
dynamic parking redistribution and rideshare matching. It reads synthetic student
commuter schedules and executes DBSCAN spatial clustering to visualize real-time
rideshare pairing alongside lot saturation telemetry.
"""

import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

# Ensure python can locate the local simulation module regardless of execution directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from simulation.clustering import match_commuters_by_timetable

# Configure page metadata and wide layout
st.set_page_config(page_title="Campus AI Traffic & Rideshare Engine", layout="wide")

# -----------------------------------------------------------------------------
# 1. Session State Initialization
# -----------------------------------------------------------------------------
if "traffic_condition" not in st.session_state:
    st.session_state.traffic_condition = "Morning Rush (High Congestion)"


# -----------------------------------------------------------------------------
# 2. Interactive Control Sidebar
# -----------------------------------------------------------------------------
st.sidebar.title("🎛️ Simulation Controls")

scenario = st.sidebar.selectbox(
    "Campus Traffic Scenario",
    [
        "Morning Rush (High Congestion)",
        "Midday Transition (Moderate)",
        "Evening / Weekend (Low Traffic)",
        "Game Day / Campus Event (Critical Saturation)",
    ],
    help="Simulates distinct vehicle demand spikes corresponding to academic class blocks.",
)

st.sidebar.subheader("Environmental Variables")
weather = st.sidebar.selectbox(
    "Weather Condition",
    ["Clear", "Heavy Rain (Vision Degraded)", "Dense Fog"],
    help="Models camera optical distortion, glare, and edge-vision confidence loss.",
)

ai_reroute_enabled = st.sidebar.toggle(
    "Enable Dynamic AI Rerouting",
    value=True,
    help="When enabled, in-transit drivers are automatically diverted if target lots reach >=90% capacity.",
)

st.sidebar.divider()
st.sidebar.subheader("Commuter Clustering Parameters")
selected_arrival_time = st.sidebar.selectbox(
    "Target Class Arrival Block",
    ["07:45", "08:30", "09:30", "10:30"],
    index=1,
    help="Filters commuters needing to reach campus within this arrival window.",
)

max_radius = st.sidebar.slider(
    "Max Pickup Detour Radius (km)",
    min_value=0.5,
    max_value=3.0,
    value=1.2,
    step=0.1,
    help="Defines DBSCAN epsilon (maximum spherical distance allowed between carpool riders).",
)


# -----------------------------------------------------------------------------
# 3. Dynamic Parking Lot Data Generator
# -----------------------------------------------------------------------------
def get_simulated_lot_data(preset: str, weather_mode: str):
    """
    Synthesizes real-time parking lot occupancy based on scenario presets.
    """
    lots = [
        {
            "id": "LOT-A",
            "name": "North Commuter Lot",
            "capacity": 300,
            "lat": 36.1775,
            "lon": -85.5030,
        },
        {
            "id": "LOT-B",
            "name": "South Parking Garage",
            "capacity": 550,
            "lat": 36.1730,
            "lon": -85.5055,
        },
        {
            "id": "LOT-C",
            "name": "East Peripheral Overflow",
            "capacity": 200,
            "lat": 36.1790,
            "lon": -85.4980,
        },
    ]

    if "Low" in preset:
        occupancies = [65, 120, 10]
        avg_wait = "0 mins"
    elif "Moderate" in preset:
        occupancies = [210, 380, 45]
        avg_wait = "4.5 mins"
    elif "Critical" in preset:
        occupancies = [298, 545, 195]
        avg_wait = "18.2 mins"
    else:  # Morning Rush default
        occupancies = [285, 410, 30]
        avg_wait = "9.8 mins"

    df = pd.DataFrame(lots)
    df["occupied"] = occupancies
    df["pct_full"] = (df["occupied"] / df["capacity"]) * 100

    # Degrade confidence based on simulated visibility
    if weather_mode == "Clear":
        confidence = 98.5
    elif "Rain" in weather_mode:
        confidence = 82.1
    else:
        confidence = 74.0

    df["sensor_confidence"] = confidence
    return df, avg_wait


lot_data, wait_time = get_simulated_lot_data(scenario, weather)

# -----------------------------------------------------------------------------
# 4. Clustered Commuter Data Pipeline
# -----------------------------------------------------------------------------
csv_path = "simulation/data/commuter_schedules.csv"
if os.path.exists(csv_path):
    clustered_commuters = match_commuters_by_timetable(
        csv_path=csv_path, target_time=selected_arrival_time, max_radius_km=max_radius
    )
    valid_carpools = clustered_commuters[clustered_commuters["carpool_group"] != -1]
    num_matched_students = len(valid_carpools)
    num_distinct_groups = valid_carpools["carpool_group"].nunique()
else:
    clustered_commuters = pd.DataFrame()
    num_matched_students = 0
    num_distinct_groups = 0


# -----------------------------------------------------------------------------
# 5. Header & Executive Metric Strip
# -----------------------------------------------------------------------------
st.title("🚗 Smart Campus Parking & Navigation Dashboard")
st.caption(
    f"Active Scenario: **{scenario}** | Edge Vision Confidence: **{lot_data['sensor_confidence'].iloc[0]}%**"
)

m1, m2, m3, m4 = st.columns(4)
total_capacity = lot_data["capacity"].sum()
total_occupied = lot_data["occupied"].sum()
system_pct = (total_occupied / total_capacity) * 100

m1.metric(
    label="Campus Lot Saturation",
    value=f"{total_occupied} / {total_capacity}",
    delta=f"{system_pct:.1f}% Capacity",
)
m2.metric(
    label="Avg. Time-to-Park",
    value=wait_time,
    delta="-3.2 min with AI" if ai_reroute_enabled else "+4.5 min queuing",
    delta_color="normal" if ai_reroute_enabled else "inverse",
)
m3.metric(
    label="In-Transit Reroutes",
    value="42 Diverted" if ai_reroute_enabled else "0 (Disabled)",
    delta="Balancing overflow" if ai_reroute_enabled else "Gate bottlenecks",
    delta_color="normal" if ai_reroute_enabled else "off",
)
m4.metric(
    label=f"Active Carpools ({selected_arrival_time})",
    value=f"{num_distinct_groups} Groups",
    delta=f"{num_matched_students} Students paired",
)

st.divider()

# -----------------------------------------------------------------------------
# 6. Main Dashboard Tabs
# -----------------------------------------------------------------------------
tab_map, tab_driver, tab_rideshare = st.tabs([
    "📍 Interactive Campus & Commuter Map",
    "📱 Driver Navigation View",
    "👥 DBSCAN Rideshare Cohorts",
])

with tab_map:
    col_view, col_status = st.columns([2, 1])

    with col_view:
        st.subheader("Spatial Saturation & Commuter Hubs")

        # Color mapping helper for DBSCAN clusters
        palette = [
            [230, 25, 75],  # Red
            [60, 180, 75],  # Green
            [255, 225, 25],  # Yellow
            [0, 130, 200],  # Blue
            [245, 130, 48],  # Orange
            [145, 30, 180],  # Purple
            [70, 240, 240],  # Cyan
        ]

        layers = []

        # Layer 1: Campus Parking Facilities
        parking_layer = pdk.Layer(
            "ScatterplotLayer",
            data=lot_data,
            get_position=["lon", "lat"],
            get_color="[255, 0, 0, 180]",
            get_radius="occupied * 1.5",
            pickable=True,
            auto_highlight=True,
        )
        layers.append(parking_layer)

        # Layer 2: Commuter Pickups (if dataset present)
        if not clustered_commuters.empty:
            # Assign RGB colors based on cluster label (-1 is grey noise)
            def assign_color(group_id):
                if group_id == -1:
                    return [160, 160, 160, 120]
                return palette[group_id % len(palette)] + [200]

            plot_df = clustered_commuters.copy()
            plot_df["color"] = plot_df["carpool_group"].apply(assign_color)
            plot_df["radius"] = plot_df["has_car"].apply(lambda has: 90 if has else 45)

            commuter_layer = pdk.Layer(
                "ScatterplotLayer",
                data=plot_df,
                get_position=["home_lon", "home_lat"],
                get_color="color",
                get_radius="radius",
                pickable=True,
                auto_highlight=True,
            )
            layers.append(commuter_layer)

        view_state = pdk.ViewState(
            latitude=36.1775, longitude=-85.5030, zoom=13, pitch=35
        )

        st.pydeck_chart(
            pdk.Deck(
                layers=layers,
                initial_view_state=view_state,
                tooltip={
                    "text": "Lot/Commuter Telemetry: {name}\nCapacity/Group: {capacity}{carpool_group}"
                },
            )
        )
        st.caption(
            "🔴 Red hubs = Campus parking lots (scaled by occupancy). 🔵 Multi-colored dots = Matched commuter carpools. ⚪ Grey dots = Isolated commuters (DBSCAN noise)."
        )

    with col_status:
        st.subheader("Lot Saturation Telemetry")
        for _, row in lot_data.iterrows():
            pct = row["pct_full"]
            st.write(f"**{row['name']}**")
            if pct >= 90.0:
                st.progress(
                    pct / 100,
                    text=f"🚨 {row['occupied']}/{row['capacity']} ({pct:.0f}%) - SATURATED",
                )
                if ai_reroute_enabled:
                    st.info(
                        "⚡ *Automated Reroute Active:* Diverting incoming traffic to East Overflow."
                    )
            elif pct >= 75.0:
                st.progress(
                    pct / 100,
                    text=f"⚠️ {row['occupied']}/{row['capacity']} ({pct:.0f}%) - HIGH CONGESTION",
                )
            else:
                st.progress(
                    pct / 100,
                    text=f"✅ {row['occupied']}/{row['capacity']} ({pct:.0f}%) - AVAILABLE",
                )

with tab_driver:
    st.subheader("In-Transit Driver Telemetry (Walk Stage Simulation)")
    d_col1, d_col2 = st.columns([1, 1])

    with d_col1:
        target_lot = "North Commuter Lot"
        lot_a_full = (
            lot_data.loc[lot_data["id"] == "LOT-A", "pct_full"].values[0] >= 90.0
        )

        if lot_a_full and ai_reroute_enabled:
            st.error(f"⚠️ Destination '{target_lot}' reached saturation (95% full)!")
            st.success(
                "🤖 Dynamic AI Reroute: Diverting to East Peripheral Overflow (15% full). Added walk time: +2 mins."
            )
        elif lot_a_full and not ai_reroute_enabled:
            st.error(
                f"⚠️ Destination '{target_lot}' is full. Drivers will experience gate delays."
            )
        else:
            st.success(
                f"Clear route: Proceeding to {target_lot}. Open spaces verified via vision sensors."
            )

    with d_col2:
        st.info(
            "💡 **Human-in-the-Loop Walk Stage:** The driver retains final override authority on the suggested detour with a single tap, ensuring driver agency without sudden navigation disruptions."
        )

with tab_rideshare:
    st.subheader(f"DBSCAN Commuter Clusters for {selected_arrival_time} Arrival Window")
    if not clustered_commuters.empty:
        st.write(
            f"**Total Cohort Size:** {len(clustered_commuters)} students | **Clustered into Carpools:** {num_matched_students} students across {num_distinct_groups} groups"
        )

        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            st.dataframe(
                valid_carpools[
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
        with col_c2:
            st.metric(
                "Excluded Outliers (Noise Points)",
                f"{(clustered_commuters['carpool_group'] == -1).sum()} Commuters",
            )
            st.write(
                "Commuters marked with cluster `-1` reside beyond the specified pickup radius threshold and will not create excessive driver detours."
            )
    else:
        st.warning(
            "No synthetic commuter schedules found. Please run `simulation/generate_commuters.py`."
        )
