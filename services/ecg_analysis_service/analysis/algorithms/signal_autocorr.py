"""
Signal Autocorrelation Analysis
Translated from MATLAB: computeFeat_signalxcorr.m

Computes normalized autocorrelation function of ECG signal to identify
periodic patterns and self-similarity.
"""

import numpy as np
from scipy import signal
from typing import Tuple, Optional


def compute_signal_autocorr(
    ecg_signal: np.ndarray,
    fs: float = 128.0,
    normalize: bool = True,
    max_lag_seconds: Optional[float] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute autocorrelation of ECG signal.
    
    Mathematical Foundation:
    ----------------------
    R_xx[k] = E[x[n] * x[n+k]]  (Autocorrelation)
    
    Normalized: ρ_xx[k] = R_xx[k] / R_xx[0]
    
    Where:
    - x[n] is the input signal
    - k is the lag
    - R_xx[0] is the signal variance
    
    Parameters:
    -----------
    ecg_signal : np.ndarray
        Input ECG signal (1D array)
    fs : float
        Sampling frequency in Hz (default: 128 Hz)
    normalize : bool
        Whether to normalize by variance (default: True)
    max_lag_seconds : float, optional
        Maximum lag in seconds to compute (default: None = full signal)
        
    Returns:
    --------
    autocorr : np.ndarray
        Autocorrelation function values
    lags : np.ndarray
        Lag values in samples
        
    Example:
    --------
    >>> ecg_data = np.random.randn(1000)
    >>> autocorr, lags = compute_signal_autocorr(ecg_data, fs=128.0)
    >>> # autocorr[0] should be 1.0 if normalized
    """
    
    # Input validation
    if not isinstance(ecg_signal, np.ndarray):
        ecg_signal = np.array(ecg_signal)
    
    if ecg_signal.ndim != 1:
        raise ValueError(f"ECG signal must be 1D array, got shape {ecg_signal.shape}")
    
    n = len(ecg_signal)
    if n < 10:
        raise ValueError(f"ECG signal too short: {n} samples (minimum 10)")
    
    # Step 1: Remove mean (zero-center signal)
    signal_centered = ecg_signal - np.mean(ecg_signal)
    
    # Step 2: Compute autocorrelation using FFT method (O(N log N) complexity)
    # This is faster than direct method for signals > 100 samples
    autocorr_full = signal.correlate(
        signal_centered, 
        signal_centered, 
        mode='full',
        method='fft'
    )
    
    # Step 3: Take only positive lags (second half of correlation)
    # correlate returns lags from -(N-1) to (N-1)
    autocorr = autocorr_full[n-1:]  # Start from zero lag
    lags = np.arange(0, n)
    
    # Step 4: Limit to max_lag if specified
    if max_lag_seconds is not None:
        max_lag_samples = int(max_lag_seconds * fs)
        if max_lag_samples < n:
            autocorr = autocorr[:max_lag_samples + 1]
            lags = lags[:max_lag_samples + 1]
    
    # Step 5: Normalize by variance if requested
    if normalize:
        variance = autocorr[0]
        if variance > 1e-10:  # Avoid division by zero
            autocorr = autocorr / variance
        else:
            raise ValueError("Signal has near-zero variance, cannot normalize")
    
    return autocorr, lags


def extract_autocorr_features(
    autocorr: np.ndarray,
    lags: np.ndarray,
    fs: float = 128.0
) -> dict:
    """
    Extract statistical features from autocorrelation function.
    
    Features extracted:
    - First minimum location (cardiac period indicator)
    - Peak values and locations (excluding zero lag)
    - Decay rate (exponential fit)
    - Periodicity strength
    
    Parameters:
    -----------
    autocorr : np.ndarray
        Normalized autocorrelation values
    lags : np.ndarray
        Lag values in samples
    fs : float
        Sampling frequency in Hz
        
    Returns:
    --------
    features : dict
        Dictionary containing:
        - 'first_min_lag': Lag of first minimum (samples)
        - 'first_min_value': Value at first minimum
        - 'first_peak_lag': Lag of first peak after minimum
        - 'first_peak_value': Value at first peak
        - 'decay_rate': Exponential decay constant
        - 'periodicity_strength': Measure of periodicity (0-1)
    """
    
    features = {}
    
    # Find first minimum (skip first few samples to avoid noise)
    start_idx = int(0.2 * fs)  # Skip first 0.2 seconds
    if start_idx >= len(autocorr):
        start_idx = len(autocorr) // 4
    
    # Find local minima
    minima_indices = signal.argrelextrema(autocorr[start_idx:], np.less)[0]
    if len(minima_indices) > 0:
        first_min_idx = minima_indices[0] + start_idx
        features['first_min_lag'] = int(lags[first_min_idx])
        features['first_min_value'] = float(autocorr[first_min_idx])
    else:
        features['first_min_lag'] = None
        features['first_min_value'] = None
    
    # Find first peak after first minimum
    if features['first_min_lag'] is not None and first_min_idx < len(autocorr) - 1:
        maxima_indices = signal.argrelextrema(
            autocorr[first_min_idx:], 
            np.greater
        )[0]
        if len(maxima_indices) > 0:
            first_peak_idx = maxima_indices[0] + first_min_idx
            features['first_peak_lag'] = int(lags[first_peak_idx])
            features['first_peak_value'] = float(autocorr[first_peak_idx])
        else:
            features['first_peak_lag'] = None
            features['first_peak_value'] = None
    else:
        features['first_peak_lag'] = None
        features['first_peak_value'] = None
    
    # Estimate decay rate (fit exponential to envelope)
    # Use first 2 seconds of data
    decay_window = min(int(2 * fs), len(autocorr))
    if decay_window > 10:
        try:
            # Fit log(abs(autocorr)) ~ -decay_rate * lag
            valid_idx = autocorr[:decay_window] > 1e-10
            if np.sum(valid_idx) > 5:
                log_autocorr = np.log(np.abs(autocorr[:decay_window][valid_idx]))
                valid_lags = lags[:decay_window][valid_idx]
                
                # Linear regression
                coeffs = np.polyfit(valid_lags, log_autocorr, 1)
                features['decay_rate'] = float(-coeffs[0])  # Negative slope = decay
            else:
                features['decay_rate'] = None
        except:
            features['decay_rate'] = None
    else:
        features['decay_rate'] = None
    
    # Periodicity strength: ratio of first peak to first minimum
    if (features['first_peak_value'] is not None and 
        features['first_min_value'] is not None):
        periodicity = (features['first_peak_value'] - features['first_min_value']) / 2.0
        features['periodicity_strength'] = float(np.clip(periodicity, 0, 1))
    else:
        features['periodicity_strength'] = None
    
    return features


def compute_full_autocorr_analysis(
    ecg_signal: np.ndarray,
    fs: float = 128.0
) -> dict:
    """
    Perform complete autocorrelation analysis on ECG signal.
    
    Combines autocorrelation computation and feature extraction.
    
    Parameters:
    -----------
    ecg_signal : np.ndarray
        Input ECG signal
    fs : float
        Sampling frequency in Hz
        
    Returns:
    --------
    result : dict
        Dictionary containing:
        - 'autocorr': Normalized autocorrelation array
        - 'lags': Lag values array
        - 'features': Dictionary of extracted features
        - 'fs': Sampling frequency
        - 'n_samples': Number of samples in original signal
    """
    
    # Compute autocorrelation
    autocorr, lags = compute_signal_autocorr(
        ecg_signal,
        fs=fs,
        normalize=True,
        max_lag_seconds=5.0  # Limit to 5 seconds for efficiency
    )
    
    # Extract features
    features = extract_autocorr_features(autocorr, lags, fs)
    
    # Package results
    result = {
        'autocorr': autocorr.tolist(),  # Convert to list for JSON serialization
        'lags': lags.tolist(),
        'features': features,
        'fs': fs,
        'n_samples': len(ecg_signal)
    }
    
    return result
