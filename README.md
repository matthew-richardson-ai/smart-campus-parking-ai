# Smart Campus Parking & Rideshare Optimization Engine

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://smart-campus-parking-ai.streamlit.app/)

An AI-powered transit management solution engineered to alleviate university vehicle congestion, reduce parking discovery latency, and automate student carpooling without constructing new physical infrastructure.

---

## Project Overview
University campus parking lots face severe morning bottlenecks, resulting in 15–30 minutes of search latency per commuter, roadway gridlock, and unnecessary emissions. Because building new parking garages requires prohibitive capital expenditure and physical space, this platform applies dynamic software optimization to existing campus resources.

### Key Capabilities
* **Edge-Informed Lot Occupancy:** Ingests live perimeter camera data to monitor lot saturation in real time.
* **Predictive Turnover Forecasting:** Analyzes historical turnover rates correlated with class dismissal schedules to predict space availability.
* **Dynamic In-Transit Navigation:** Automatically calculates and dispatches reroute advisories to peripheral overflow facilities before primary lots hit 90% saturation.
* **Commuter Rideshare Clustering:** Groups student commuters based on geographic proximity and class schedule alignment using spatial density clustering (DBSCAN).

---

## Architecture & Lab Alignment
* **AI Strategy:** Partial Automation with Human-in-the-Loop verification (Crawl $\rightarrow$ Walk maturity model).
* **Core Model Interfaces:**
  * Spatial Clustering: Density-Based Spatial Clustering of Applications with Noise (DBSCAN)
  * Turnover Modeling: Regression forecasting trained on historical turnover & course schedule dismissal data
* **Simulation Sandbox:** Multi-state dynamic prototype built with Streamlit and Pydeck.

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