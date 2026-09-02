"""
Commuter Rideshare Spatial Clustering Module

This module implements density-based spatial clustering (DBSCAN) using the Haversine
metric to group student commuters by geographic proximity. It identifies high-density
pickup pockets to minimize detour distance for driver vehicles.
"""

import numpy as np
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
    # Mean radius of Earth in kilometers (WGS-84 approximation)
    EARTH_RADIUS_KM = 6371.0088

    # Scikit-learn's Haversine metric requires distance threshold (epsilon) expressed in radians.
    # Formula: radians = arc_length (km) / sphere_radius (km)
    epsilon_radians = max_pickup_radius_km / EARTH_RADIUS_KM

    # Convert coordinates from degrees to radians as required by the Haversine metric
    coords_in_radians = np.radians(student_coords)

    # min_samples=2 enforces that at least two commuters must be nearby to constitute a valid rideshare
    clustering_model = DBSCAN(
        eps=epsilon_radians, min_samples=2, metric="haversine"
    ).fit(coords_in_radians)

    matches = {}
    for student_idx, cluster_id in enumerate(clustering_model.labels_):
        # A label of -1 indicates an outlier/noise point (no convenient carpool within radius)
        if cluster_id != -1:
            matches.setdefault(cluster_id, []).append(student_idx)

    return matches


if __name__ == "__main__":
    # Test coordinates representing student residences near the campus area
    # Index 0 and 1 are within walking distance of each other; Index 2 is an outlier.
    sample_commuter_coords = np.array([
        [36.1628, -85.5016],  # Student A (Apartment Complex 1)
        [36.1632, -85.5022],  # Student B (Neighboring Complex)
        [
            36.1850,
            -85.4500,
        ],  # Student C (Isolated Commuter, should be classified as noise)
    ])

    print("Running DBSCAN commuter clustering dry-run...")
    clusters = match_commuter_rideshares(
        sample_commuter_coords, max_pickup_radius_km=1.0
    )
    print(f"Identified Carpool Groups: {clusters}")

    # Verification: Student A (0) and Student B (1) should pair in Cluster 0; Student C (2) should be excluded.
    assert 0 in clusters, "Expected at least one valid cluster formed."
    assert set(clusters[0]) == {0, 1}, "Students 0 and 1 should be paired together."
    print(
        "Self-test passed: Outlier correctly excluded and nearby pair successfully grouped."
    )
