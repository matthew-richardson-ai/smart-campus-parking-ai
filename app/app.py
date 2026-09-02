"""
Smart Campus Parking & Navigation Dashboard (Streamlit Prototype)

This module serves as the primary GUI and simulation sandbox for demonstrating
dynamic parking redistribution and rideshare matching. It exposes high-level
system states, environmental variables, and simulated student driver views
to evaluate Human-in-the-Loop decision flows without requiring live camera hardware.
"""

import streamlit as st
import pandas as pd
import numpy as np

# Configure the browser tab title and default to wide mode so our map and telemetry cards sit side-by-side
st.set_page_config(page_title="Campus AI Traffic & Parking Simulator", layout="wide")

# -----------------------------------------------------------------------------
# 1. Session State Initialization
# -----------------------------------------------------------------------------
# Streamlit re-executes this entire script on every user interaction. We store
# mutable state variables in `st.session_state` so user changes persist across runs.
if "traffic_condition" not in st.session_state:
    st.session_state.traffic_condition = "Morning Rush (High Congestion)"


# -----------------------------------------------------------------------------
# 2. Interactive Control Sidebar
# -----------------------------------------------------------------------------
st.sidebar.title("🎛️ Simulation Control Panel")

# These presets allow us to jump between distinct operational profiles during
# our presentation without manually tweaking each lot's vehicle counts.
scenario = st.sidebar.selectbox(
    "Select Scenario Preset",
    [
        "Morning Rush (High Congestion)",
        "Midday Transition (Moderate)",
        "Evening / Weekend (Low Traffic)",
        "Game Day / Campus Event (Critical Saturation)",
    ],
    help="Simulates distinct traffic distributions reflecting academic bell schedules.",
)

st.sidebar.subheader("Environmental Variables")

# Weather impacts vision-based camera inference accuracy in real edge deployments.
weather = st.sidebar.selectbox(
    "Weather Condition",
    ["Clear", "Heavy Rain (Vision Degraded)", "Dense Fog"],
    help="Simulates optical occlusion and camera confidence degradation.",
)

# This toggle simulates our Walk-stage Human-in-the-Loop dynamic routing feature.
# When disabled, drivers behave normally without AI guidance and pile into saturated lots.
ai_reroute_enabled = st.sidebar.toggle(
    "Enable Dynamic AI Rerouting",
    value=True,
    help="When enabled, in-transit drivers are diverted once a lot hits >=90% capacity.",
)


# -----------------------------------------------------------------------------
# 3. Dynamic State Generation
# -----------------------------------------------------------------------------
def get_simulated_lot_data(preset: str, weather_mode: str):
    """
    Synthesizes real-time parking telemetry based on the active scenario and weather.

    In a full deployment, this data would arrive via edge-vision inference streams
    from perimeter camera nodes. Here, we model realistic congestion distributions
    across three core campus parking hubs.
    """
    # Baseline coordinates and parking capacities for campus lots
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

    # Map presets to expected vehicle distribution patterns
    if "Low" in preset:
        # Off-peak: minimal demand, negligible search latency
        occupancies = [65, 120, 10]
        avg_wait = "0 mins"
    elif "Moderate" in preset:
        # Midday: classes rotating; steady turnover keeps queues manageable
        occupancies = [210, 380, 45]
        avg_wait = "4.5 mins"
    elif "Critical" in preset:
        # Special event: campus-wide saturation forcing reliance on peripheral lots
        occupancies = [298, 545, 195]
        avg_wait = "18.2 mins"
    else:
        # Morning Rush: commuter surge heavily favors North Lot due to academic building proximity
        occupancies = [285, 410, 30]
        avg_wait = "9.8 mins"

    df = pd.DataFrame(lots)
    df["occupied"] = occupancies
    df["pct_full"] = (df["occupied"] / df["capacity"]) * 100

    # Simulate computer vision confidence loss: precipitation and fog cause lens flare,
    # occlusion, and glare that lower spot-detection certainty.
    if weather_mode == "Clear":
        confidence = 98.5
    elif "Rain" in weather_mode:
        confidence = 82.1
    else:  # Fog
        confidence = 74.0

    df["sensor_confidence"] = confidence
    return df, avg_wait


lot_data, wait_time = get_simulated_lot_data(scenario, weather)


# -----------------------------------------------------------------------------
# 4. Main Executive Telemetry View
# -----------------------------------------------------------------------------
st.title("🚗 Smart Campus Parking & Navigation Dashboard")
st.caption(
    f"Active Scenario: **{scenario}** | Edge Vision Confidence: **{lot_data['sensor_confidence'].iloc[0]}%**"
)

# High-level KPIs to immediately communicate system health during presentations
m1, m2, m3, m4 = st.columns(4)
total_capacity = lot_data["capacity"].sum()
total_occupied = lot_data["occupied"].sum()
system_pct = (total_occupied / total_capacity) * 100

m1.metric(
    label="Campus-Wide Occupancy",
    value=f"{total_occupied} / {total_capacity}",
    delta=f"{system_pct:.1f}% Saturation",
)

# Demonstrates the tangible ROI of the routing algorithm on search latency
m2.metric(
    label="Avg. Time-to-Park",
    value=wait_time,
    delta="-3.2 min with AI" if ai_reroute_enabled else "+4.5 min delay",
    delta_color="normal" if ai_reroute_enabled else "inverse",
)

m3.metric(
    label="Rerouted Vehicles (In-Transit)",
    value="42 Cars" if ai_reroute_enabled else "0 (Reroute Disabled)",
    delta="Load balanced" if ai_reroute_enabled else "Queuing at gates",
    delta_color="normal" if ai_reroute_enabled else "off",
)

m4.metric(
    label="Active Carpools Matched",
    value="18 Groups" if "Rush" in scenario or "Critical" in scenario else "4 Groups",
    delta="36 Single-occupant trips removed",
)

st.divider()

# -----------------------------------------------------------------------------
# 5. Spatial Map & Facility Breakdown
# -----------------------------------------------------------------------------
col_map, col_details = st.columns([2, 1])

with col_map:
    st.subheader("Live Campus Facility Map")
    # Native Streamlit map rendering lot coordinates scaled by current vehicle count
    st.map(lot_data, latitude="lat", longitude="lon", size="occupied", zoom=14)

with col_details:
    st.subheader("Facility Saturation Levels")
    for _, row in lot_data.iterrows():
        pct = row["pct_full"]
        st.write(f"**{row['name']}**")

        # Color & warning tiering based on operational thresholds
        if pct >= 90.0:
            st.progress(
                pct / 100,
                text=f"🚨 {row['occupied']}/{row['capacity']} ({pct:.0f}%) - SATURATED",
            )
            if ai_reroute_enabled:
                st.info(
                    "⚡ *Automated Reroute Active:* Diverting incoming arrivals to East Overflow."
                )
        elif pct >= 75.0:
            st.progress(
                pct / 100,
                text=f"⚠️ {row['occupied']}/{row['capacity']} ({pct:.0f}%) - HIGH CONGESTION",
            )
        else:
            st.progress(
                pct / 100,
                text=f"✅ {row['occupied']}/{row['capacity']} ({pct:.0f}%) - SPOTS AVAILABLE",
            )

st.divider()

# -----------------------------------------------------------------------------
# 6. Simulated Mobile Client Experience (Student Perspective)
# -----------------------------------------------------------------------------
st.subheader("📱 End-User Mobile View (In-Transit Driver)")
driver_col1, driver_col2 = st.columns([1, 2])

with driver_col1:
    target_lot = "North Commuter Lot"
    # Check if North Lot is saturated in current state
    lot_a_is_saturated = (
        lot_data.loc[lot_data["id"] == "LOT-A", "pct_full"].values[0] >= 90.0
    )

    # Illustrates the Human-in-the-Loop Walk stage:
    # Instead of forcing an unexpected detour, the app transparently recommends
    # an alternate destination before the driver reaches congested gates.
    if lot_a_is_saturated and ai_reroute_enabled:
        st.error(f"⚠️ Destination '{target_lot}' reached capacity (95% full)!")
        st.success(
            "🤖 AI Reroute Recommendation: Divert to East Peripheral Overflow (15% full). Added walk time: +2 mins."
        )
    elif lot_a_is_saturated and not ai_reroute_enabled:
        st.error(
            f"⚠️ Destination '{target_lot}' is full. Anticipate significant gate queuing."
        )
    else:
        st.success(f"Clear route: Proceeding to {target_lot}. Open spaces verified.")

with driver_col2:
    with st.expander("Connected Carpool Pairing Details", expanded=True):
        st.caption(
            "Matches computed via DBSCAN spatial clustering on student home coordinates and class arrival schedules."
        )
        st.table(
            pd.DataFrame({
                "Driver": ["Matthew R.", "Alex C."],
                "Pickup Hub": ["West Commuter Zone", "Campus North Apts"],
                "Matched Riders": [2, 3],
                "Route Alignment Score": ["94%", "88%"],
            })
        )
