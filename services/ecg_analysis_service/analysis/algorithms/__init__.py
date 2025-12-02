"""
ECG Analysis Algorithms Package

Translated MATLAB algorithms to Python:
- signal_autocorr: Signal autocorrelation analysis
- wavelet_features: Wavelet-based multi-scale features (MODWT approximation)
- graph_features: Graph-theoretic features from correlation matrix
"""

from .signal_autocorr import (
    compute_signal_autocorr,
    extract_autocorr_features,
    compute_full_autocorr_analysis
)

from .wavelet_features import (
    compute_modwt_decomposition,
    compute_modwtxcorr_sequences,
    compute_elementary_corr,
    extract_wavelet_features,
    compute_full_wavelet_analysis
)

from .graph_features import (
    construct_adjacency_matrix,
    extract_graph_features,
    compute_full_graph_analysis
)

__all__ = [
    # Autocorrelation
    'compute_signal_autocorr',
    'extract_autocorr_features',
    'compute_full_autocorr_analysis',
    # Wavelet
    'compute_modwt_decomposition',
    'compute_modwtxcorr_sequences',
    'compute_elementary_corr',
    'extract_wavelet_features',
    'compute_full_wavelet_analysis',
    # Graph
    'construct_adjacency_matrix',
    'extract_graph_features',
    'compute_full_graph_analysis',
]
