"""
Synthetic Commuter Schedule & Geolocation Generator

Generates realistic student commuter profiles around campus to test
DBSCAN rideshare clustering, arrival timing, and parking demand.
"""

import pandas as pd
import numpy as np
import os


def generate_commuter_dataset(
    n_commuters: int = 150, random_seed: int = 42
) -> pd.DataFrame:
    """
    Generates synthetic commuter coordinates, timetable slots, and vehicle roles.

    Coordinates are distributed across realistic residential hubs around Cookeville:
    - On-campus / Perimeter Apartments
    - Downtown & West Cookeville
    - South Interstate corridor
    - Scattered rural/suburban commuters (noise points for DBSCAN)
    """
    np.random.seed(random_seed)

    # Campus anchor coordinates (Cookeville, TN)
    campus_lat, campus_lon = 36.1775, -85.5030

    commuters = []

    # Cluster distributions: (center_lat, center_lon, std_dev_km, proportion)
    hubs = [
        (36.1650, -85.5080, 0.4, 0.40),  # West student apartment corridor
        (36.1520, -85.4980, 0.5, 0.30),  # South Jefferson / Commercial corridor
        (36.1850, -85.4850, 0.6, 0.20),  # East residential neighborhoods
        (
            36.2100,
            -85.4500,
            2.5,
            0.10,
        ),  # Outlying rural commuters (expected noise points)
    ]

    # Conversion approximation: 1 deg lat ~ 111 km, 1 deg lon ~ 89 km at 36 deg N
    KM_TO_LAT = 1 / 110.574
    KM_TO_LON = 1 / (111.320 * np.cos(np.radians(campus_lat)))

    commuter_id = 1
    for center_lat, center_lon, std_dev_km, proportion in hubs:
        count = int(n_commuters * proportion)
        lats = np.random.normal(center_lat, std_dev_km * KM_TO_LAT, count)
        lons = np.random.normal(center_lon, std_dev_km * KM_TO_LON, count)

        for lat, lon in zip(lats, lons):
            commuters.append({
                "student_id": f"STU-{commuter_id:04d}",
                "home_lat": round(lat, 6),
                "home_lon": round(lon, 6),
                "target_arrival_time": np.random.choice(
                    ["07:45", "08:30", "09:30", "10:30"], p=[0.15, 0.45, 0.25, 0.15]
                ),
                "class_dismissal_time": np.random.choice(
                    ["11:15", "12:45", "14:15", "16:00"], p=[0.20, 0.35, 0.30, 0.15]
                ),
                "has_car": np.random.choice([True, False], p=[0.60, 0.40]),
                "seats_available": 0,
            })
            commuter_id += 1

    df = pd.DataFrame(commuters)

    # Drivers allocate 2 to 3 available seats for carpooling
    df.loc[df["has_car"] == True, "seats_available"] = np.random.choice(
        [2, 3], size=(df["has_car"] == True).sum(), p=[0.7, 0.3]
    )

    return df


if __name__ == "__main__":
    os.makedirs("simulation/data", exist_ok=True)
    dataset = generate_commuter_dataset()
    output_path = "simulation/data/commuter_schedules.csv"
    dataset.to_csv(output_path, index=False)
    print(f"Generated {len(dataset)} synthetic commuter schedules at {output_path}.")
    print(dataset.head())
