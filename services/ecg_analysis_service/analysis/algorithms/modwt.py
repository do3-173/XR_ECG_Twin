"""
Maximal Overlap Discrete Wavelet Transform (MODWT)
Pure Python implementation matching MATLAB's modwt() function exactly.
Uses FFT-based algorithm like MATLAB.
"""

import numpy as np
import pywt


def modwt(x, wavelet, level):
    '''
    Maximal Overlap Discrete Wavelet Transform
    
    This implementation matches MATLAB's modwt() function exactly by using
    FFT-based convolution with upsampled filters in the frequency domain.
    
    Parameters:
    -----------
    x : np.ndarray
        Input signal (1D array)
    wavelet : str
        Wavelet name ('sym4', 'db4', 'haar', etc.)
    level : int
        Decomposition level
        
    Returns:
    --------
    wavecoeff : np.ndarray
        Array of wavelet coefficients, shape (level+1, N)
        First 'level' rows are detail coefficients (W1, W2, ..., WJ)
        Last row is approximation coefficient (VJ)
    '''
    
    # Get wavelet filters
    wavelet_obj = pywt.Wavelet(wavelet)
    # MATLAB's modwt uses synthesis filters (reconstruction filters)
    # where the roles are reversed compared to decomposition
    # PyWavelets: rec_lo and rec_hi are synthesis filters
    Lo = np.array(wavelet_obj.rec_lo)  # Synthesis low-pass (for approximation in MODWT)
    Hi = np.array(wavelet_obj.rec_hi)  # Synthesis high-pass (for detail in MODWT)  
    
    # Scale the filters for MODWT (divide by sqrt(2))
    Lo = Lo / np.sqrt(2.0)
    Hi = Hi / np.sqrt(2.0)
    
    # Ensure column vectors
    Lo = Lo.flatten()
    Hi = Hi.flatten()
    
    N = len(x)
    x = x.astype(np.float64)
    
    # If signal length < filter length, periodize the signal
    Nrep = N
    if N < len(Lo):
        num_reps = int(np.ceil(len(Lo) / N))
        x = np.tile(x, num_reps + 1)[:num_reps * N]
        Nrep = len(x)
    
    # Compute FFT of filters (zero-padded to signal length)
    G = np.fft.fft(Lo, Nrep)  # Scaling filter in frequency domain
    H = np.fft.fft(Hi, Nrep)  # Wavelet filter in frequency domain
    
    # Allocate output
    w = np.zeros((level + 1, Nrep), dtype=np.float64)
    
    # Compute FFT of signal
    V_fft = np.fft.fft(x)
    
    # Main MODWT algorithm - iterate through levels
    for j in range(1, level + 1):
        # Upsample factor for this level
        upfactor = 2 ** (j - 1)
        
        # Upsample filters in frequency domain by circular indexing
        # This is the key insight from MATLAB's implementation!
        indices = (upfactor * np.arange(Nrep)) % Nrep
        G_up = G[indices]
        H_up = H[indices]
        
        # Convolve in frequency domain (element-wise multiplication)
        W_fft = H_up * V_fft  # Detail coefficients
        V_fft = G_up * V_fft  # Approximation coefficients (input to next level)
        
        # Transform back to time domain
        w[j-1, :] = np.fft.ifft(W_fft).real
    
    # Final approximation
    w[level, :] = np.fft.ifft(V_fft).real
    
    # Truncate to original signal length if needed
    if Nrep > N:
        w = w[:, :N]
    
    return w


def imodwt(w, wavelet):
    ''' 
    Inverse MODWT
    
    Parameters:
    -----------
    w : np.ndarray
        Wavelet coefficients from modwt, shape (level+1, N)
    wavelet : str
        Wavelet name
        
    Returns:
    --------
    reconstructed : np.ndarray
        Reconstructed signal
    '''
    # Get wavelet filters
    wavelet_obj = pywt.Wavelet(wavelet)
    h = np.array(wavelet_obj.dec_hi)
    g = np.array(wavelet_obj.dec_lo)
    
    # Normalize for MODWT
    h_t = h / np.sqrt(2.0)
    g_t = g / np.sqrt(2.0)
    
    L = len(h_t)
    level = w.shape[0] - 1
    N = w.shape[1]
    
    # Start with final approximation
    V_j = w[-1].copy()
    
    # Reconstruct from coarsest to finest
    for j in range(level, 0, -1):
        W_j = w[j-1]
        V_j_new = np.zeros(N, dtype=np.float64)
        
        shift = 2 ** (j - 1)
        
        # Inverse transform
        for t in range(N):
            for n in range(L):
                idx = (t + n * shift) % N
                V_j_new[t] += h_t[n] * W_j[idx] + g_t[n] * V_j[idx]
        
        V_j = V_j_new
    
    return V_j


def modwtmra(w, wavelet):
    ''' 
    Multiresolution analysis based on MODWT
    
    Parameters:
    -----------
    w : np.ndarray
        Wavelet coefficients from modwt
    wavelet : str
        Wavelet name
        
    Returns:
    --------
    mra : np.ndarray
        Multiresolution analysis components
    '''
    # For now, return the coefficients as-is
    # Full MRA implementation would reconstruct each level separately
    return w
