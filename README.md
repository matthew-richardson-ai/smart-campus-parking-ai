# Smart Campus Parking & Rideshare Optimization Engine

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://eaglepark.streamlit.app/)

An AI-powered transit management solution engineered to alleviate university vehicle congestion, reduce parking discovery latency, and automate student carpooling without constructing new physical infrastructure.

---

## Project Overview
University campus parking lots face severe morning bottlenecks, resulting in 15–30 minutes of search latency per commuter, roadway gridlock, and unnecessary emissions. Because building new parking garages requires prohibitive capital expenditure and physical space, this platform applies dynamic software optimization to existing campus resources.

### Key Capabilities
* **Institutional Permit & Tuition Sync:** Prototype `T-Number` identity verification reflecting Tennessee Tech parking rules—auto-granting **Purple (Student - Tuition Covered)** access and distinguishing **Gold (Faculty/Staff)** permits to prevent lot mismatch citations.
* **Asphalt-Calibrated Curb-Cut Navigation:** Pinned directly to verified asphalt entry points (e.g., Stadium Dr for Volpe Library Lot) rather than generic building centroids.
* **One-Tap Mobile GPS Deep-Linking:** Hands off destination coordinates directly to native mobile turn-by-turn navigation (Google Maps / Apple Maps).
* **Aerial Satellite Visualization:** Renders high-resolution satellite imagery via Pydeck `TileLayer` (Esri World Imagery) without requiring proprietary API tokens.
* **Dynamic In-Transit Navigation:** Automatically calculates and dispatches reroute advisories to peripheral overflow facilities before primary lots hit 90% saturation.
* **Commuter Rideshare Clustering:** Groups student commuters based on geographic proximity and class schedule alignment using spatial density clustering (DBSCAN).

---

## Architecture & Lab Alignment
* **AI Strategy:** Partial Automation with Human-in-the-Loop verification (Crawl $\rightarrow$ Walk maturity model).
* **Core Model Interfaces:**
  * Spatial Clustering: Density-Based Spatial Clustering of Applications with Noise (DBSCAN)
  * Turnover Modeling: Predictive saturation modeling correlated with class schedules and rush presets
* **Mapping Engine:** Pydeck raster `TileLayer` over Esri World Imagery combined with Overpass API campus building centroids.
* **Simulation Sandbox:** Multi-state dynamic prototype built with Streamlit.

---

## Calibrated Campus Facilities

| Facility | Permit Tier | Capacity | Calibrated Entry Coordinate | Walk Distance |
| :--- | :--- | :--- | :--- | :--- |
| **Volpe Library North Lot** | Purple | 340 stalls | `36.17755, -85.50550` (Stadium Dr) | ~1.0 min |
| **Hooper Eblen Center Lot** | Purple | 580 stalls | `36.17750, -85.50930` (Willow Ave) | ~5.0 mins |
| **Peachtree Commuter Lot** | Purple | 220 stalls | `36.17360, -85.50390` (Peachtree Ave) | ~4.5 mins |
| **Ashburn Drive Lot** | Gold | 175 stalls | `36.17630, -85.50150` (Ashburn Dr) | ~2.5 mins |
| **Bell Hall / 10th St Lot** | Purple | 140 stalls | `36.17515, -85.50790` (W 10th St) | ~6.0 mins |
| **Tech Village Overflow Lot** | Purple | 320 stalls | `36.18240, -85.51160` (W 12th St) | ~8.0 mins |

---

## Getting Started

### Prerequisites
* Python 3.10+
* Git

### Installation & Local Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/matthew-richardson-ai/smart-campus-parking-ai.git](https://github.com/matthew-richardson-ai/smart-campus-parking-ai.git)
   cd smart-campus-parking-ai