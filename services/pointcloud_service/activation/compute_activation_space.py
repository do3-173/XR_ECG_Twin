"""
ActivationSpace computation module.
Translates compute_ActivationSpace_01.m MATLAB code to Python.

This module identifies anatomical cardiac regions in a heart point cloud.
Segments a 3D point cloud into 8 anatomical regions relevant for action potential propagation.
"""
import numpy as np
from scipy.spatial import KDTree
from typing import Tuple, Optional


class ActivationSpaceComputer:
    """
    Computes the activation space for heart point cloud.
    Identifies 8 anatomical regions:
    1 → SA Node
    2 → Right Atrium
    3 → Left Atrium
    4 → AV Node
    5 → His bundle
    6 → Bundle branches
    7 → Purkinje fibers start (apex)
    8 → Purkinje fibers extension
    """

    def __init__(self, points: np.ndarray):
        """
        Initialize with point cloud data.
        
        Args:
            points: Nx3 numpy array of point cloud coordinates
        """
        self.points = points
        self.n_points = points.shape[0]
        self.activation_space = np.zeros((self.n_points, 8), dtype=np.uint8)
        self.kdtree = KDTree(points)

    def find_nearest_neighbors(self, center: np.ndarray, k: int) -> np.ndarray:
        """
        Find k nearest neighbors to a center point.
        
        Args:
            center: 3D coordinate [x, y, z]
            k: number of nearest neighbors
            
        Returns:
            indices of nearest neighbors
        """
        distances, indices = self.kdtree.query(center, k=k)
        return indices

    def find_neighbors_in_radius(self, center: np.ndarray, radius: float) -> np.ndarray:
        """
        Find all neighbors within a radius from center.
        
        Args:
            center: 3D coordinate [x, y, z]
            radius: search radius
            
        Returns:
            indices of points within radius
        """
        indices = self.kdtree.query_ball_point(center, radius)
        return np.array(indices)

    def find_points_in_oblique_cylinder(
        self, p1: np.ndarray, p2: np.ndarray, radius: float
    ) -> np.ndarray:
        """
        Find points inside an oblique cylinder defined by two endpoints and radius.
        
        Args:
            p1: Starting point [x, y, z]
            p2: Ending point [x, y, z]
            radius: Cylinder radius
            
        Returns:
            indices of points inside cylinder
        """
        # Direction vector of cylinder
        axis_vec = p2 - p1
        axis_len = np.linalg.norm(axis_vec)
        axis_dir = axis_vec / axis_len  # normalized

        # Vector from P1 to each point
        vec_to_points = self.points - p1

        # Scalar projection of each point onto axis
        t = np.dot(vec_to_points, axis_dir)

        # Orthogonal projection of point onto axis
        proj_points = p1 + t[:, np.newaxis] * axis_dir

        # Orthogonal distance from point to axis
        dist_orth = np.linalg.norm(self.points - proj_points, axis=1)

        # Criteria: within cylinder (length + radius)
        inside = (t >= 0) & (t <= axis_len) & (dist_orth <= radius)

        return np.where(inside)[0]

    def compute(self, display_figures: bool = False) -> np.ndarray:
        """
        Compute activation space for all 8 anatomical regions.
        
        Args:
            display_figures: Whether to display visualization figures
            
        Returns:
            Sparse matrix (nPoints × 8) with 1 for points in each region
        """
        # Region 1: SA Node
        # Junction between superior vena cava and right atrium
        c_nodo_sa = np.array([1.3, 5, -11.2])
        idx_nodo_sa = self.find_nearest_neighbors(c_nodo_sa, 10)
        self.activation_space[idx_nodo_sa, 0] = 1

        # Region 2: Right Atrium
        c_atrio_destro = np.array([1.3, 4.2, -11.2])
        r_atrio_destro = 1.0
        idx_atrio_destro = self.find_neighbors_in_radius(c_atrio_destro, r_atrio_destro)
        self.activation_space[idx_atrio_destro, 1] = 1

        # Region 3: Left Atrium
        c_atrio_sinistro = np.array([3, 4.5, -12])
        r_atrio_sinistro = 0.7
        idx_atrio_sinistro = self.find_neighbors_in_radius(c_atrio_sinistro, r_atrio_sinistro)
        self.activation_space[idx_atrio_sinistro, 2] = 1

        # Region 4: AV Node
        c_nodo_av = np.array([1.5, 3.8, -11.2])
        idx_nodo_av = self.find_nearest_neighbors(c_nodo_av, 10)
        self.activation_space[idx_nodo_av, 3] = 1

        # Region 5: His bundle
        # Region 6: Bundle branches
        c_start_purkinje = np.array([4.5, 1.0, -9])
        end_his_bundle = (c_nodo_av + c_start_purkinje) / 2
        start_bundle_branches = end_his_bundle
        end_bundle_branches = np.array([4, 1.7, -9])
        radius = 0.7

        idx_his_bundle = self.find_points_in_oblique_cylinder(
            c_nodo_av, end_his_bundle, radius
        )
        idx_bundle_branches = self.find_points_in_oblique_cylinder(
            start_bundle_branches, end_bundle_branches, radius
        )
        self.activation_space[idx_his_bundle, 4] = 1
        self.activation_space[idx_bundle_branches, 5] = 1

        # Region 7: Apex - Purkinje Fibers start
        c_start_purkinje = np.array([4.5, 1.0, -9])
        r_start_purkinje = 1.0
        idx_start_purkinje = self.find_neighbors_in_radius(c_start_purkinje, r_start_purkinje)
        self.activation_space[idx_start_purkinje, 6] = 1

        # Region 8: Purkinje lateral extension
        # Complex cone-based selection
        p1_purkinje_sx = np.array([3.3, 4.2, -13])
        p2_purkinje_sx = np.array([4.5, 1.0, -9])
        c_purkinje_sx = (p1_purkinje_sx + p2_purkinje_sx) / 2

        p1_purkinje_dx = np.array([1.5, 6, -8])
        p2_purkinje_dx = np.array([4.5, 1.0, -9])
        c_purkinje_dx = (p1_purkinje_dx + p2_purkinje_dx) / 2

        # Cone base parameters
        purkinje_cono_base_c = (c_purkinje_sx + c_purkinje_dx) / 2
        purkinje_cono_base_raggio = np.linalg.norm(c_purkinje_dx - purkinje_cono_base_c) / 2
        purkinje_cono_normal = purkinje_cono_base_c - p2_purkinje_sx
        purkinje_cono_normal = purkinje_cono_normal / np.linalg.norm(purkinje_cono_normal)

        max_height = 1.5

        # Vector from cone base center to all points
        v = self.points - c_start_purkinje
        # Projection along cone normal
        h = np.dot(v, purkinje_cono_normal)
        # Points on the cone axis
        axis_points = c_start_purkinje + h[:, np.newaxis] * purkinje_cono_normal
        # Theoretical radius at each height
        r = (h / max_height) * (2 * purkinje_cono_base_raggio)

        # Lateral distance from each point to axis
        lateral_distance = np.linalg.norm(self.points - axis_points, axis=1)

        # Selection criteria
        condition = (
            (np.abs(lateral_distance - r) <= 0.7) & 
            (self.points[:, 2] > -11.2)
        )
        idx_lateral_purkinje = np.where(condition)[0]
        self.activation_space[idx_lateral_purkinje, 7] = 1

        return self.activation_space

    def get_region_points(self, region_idx: int) -> np.ndarray:
        """
        Get points belonging to a specific region.
        
        Args:
            region_idx: Region index (0-7)
            
        Returns:
            Nx3 array of points in the region
        """
        mask = self.activation_space[:, region_idx] == 1
        return self.points[mask]
