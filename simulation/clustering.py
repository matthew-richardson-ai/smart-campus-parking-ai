"""
Commuter Rideshare Spatial Clustering Module

This module implements density-based spatial clustering (DBSCAN) using the Haversine
metric to group student commuters by geographic proximity. It identifies high-density
pickup pockets to minimize detour distance for driver vehicles.
"""

import os
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN


def match_commuter_rideshares(
    student_coords: np.ndarray, max_pickup_radius_km: float = 1.5
) -> dict:
    """
    Groups student commuters into shared carpools based on real-world spherical distance.

    Why DBSCAN over K-Means?
    ------------------------
    1. K-Means forces every commuter into a cluster, even isolated rural students who
       would create excessive detours for drivers. DBSCAN labels those points as noise (-1).
    2. DBSCAN does not require an arbitrary pre-selected 'k' number of carpools; it forms
       clusters purely based on spatial commuter density.

    Parameters:
    -----------
    student_coords : np.ndarray
        Array of shape (N, 2) containing [latitude, longitude] in decimal degrees.
    max_pickup_radius_km : float
        Maximum allowable detour radius (in kilometers) between matched commuter pickup points.

    Returns:
    --------
    dict
        Mapping of {cluster_id: [student_indices]} containing only valid groupings (minimum 2 commuters).
    """
    EARTH_RADIUS_KM = 6371.0088
    epsilon_radians = max_pickup_radius_km / EARTH_RADIUS_KM
    coords_in_radians = np.radians(student_coords)

    clustering_model = DBSCAN(
        eps=epsilon_radians, min_samples=2, metric="haversine"
    ).fit(coords_in_radians)

    matches = {}
    for student_idx, cluster_id in enumerate(clustering_model.labels_):
        if cluster_id != -1:
            matches.setdefault(cluster_id, []).append(student_idx)

    return matches


def match_commuters_by_timetable(
    csv_path: str, target_time: str = "08:30", max_radius_km: float = 1.2
) -> pd.DataFrame:
    """
    Filters synthetic commuters targeting the same arrival window and applies spatial clustering.
    Maps the resulting cluster labels back to the DataFrame for easy analysis.
    """
    df = pd.read_csv(csv_path)

    # Isolate only the students arriving at the target time
    cohort = df[df["target_arrival_time"] == target_time].copy()

    if cohort.empty:
        return cohort

    # Extract coordinates for the clustering algorithm
    coords = cohort[["home_lat", "home_lon"]].to_numpy()

    # Run DBSCAN directly to retrieve labels for the DataFrame
    EARTH_RADIUS_KM = 6371.0088
    eps_rad = max_radius_km / EARTH_RADIUS_KM
    clustering = DBSCAN(eps=eps_rad, min_samples=2, metric="haversine").fit(
        np.radians(coords)
    )

    # -1 indicates noise/isolated commuters; integers represent valid carpool groups
    cohort["carpool_group"] = clustering.labels_

    return cohort


if __name__ == "__main__":
    data_file = "simulation/data/commuter_schedules.csv"

    if os.path.exists(data_file):
        print(f"Loading synthetic dataset from {data_file}...")
        results = match_commuters_by_timetable(
            data_file, target_time="08:30", max_radius_km=1.2
        )

        valid_groups = results[results["carpool_group"] != -1]
        noise_count = (results["carpool_group"] == -1).sum()

        print(f"\nTotal students arriving at 08:30: {len(results)}")
        print(
            f"Students successfully grouped: {len(valid_groups)} across {valid_groups['carpool_group'].nunique()} carpools"
        )
        print(f"Commuters isolated/unmatched (noise): {noise_count}")

        if not valid_groups.empty:
            print("\nSample Carpool Group 0:")
            print(
                valid_groups[valid_groups["carpool_group"] == 0][
                    ["student_id", "has_car", "seats_available", "home_lat", "home_lon"]
                ]
            )
    else:
        print(f"Dataset {data_file} not found.")
        print(
            "Please run 'python simulation/generate_commuters.py' to generate the data."
        )
