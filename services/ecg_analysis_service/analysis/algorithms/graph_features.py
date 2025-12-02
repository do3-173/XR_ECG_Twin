"""
Graph Adjacency Matrix Features
Translated from MATLAB: computeFeat_adjmat01.m

Constructs graph from wavelet cross-correlation matrix and extracts
graph-theoretic features.
"""

import numpy as np
import networkx as nx
from typing import Dict, Optional, Tuple


def construct_adjacency_matrix(
    corr_matrix: np.ndarray,
    threshold_method: str = 'percentile',
    threshold_value: float = 75.0,
    absolute_threshold: Optional[float] = None
) -> np.ndarray:
    """
    Construct binary adjacency matrix from correlation matrix.
    
    Note: Input correlation matrix should already have diagonal = 0
    (as computed by MATLAB-style correlation computation).
    
    Thresholding methods:
    - 'percentile': Keep edges above percentile (e.g., 75th percentile)
    - 'absolute': Keep edges above absolute value
    - 'adaptive': Use mean + k*std as threshold
    
    Parameters:
    -----------
    corr_matrix : np.ndarray
        Correlation matrix (J×J) with diagonal = 0
    threshold_method : str
        Method for thresholding ('percentile', 'absolute', 'adaptive')
    threshold_value : float
        Value for thresholding (percentile or std multiplier)
    absolute_threshold : float, optional
        Absolute threshold value (overrides threshold_method if provided)
        
    Returns:
    --------
    adj_matrix : np.ndarray
        Binary adjacency matrix (0s and 1s)
    """
    
    # Get upper triangle values (excluding diagonal)
    n = corr_matrix.shape[0]
    triu_indices = np.triu_indices(n, k=1)
    corr_values = corr_matrix[triu_indices]
    
    # Determine threshold
    if absolute_threshold is not None:
        threshold = absolute_threshold
    elif threshold_method == 'percentile':
        threshold = np.percentile(np.abs(corr_values), threshold_value)
    elif threshold_method == 'absolute':
        threshold = threshold_value
    elif threshold_method == 'adaptive':
        # mean + k*std where k=threshold_value
        mean_val = np.mean(np.abs(corr_values))
        std_val = np.std(np.abs(corr_values))
        threshold = mean_val + threshold_value * std_val
    else:
        raise ValueError(f"Unknown threshold method: {threshold_method}")
    
    # Apply threshold
    adj_matrix = (np.abs(corr_matrix) >= threshold).astype(int)
    
    # Make sure diagonal is 0 (no self-loops)
    np.fill_diagonal(adj_matrix, 0)
    
    # Ensure symmetry
    adj_matrix = np.maximum(adj_matrix, adj_matrix.T)
    
    return adj_matrix


def extract_graph_features(
    adj_matrix: np.ndarray,
    weighted: bool = False,
    weight_matrix: Optional[np.ndarray] = None
) -> Dict:
    """
    Extract graph-theoretic features from adjacency matrix.
    
    Features include:
    - Number of nodes and edges
    - Graph density
    - Average degree
    - Clustering coefficient
    - Number of connected components
    - Diameter (if connected)
    - Centrality measures
    
    Parameters:
    -----------
    adj_matrix : np.ndarray
        Binary adjacency matrix
    weighted : bool
        Whether to use weighted edges
    weight_matrix : np.ndarray, optional
        Weight matrix (e.g., original xcorr values)
        
    Returns:
    --------
    features : dict
        Dictionary of graph features
    """
    
    features = {}
    
    # Create NetworkX graph
    if weighted and weight_matrix is not None:
        # Create weighted graph
        G = nx.from_numpy_array(weight_matrix * adj_matrix)
    else:
        # Create unweighted graph
        G = nx.from_numpy_array(adj_matrix)
    
    # Basic properties
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    
    features['n_nodes'] = n_nodes
    features['n_edges'] = n_edges
    
    # Density: ratio of actual edges to possible edges
    # density = 2*E / (N*(N-1)) for undirected graph
    if n_nodes > 1:
        density = nx.density(G)
        features['density'] = float(density)
    else:
        features['density'] = 0.0
    
    # Average degree
    if n_nodes > 0:
        degrees = dict(G.degree())
        avg_degree = np.mean(list(degrees.values()))
        features['avg_degree'] = float(avg_degree)
        features['max_degree'] = float(max(degrees.values()))
        features['min_degree'] = float(min(degrees.values()))
    else:
        features['avg_degree'] = 0.0
        features['max_degree'] = 0.0
        features['min_degree'] = 0.0
    
    # Clustering coefficient
    # Measures how much nodes tend to cluster together
    if n_nodes > 2:
        try:
            clustering = nx.average_clustering(G)
            features['avg_clustering'] = float(clustering)
        except:
            features['avg_clustering'] = 0.0
    else:
        features['avg_clustering'] = 0.0
    
    # Connected components
    n_components = nx.number_connected_components(G)
    features['n_components'] = n_components
    
    # Is connected?
    is_connected = (n_components == 1)
    features['is_connected'] = is_connected
    
    # Diameter and radius (only for connected graphs)
    if is_connected and n_nodes > 1:
        try:
            diameter = nx.diameter(G)
            radius = nx.radius(G)
            features['diameter'] = diameter
            features['radius'] = radius
        except:
            features['diameter'] = None
            features['radius'] = None
    else:
        features['diameter'] = None
        features['radius'] = None
    
    # Centrality measures (for connected graphs)
    if is_connected and n_nodes > 1 and n_edges > 0:
        try:
            # Degree centrality
            degree_centrality = nx.degree_centrality(G)
            features['max_degree_centrality'] = float(max(degree_centrality.values()))
            features['avg_degree_centrality'] = float(np.mean(list(degree_centrality.values())))
            
            # Betweenness centrality (can be expensive for large graphs)
            if n_nodes <= 20:  # Only for small graphs
                betweenness = nx.betweenness_centrality(G)
                features['max_betweenness'] = float(max(betweenness.values()))
                features['avg_betweenness'] = float(np.mean(list(betweenness.values())))
            else:
                features['max_betweenness'] = None
                features['avg_betweenness'] = None
            
            # Closeness centrality
            if n_nodes <= 20:
                closeness = nx.closeness_centrality(G)
                features['max_closeness'] = float(max(closeness.values()))
                features['avg_closeness'] = float(np.mean(list(closeness.values())))
            else:
                features['max_closeness'] = None
                features['avg_closeness'] = None
                
        except Exception as e:
            # If any centrality computation fails
            features['max_degree_centrality'] = None
            features['avg_degree_centrality'] = None
            features['max_betweenness'] = None
            features['avg_betweenness'] = None
            features['max_closeness'] = None
            features['avg_closeness'] = None
    else:
        features['max_degree_centrality'] = None
        features['avg_degree_centrality'] = None
        features['max_betweenness'] = None
        features['avg_betweenness'] = None
        features['max_closeness'] = None
        features['avg_closeness'] = None
    
    # Assortativity (degree correlation)
    if n_edges > 0 and n_nodes > 2:
        try:
            assortativity = nx.degree_assortativity_coefficient(G)
            # Convert NaN to None for JSON compatibility
            if np.isnan(assortativity):
                features['assortativity'] = None
            else:
                features['assortativity'] = float(assortativity)
        except:
            features['assortativity'] = None
    else:
        features['assortativity'] = None
    
    return features


def compute_full_graph_analysis(
    corr_matrix: np.ndarray,
    threshold_method: str = 'none',  # Changed default to 'none' to match MATLAB
    threshold_value: float = 0.0,    # Changed to 0.0 to keep all edges
    weighted: bool = True
) -> Dict:
    """
    Perform complete graph-based feature extraction.
    
    Pipeline:
    1. Construct adjacency matrix from correlation matrix
    2. Create graph
    3. Extract graph features
    
    Note: MATLAB keeps ALL edges regardless of weight. To match MATLAB behavior,
    use threshold_method='none' (default) which creates a fully connected graph
    with all correlation values as edge weights.
    
    Parameters:
    -----------
    corr_matrix : np.ndarray
        Correlation matrix from wavelet analysis (diagonal should be 0)
    threshold_method : str
        Thresholding method ('none', 'percentile', 'absolute', 'adaptive')
        Default 'none' keeps all edges like MATLAB
    threshold_value : float
        Threshold parameter (ignored if threshold_method='none')
    weighted : bool
        Use weighted edges
        
    Returns:
    --------
    result : dict
        Dictionary containing:
        - 'adj_matrix': Binary adjacency matrix (as list) or weighted matrix
        - 'threshold': Threshold value used
        - 'features': Dictionary of graph features
        - 'n_nodes': Number of nodes
    """
    
    # MATLAB behavior: use correlation matrix directly as adjacency (no thresholding)
    if threshold_method == 'none':
        # Use correlation matrix directly (already has diagonal=0, is symmetric)
        adj_matrix = np.abs(corr_matrix)  # Take absolute values for edge weights
        threshold_used = 0.0
    else:
        # Construct binary adjacency matrix with thresholding
        adj_matrix = construct_adjacency_matrix(
            corr_matrix,
            threshold_method=threshold_method,
            threshold_value=threshold_value
        )
        
        # Compute threshold value for reporting
        n = corr_matrix.shape[0]
        triu_indices = np.triu_indices(n, k=1)
        corr_values = corr_matrix[triu_indices]
        if threshold_method == 'percentile':
            threshold_used = float(np.percentile(np.abs(corr_values), threshold_value))
        elif threshold_method == 'absolute':
            threshold_used = float(threshold_value)
        elif threshold_method == 'adaptive':
            mean_val = np.mean(np.abs(corr_values))
            std_val = np.std(np.abs(corr_values))
            threshold_used = float(mean_val + threshold_value * std_val)
        else:
            threshold_used = None
    
    # Extract features
    weight_matrix = np.abs(corr_matrix) if weighted else None
    features = extract_graph_features(
        adj_matrix,
        weighted=weighted,
        weight_matrix=weight_matrix
    )
    
    # Package results
    result = {
        'adj_matrix': adj_matrix.tolist(),  # Convert to list for JSON
        'threshold_method': threshold_method,
        'threshold_value': threshold_value,
        'threshold_used': threshold_used,
        'features': features,
        'n_nodes': corr_matrix.shape[0]
    }
    
    return result
