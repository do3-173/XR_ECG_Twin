"""
ActivationTime computation module.
Translates compute_ActivationTime_01.m MATLAB code to Python.

This module generates a temporal activation map of the heart divided into 8 anatomical districts,
based on ECG temporal landmarks. Each district is coded over time with discrete values representing
states: inactive, trigger, depolarization, or repolarization.
"""
import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ECGEvents:
    """ECG landmark events in milliseconds."""
    p_onset: float
    p_peak: float
    p_offset: float
    qrs_onset: float
    r_peak: float
    qrs_offset: float
    t_onset: float
    t_offset: float


class ActivationTimeComputer:
    """
    Computes temporal activation map for 8 cardiac districts.
    
    Districts:
    1. SA Node
    2. Right Atrium
    3. Left Atrium
    4. AV Node
    5. His bundle
    6. Bundle branches
    7. Apex
    8. Purkinje fibers
    
    States:
    0: inactive
    1: trigger (start of action potential)
    2: depolarization
    3: repolarization
    """

    def __init__(self, t_ms: np.ndarray, ecg_events: ECGEvents):
        """
        Initialize with time vector and ECG events.
        
        Args:
            t_ms: Time vector in milliseconds (1D array)
            ecg_events: ECGEvents dataclass with landmark times
        """
        self.t_ms = t_ms
        self.n_time = len(t_ms)
        self.ecg_events = ecg_events
        self.activation_time = np.zeros((8, self.n_time), dtype=np.uint8)

    def compute(self, display_figure: bool = False, signal: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Compute activation time matrix.
        
        Args:
            display_figure: Whether to display visualization
            signal: Optional ECG signal for visualization
            
        Returns:
            Matrix (8 × nTime) with activation states
        """
        events = self.ecg_events
        t_ms = self.t_ms

        # Cardiac cycle description:
        # - SA node fires
        # - P wave: electrical activity propagates in atria, contraction
        # - PQ segment: propagation delay at AV node (isoelectric)
        # - AV node fires
        # - QRS: ventricular depolarization, contraction, systole
        # - His bundle → bundle branches → apex → Purkinje fibers
        # - ST segment: isoelectric (plateau of action potential)
        # - T wave: ventricular repolarization
        # - T to P: isoelectric, diastole

        # Region 1: SA Node - Trigger
        nodo_sa_tf = (t_ms >= events.p_onset - 10) & (t_ms < events.p_onset)
        self.activation_time[0, nodo_sa_tf] = 1

        # Region 2: Right Atrium
        atrio_destro_dep_tf = (t_ms >= events.p_onset) & (t_ms < events.qrs_onset)
        atrio_destro_rip_tf = (t_ms >= events.qrs_onset) & (t_ms < events.r_peak)
        self.activation_time[1, atrio_destro_dep_tf] = 2  # depolarization
        self.activation_time[1, atrio_destro_rip_tf] = 3  # repolarization

        # Region 3: Left Atrium
        atrio_sinistro_dep_tf = (t_ms >= events.p_peak) & (t_ms < events.qrs_onset)
        atrio_sinistro_rip_tf = (t_ms >= events.qrs_onset) & (t_ms < events.r_peak)
        self.activation_time[2, atrio_sinistro_dep_tf] = 2  # depolarization
        self.activation_time[2, atrio_sinistro_rip_tf] = 3  # repolarization

        # Region 4: AV Node - Trigger
        nodo_av_tf = (t_ms >= events.qrs_onset - 10) & (t_ms < events.qrs_onset)
        self.activation_time[3, nodo_av_tf] = 1

        # Region 5: His Bundle
        his_bundle_dep_tf = (t_ms >= events.qrs_onset) & (t_ms < events.t_onset)
        his_bundle_rip_tf = (t_ms >= events.t_onset) & (t_ms < events.t_offset)
        self.activation_time[4, his_bundle_dep_tf] = 2  # depolarization
        self.activation_time[4, his_bundle_rip_tf] = 3  # repolarization

        # Region 6: Bundle Branches
        bundle_branches_dep_tf = (t_ms >= events.qrs_onset + 20) & (t_ms < events.t_onset)
        bundle_branches_rip_tf = (t_ms >= events.t_onset) & (t_ms < events.t_offset)
        self.activation_time[5, bundle_branches_dep_tf] = 2  # depolarization
        self.activation_time[5, bundle_branches_rip_tf] = 3  # repolarization

        # Region 7: Apex
        apex_dep_tf = (t_ms >= events.qrs_onset + 40) & (t_ms < events.t_onset)
        apex_rip_tf = (t_ms >= events.t_onset) & (t_ms < events.t_offset)
        self.activation_time[6, apex_dep_tf] = 2  # depolarization
        self.activation_time[6, apex_rip_tf] = 3  # repolarization

        # Region 8: Purkinje Fibers
        purkinje_dep_tf = (t_ms >= events.r_peak) & (t_ms < events.t_onset)
        purkinje_rip_tf = (t_ms >= events.t_onset) & (t_ms < events.t_offset)
        self.activation_time[7, purkinje_dep_tf] = 2  # depolarization
        self.activation_time[7, purkinje_rip_tf] = 3  # repolarization

        return self.activation_time

    def get_activation_time_binary(self) -> np.ndarray:
        """
        Get binary version where any activation is marked as 1.
        
        Returns:
            Binary matrix (8 × nTime)
        """
        return (self.activation_time != 0).astype(np.uint8)

    def get_state_at_time(self, time_ms: float) -> np.ndarray:
        """
        Get activation state of all regions at a specific time.
        
        Args:
            time_ms: Time in milliseconds
            
        Returns:
            Array of 8 states (one per region)
        """
        idx = np.argmin(np.abs(self.t_ms - time_ms))
        return self.activation_time[:, idx]

    def get_region_timeline(self, region_idx: int) -> np.ndarray:
        """
        Get activation timeline for a specific region.
        
        Args:
            region_idx: Region index (0-7)
            
        Returns:
            1D array of activation states over time
        """
        return self.activation_time[region_idx, :]

    @staticmethod
    def get_region_name(region_idx: int) -> str:
        """Get anatomical name for region index."""
        region_names = [
            "SA Node",
            "Right Atrium",
            "Left Atrium",
            "AV Node",
            "His Bundle",
            "Bundle Branches",
            "Apex",
            "Purkinje Fibers"
        ]
        return region_names[region_idx] if 0 <= region_idx < 8 else "Unknown"

    @staticmethod
    def get_state_name(state: int) -> str:
        """Get name for activation state."""
        state_names = {
            0: "Inactive",
            1: "Trigger",
            2: "Depolarization",
            3: "Repolarization"
        }
        return state_names.get(state, "Unknown")
