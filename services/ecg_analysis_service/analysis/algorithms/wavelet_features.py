"""
Wavelet Cross-Correlation Features
Translated from MATLAB: computeFeat_modwtxcorr03.m

Extracts multi-scale features using Maximal Overlap Discrete Wavelet Transform (MODWT)
and computes cross-correlations between scales.
"""

import numpy as np
import pywt
from scipy import signal
from typing import Tuple, List, Optional, Dict

from .modwt import modwt, imodwt


def compute_modwt_decomposition(
    ecg_signal: np.ndarray,
    wavelet: str = 'sym4',
    level: Optional[int] = None,
    fs: float = 128.0
) -> Tuple[List[np.ndarray], List[np.ndarray]]:
    """
    Perform MODWT decomposition on ECG signal (matches MATLAB's modwt).
    
    Parameters:
    -----------
    ecg_signal : np.ndarray
        Input ECG signal (1D array)
    wavelet : str
        Wavelet family (default: 'sym4')
    level : int, optional
        Decomposition level (default: auto-detect, max 7)
    fs : float
        Sampling frequency in Hz
        
    Returns:
    --------
    coeffs_d : list of np.ndarray
        Detail coefficients [W1, W2, ..., WJ]
    coeffs_a : list of np.ndarray
        Approximation coefficients [V1, V2, ..., VJ]
    """
    
    # Input validation
    if not isinstance(ecg_signal, np.ndarray):
        ecg_signal = np.array(ecg_signal)
    
    if ecg_signal.ndim != 1:
        raise ValueError(f"ECG signal must be 1D array, got shape {ecg_signal.shape}")
    
    # Determine maximum decomposition level
    if level is None:
        # MODWT doesn't have the same restrictions as SWT
        # Match MATLAB's default behavior: limit to 6 levels for 640 samples at 128 Hz
        # This matches computeFeat_modwtxcorr03.m behavior
        level = 6
    
    # Perform MODWT decomposition
    try:
        wavecoeffs = modwt(ecg_signal, wavelet, level)
    except Exception as e:
        raise ValueError(f"MODWT decomposition failed: {str(e)}")
    
    # Extract detail and approximation coefficients
    # modwt returns array of shape (level+1, N)
    # First 'level' rows are detail coefficients (W1, W2, ..., WJ)
    # Last row is approximation coefficient (VJ)
    coeffs_d = [wavecoeffs[i] for i in range(level)]
    coeffs_a = [wavecoeffs[-1]]  # Only the final approximation
    
    return coeffs_d, coeffs_a


def compute_modwtxcorr_sequences(
    w1: np.ndarray,
    w2: np.ndarray,
    wavelet: str = 'sym4'
) -> List[np.ndarray]:
    """
    Compute MODWT cross-correlation sequences (matches MATLAB's modwtxcorr).
    
    This implements the algorithm from MATLAB's modwtxcorr_stf.m:
    1. For each level, compute cross-correlation using FFT
    2. Normalize by sqrt(SSX * SSY) where SSX, SSY are signal energies
    3. Return sequences from -(MJ-1) to (MJ-1) lags
    
    Reference: MATLAB modwtxcorr() - Wavelet cross-correlation sequence estimates using MODWT
    
    Parameters:
    -----------
    w1 : np.ndarray
        First MODWT transform (levels x samples)
    w2 : np.ndarray
        Second MODWT transform (levels x samples) - can be same as w1 for autocorrelation
    wavelet : str
        Wavelet name (used to compute boundary coefficients)
        
    Returns:
    --------
    xcseq : list of np.ndarray
        Cross-correlation sequences for each level
    """
    
    # Get filter length for boundary coefficient calculation
    wav = pywt.Wavelet(wavelet)
    L = len(wav.dec_lo)  # Filter length
    
    N = w1.shape[1]  # Number of samples
    J = w1.shape[0] - 1  # Number of detail levels (excluding approximation)
    
    # Compute Jmax - maximum level with nonboundary coefficients
    # MATLAB: Jmax = floor(log2((N-1)/(filtlen-1)+1))
    Jmax = int(np.floor(np.log2((N - 1) / (L - 1) + 1)))
    if Jmax < 1:
        raise ValueError("No nonboundary coefficients available")
    Jmax = min(Jmax, J)
    
    xcseq = []
    
    # Process each DETAIL level only (not approximation)
    # MATLAB's computeFeat_modwtxcorr03 only works with detail coefficients
    for j in range(Jmax):
        # Get coefficients for this level
        cfs1 = w1[j, :N]
        cfs2 = w2[j, :N]
        
        # Remove boundary coefficients
        # MATLAB: LJ(j) = (2^j - 1) * (L - 1)
        LJ = (2**((j+1)) - 1) * (L - 1)
        M = min(LJ, N)
        
        # Set boundary coefficients to NaN and remove
        cfs1_clean = cfs1[M:]  # Remove first M samples
        cfs2_clean = cfs2[M:]
        
        MJ = len(cfs1_clean)  # Number of nonboundary coefficients
        
        if MJ < 1:
            # No nonboundary coefficients at this level
            continue
        
        # Compute cross-correlation sequence (MATLAB's modwtCCS)
        # FFT-based cross-correlation
        fftpad = 2 ** int(np.ceil(np.log2(2 * MJ - 1)))
        zerolag = fftpad // 2
        idxbegin = zerolag - (MJ - 1)
        idxend = zerolag + MJ
        
        # Compute energies for normalization
        SSX = np.sum(np.abs(cfs1_clean) ** 2)
        SSY = np.sum(np.abs(cfs2_clean) ** 2)
        scalefactor = np.sqrt(SSX * SSY)
        
        if scalefactor < 1e-10:
            # Near-zero energy, return zeros
            xcseq.append(np.zeros(2 * MJ - 1))
            continue
        
        # Cross-correlation via FFT
        # MATLAB: wccsDFT = fft(cfs1,fftpad).*conj(fft(cfs2,fftpad))
        cfs1_fft = np.fft.fft(cfs1_clean, fftpad)
        cfs2_fft = np.fft.fft(cfs2_clean, fftpad)
        wccsDFT = cfs1_fft * np.conj(cfs2_fft)
        
        # MATLAB: wccs = ifftshift(ifft(wccsDFT))
        wccs = np.fft.ifft(wccsDFT)
        wccs = np.fft.ifftshift(wccs).real
        
        # Extract relevant lags: -(MJ-1) to (MJ-1)
        wccs = wccs[idxbegin:idxend]
        
        # Normalize
        wccs = wccs / scalefactor
        
        xcseq.append(wccs)
    
    # Do NOT include approximation coefficients
    # MATLAB's computeFeat_modwtxcorr03 only uses detail coefficients W1...WJ
    # The approximation VJ is NOT used in the graph construction
    
    return xcseq


def compute_elementary_corr(
    xcorr_seqs1: List[np.ndarray],
    xcorr_seqs2: List[np.ndarray]
) -> np.ndarray:
    """
    Compute correlation matrix between wavelet cross-correlation sequences.
    
    This directly matches MATLAB's computeFeat_adjmat01.m elementary_corr() function:
    1. For each pair of scales (w, y), interpolate seq2[y] to match length of seq1[w]
    2. Compute corrcoef(seq1[w], interpolated_seq2[y])
    3. Extract the (1,2) element from 2x2 correlation matrix
    4. Make matrix symmetric: A = (A + A') / 2
    5. Set diagonal to 0
    
    Parameters:
    -----------
    xcorr_seqs1 : list of np.ndarray
        Cross-correlation sequences for first signal (each element has different length)
    xcorr_seqs2 : list of np.ndarray
        Cross-correlation sequences for second signal
        
    Returns:
    --------
    A : np.ndarray
        Correlation matrix (nLevels x nLevels) with diagonal = 0
    """
    
    nLevels = len(xcorr_seqs1)
    A = np.zeros((nLevels, nLevels))
    
    for w in range(nLevels):
        for y in range(nLevels):
            xc_signal1_w = xcorr_seqs1[w]
            xc_signal2_y = xcorr_seqs2[y]
            
            # MATLAB: d2 = interp1(1:numel(xc_signal2{y}), xc_signal2{y}, 
            #                       linspace(1, numel(xc_signal2{y}), numel(xc_signal1{w})))
            # Interpolate signal2[y] to match length of signal1[w]
            len1 = len(xc_signal1_w)
            len2 = len(xc_signal2_y)
            
            if len1 == len2:
                # Same length, no interpolation needed
                d2 = xc_signal2_y
            else:
                # Interpolate: map indices 0..len2-1 to 0..len1-1
                old_indices = np.linspace(0, len2 - 1, len2)
                new_indices = np.linspace(0, len2 - 1, len1)
                d2 = np.interp(new_indices, old_indices, xc_signal2_y)
            
            # MATLAB: A_matrix = corrcoef(xc_signal1{w}, d2)
            # corrcoef returns 2x2 matrix: [[1, r], [r, 1]]
            # We want the correlation coefficient r = A_matrix(1,2)
            try:
                corr_matrix = np.corrcoef(xc_signal1_w, d2)
                A[w, y] = corr_matrix[0, 1]
            except:
                A[w, y] = 0.0
            
            # Handle NaN
            if np.isnan(A[w, y]):
                A[w, y] = 0.0
    
    # MATLAB: A = (A + A') / 2
    A = (A + A.T) / 2.0
    
    # MATLAB: A = A - diag(diag(A))
    # Set diagonal to 0 (no self-loops)
    np.fill_diagonal(A, 0.0)
    
    return A


def extract_wavelet_features(
    coeffs_d: List[np.ndarray],
    coeffs_a: List[np.ndarray],
    corr_matrix: np.ndarray,
    original_signal: Optional[np.ndarray] = None
) -> Dict:
    """
    Extract statistical features from wavelet decomposition.
    
    Features include:
    - Energy at each scale
    - Energy distribution (percentage at each scale)
    - Entropy of energy distribution
    - Correlation statistics between scales
    - Scale ratios
    
    Parameters:
    -----------
    coeffs_d : list of np.ndarray
        Detail coefficients
    coeffs_a : list of np.ndarray
        Approximation coefficients
    corr_matrix : np.ndarray
        Correlation matrix between wavelet scales
    original_signal : np.ndarray, optional
        Original signal for total energy calculation (MATLAB compatibility)
        
    Returns:
    --------
    features : dict
        Dictionary of extracted features
    """
    
    features = {}
    n_scales = len(coeffs_d)
    
    # Energy at each scale (sum of squared coefficients)
    energies = []
    for i, d in enumerate(coeffs_d):
        energy = np.sum(d ** 2)
        energies.append(float(energy))
        features[f'energy_D{i+1}'] = float(energy)
    
    # Total energy - use original signal if provided (MATLAB compatibility)
    if original_signal is not None:
        total_energy = np.sum(original_signal ** 2)
    else:
        total_energy = np.sum(energies)
    features['total_energy'] = float(total_energy)
    
    # Energy distribution (normalized)
    if total_energy > 1e-10:
        energy_dist = np.array(energies) / total_energy
        for i, e in enumerate(energy_dist):
            features[f'energy_dist_D{i+1}'] = float(e)
        
        # Entropy of energy distribution
        # Shannon entropy: H = -sum(p * log2(p))
        energy_dist_nonzero = energy_dist[energy_dist > 1e-10]
        if len(energy_dist_nonzero) > 0:
            entropy = -np.sum(energy_dist_nonzero * np.log2(energy_dist_nonzero))
            features['energy_entropy'] = float(entropy)
        else:
            features['energy_entropy'] = 0.0
    else:
        features['energy_entropy'] = 0.0
    
    # Correlation statistics between scales
    # Extract upper triangle (excluding diagonal which is 0)
    triu_indices = np.triu_indices(n_scales, k=1)
    corr_values = corr_matrix[triu_indices]
    
    if len(corr_values) > 0:
        features['corr_mean'] = float(np.mean(corr_values))
        features['corr_std'] = float(np.std(corr_values))
        features['corr_max'] = float(np.max(corr_values))
        features['corr_min'] = float(np.min(corr_values))
    else:
        features['corr_mean'] = 0.0
        features['corr_std'] = 0.0
        features['corr_max'] = 0.0
        features['corr_min'] = 0.0
    
    # Scale ratios (energy ratio between adjacent scales)
    scale_ratios = []
    for i in range(len(energies) - 1):
        if energies[i+1] > 1e-10:
            ratio = energies[i] / energies[i+1]
            scale_ratios.append(float(ratio))
            features[f'scale_ratio_D{i+1}_D{i+2}'] = float(ratio)
    
    return features


def compute_full_wavelet_analysis(
    ecg_signal: np.ndarray,
    wavelet: str = 'sym4',
    level: Optional[int] = None,
    fs: float = 128.0
) -> Dict:
    """
    Perform complete wavelet-based feature extraction (matches MATLAB exactly).
    
    MATLAB workflow from realtime_ecg_analyzer.m + computeFeat_modwtxcorr03.m:
    1. modwt() decomposition -> w1, w2 (same signal)
    2. modwtxcorr(w1, w2) -> rww (cross-correlation sequences for each scale)
    3. computeFeat_adjmat01(rww) -> correlation matrix A between scales
    4. Extract features from A
    
    Parameters:
    -----------
    ecg_signal : np.ndarray
        Input ECG signal
    wavelet : str
        Wavelet family name (default: 'sym4')
    level : int, optional
        Decomposition level (default: 6 to match MATLAB)
    fs : float
        Sampling frequency
        
    Returns:
    --------
    result : dict
        Dictionary containing:
        - 'wavelet': Wavelet name used
        - 'level': Decomposition level
        - 'corr_matrix': Correlation matrix between scales (as list)
        - 'features': Dictionary of extracted features
        - 'fs': Sampling frequency
        - 'n_samples': Number of samples
    """
    
    # Ensure signal is 1D
    if ecg_signal.ndim != 1:
        raise ValueError(f"ECG signal must be 1D, got shape {ecg_signal.shape}")
    
    # Default to 6 levels (matches MATLAB's behavior for 640 samples)
    if level is None:
        level = 6
    
    # Step 1: MODWT decomposition (MATLAB: w1 = modwt(signal, wname))
    from .modwt import modwt as modwt_transform
    w1 = modwt_transform(ecg_signal, wavelet, level)
    w2 = w1  # For autocorrelation, use same transform
    
    # w1 shape: (level+1, n_samples) where rows are [W1, W2, ..., WJ, VJ]
    
    # Step 2: Compute MODWT cross-correlation sequences (MATLAB: modwtxcorr(w1, w2))
    xcorr_seqs = compute_modwtxcorr_sequences(w1, w2, wavelet)
    
    # xcorr_seqs is a list of arrays, one per level (including approximation if Jmax=J)
    # Each array has length (2*MJ - 1) where MJ is number of nonboundary coefficients
    
    # Step 3: Compute correlation matrix (MATLAB: computeFeat_adjmat01)
    # This computes corrcoef between different scales' cross-correlation sequences
    corr_matrix = compute_elementary_corr(xcorr_seqs, xcorr_seqs)
    
    # corr_matrix is nLevels x nLevels with diagonal = 0
    
    # Step 4: Extract features
    # Use detail coefficients for energy features
    coeffs_d = [w1[i] for i in range(min(level, w1.shape[0] - 1))]
    coeffs_a = [w1[-1]] if w1.shape[0] > level else []
    
    features = extract_wavelet_features(
        coeffs_d, 
        coeffs_a, 
        corr_matrix,
        original_signal=ecg_signal
    )
    
    # Package results
    result = {
        'wavelet': wavelet,
        'level': len(xcorr_seqs),  # Number of levels in correlation matrix
        'xcorr_sequences': [seq.tolist() if isinstance(seq, np.ndarray) else seq for seq in xcorr_seqs],  # Cross-correlation sequences for each scale
        'coeffs_d': [coeff.tolist() if isinstance(coeff, np.ndarray) else coeff for coeff in coeffs_d],  # Detail coefficients for each scale
        'wavelet_name': wavelet,
        'corr_matrix': corr_matrix.tolist(),  # Convert to list for JSON
        'features': features,
        'fs': fs,
        'n_samples': len(ecg_signal)
    }
    
    return result
