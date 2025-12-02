"""
ECG Analysis Visualization Module
Generates plots and animations for autocorrelation, wavelet, and graph features
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.animation as animation
from matplotlib.colors import LinearSegmentedColormap
import networkx as nx
from io import BytesIO
import base64
from datetime import datetime
import os


class ECGVisualizer:
    """
    Generates visualizations for ECG analysis results
    """
    
    def __init__(self, output_dir='plots'):
        """
        Initialize visualizer
        
        Parameters:
        -----------
        output_dir : str
            Directory to save generated plots
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        
    def plot_autocorrelation(self, autocorr_data, fs=128.0, features=None):
        """
        Plot autocorrelation function with detected features
        
        Parameters:
        -----------
        autocorr_data : dict
            Contains 'autocorr', 'lags' arrays
        fs : float
            Sampling frequency
        features : dict
            Autocorrelation features (first_min_lag, first_peak_lag, etc.)
            
        Returns:
        --------
        str : Base64 encoded PNG image
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        autocorr = np.array(autocorr_data['autocorr'])
        lags = np.array(autocorr_data['lags'])
        
        # Convert lags to time (seconds)
        time_lags = lags / fs
        
        # Plot autocorrelation
        ax.plot(time_lags, autocorr, 'b-', linewidth=1.5, label='Autocorrelation')
        ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        
        # Mark features if provided
        if features:
            if features.get('first_min_lag'):
                min_time = features['first_min_lag'] / fs
                ax.plot(min_time, features.get('first_min_value', 0), 
                       'ro', markersize=10, label=f'First Min ({min_time:.2f}s)')
                
            if features.get('first_peak_lag'):
                peak_time = features['first_peak_lag'] / fs
                ax.plot(peak_time, features.get('first_peak_value', 0),
                       'g^', markersize=10, label=f'First Peak ({peak_time:.2f}s)')
        
        ax.set_xlabel('Lag (seconds)', fontsize=12)
        ax.set_ylabel('Autocorrelation', fontsize=12)
        ax.set_title('ECG Signal Autocorrelation Function', fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        # Add text box with features
        if features:
            textstr = f"Periodicity: {features.get('periodicity_strength', 0):.3f}\n"
            textstr += f"Decay rate: {features.get('decay_rate', 0):.6f}"
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
                   verticalalignment='top', bbox=props)
        
        plt.tight_layout()
        
        # Convert to base64
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return img_base64
    
    def plot_wavelet_scales(self, wavelet_data, fs=128.0, heart_rate=None):
        """
        Plot wavelet decomposition scales
        
        Parameters:
        -----------
        wavelet_data : dict
            Contains 'coeffs_d' (detail coefficients), 'level', 'wavelet_name'
        fs : float
            Sampling frequency
        heart_rate : float
            Current heart rate in BPM
            
        Returns:
        --------
        str : Base64 encoded PNG image
        """
        coeffs_d = wavelet_data.get('coeffs_d', [])
        level = len(coeffs_d)
        wavelet_name = wavelet_data.get('wavelet_name', 'sym4')
        
        fig, axes = plt.subplots(level, 1, figsize=(14, 2*level), sharex=True)
        
        if level == 1:
            axes = [axes]
        
        title_suffix = f" - HR: {heart_rate:.1f} bpm" if heart_rate else ""
        fig.suptitle(f'Wavelet Decomposition ({wavelet_name}){title_suffix}', 
                    fontsize=14, fontweight='bold')
        
        for i, (ax, coeff) in enumerate(zip(axes, coeffs_d)):
            if isinstance(coeff, (list, np.ndarray)) and len(coeff) > 0:
                coeff_array = np.array(coeff).flatten()
                time = np.arange(len(coeff_array)) / fs
                
                # Calculate frequency band for this level
                freq_high = fs / (2 ** (i + 1))
                freq_low = fs / (2 ** (i + 2))
                
                ax.plot(time, coeff_array, linewidth=0.8)
                ax.set_ylabel(f'D{i+1}\n({freq_low:.1f}-{freq_high:.1f} Hz)', 
                            fontsize=10, rotation=0, ha='right', va='center')
                ax.grid(True, alpha=0.3)
                
                # Add statistics
                energy = np.sum(coeff_array ** 2)
                ax.text(0.98, 0.95, f'E={energy:.2f}', transform=ax.transAxes,
                       fontsize=8, ha='right', va='top',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
        
        axes[-1].set_xlabel('Time (seconds)', fontsize=12)
        plt.tight_layout()
        
        # Convert to base64
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return img_base64
    
    def plot_wavelet_xcorr_sequences(self, wavelet_data, wavelet_name='sym4', heart_rate=None):
        """
        Plot wavelet cross-correlation sequences (MATLAB RWW style)
        Shows each scale's cross-correlation sequence as a subplot
        
        Parameters:
        -----------
        wavelet_data : dict
            Contains 'xcorr_sequences' - list of cross-correlation arrays for each scale
        wavelet_name : str
            Wavelet name
        heart_rate : float
            Current heart rate
            
        Returns:
        --------
        str : Base64 encoded PNG image
        """
        xcorr_seqs = wavelet_data.get('xcorr_sequences', [])
        
        if not xcorr_seqs or len(xcorr_seqs) == 0:
            # No cross-correlation sequences available
            fig, ax = plt.subplots(figsize=(14, 8))
            ax.text(0.5, 0.5, 'Cross-correlation sequences not available', 
                   ha='center', va='center', fontsize=14)
            ax.axis('off')
        else:
            num_levels = len(xcorr_seqs)
            fig, axes = plt.subplots(num_levels, 1, figsize=(14, 2*num_levels), sharex=True)
            
            if num_levels == 1:
                axes = [axes]
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            title_suffix = f"HR: {heart_rate:.1f} bpm" if heart_rate else ""
            fig.suptitle(f'Wavelet Cross-correlation ({wavelet_name}) - {timestamp}\n{title_suffix}', 
                        fontsize=14, fontweight='bold')
            
            for i, (ax, seq) in enumerate(zip(axes, xcorr_seqs)):
                if isinstance(seq, (list, np.ndarray)) and len(seq) > 0:
                    seq_array = np.array(seq).flatten()
                    
                    # Create lag axis centered at 0
                    seq_len = len(seq_array)
                    lags = np.arange(seq_len) - seq_len // 2
                    
                    # Normalize to [-1, 1] range for visualization
                    max_val = np.max(np.abs(seq_array))
                    if max_val > 0:
                        seq_normalized = seq_array / max_val
                    else:
                        seq_normalized = seq_array
                    
                    ax.plot(lags, seq_normalized, linewidth=1.5, color='#1976d2')
                    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
                    ax.axvline(x=0, color='red', linestyle='--', alpha=0.4, linewidth=1)
                    ax.set_ylabel(f'Scale {i+1} - {title_suffix}', fontsize=10)
                    ax.set_ylim([-1.2, 1.2])
                    ax.grid(True, alpha=0.3)
                    
            axes[-1].set_xlabel('Lag', fontsize=12)
            plt.tight_layout()
        
        # Convert to base64
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return img_base64
    
    def plot_wavelet_xcorr_heatmap(self, xcorr_matrix, wavelet_name='sym4', heart_rate=None):
        """
        Plot wavelet correlation matrix as heatmap
        
        Parameters:
        -----------
        xcorr_matrix : np.ndarray or list
            J x J correlation matrix between wavelet scales
        wavelet_name : str
            Wavelet name
        heart_rate : float
            Current heart rate
            
        Returns:
        --------
        str : Base64 encoded PNG image
        """
        if isinstance(xcorr_matrix, list):
            xcorr_matrix = np.array(xcorr_matrix)
        
        fig, ax = plt.subplots(figsize=(8, 7))
        
        im = ax.imshow(xcorr_matrix, cmap='coolwarm', aspect='auto', 
                      vmin=-1, vmax=1, interpolation='nearest')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Correlation Coefficient', rotation=270, labelpad=20, fontsize=11)
        
        # Set ticks
        n_scales = xcorr_matrix.shape[0]
        ax.set_xticks(np.arange(n_scales))
        ax.set_yticks(np.arange(n_scales))
        ax.set_xticklabels([f'D{i+1}' for i in range(n_scales)])
        ax.set_yticklabels([f'D{i+1}' for i in range(n_scales)])
        
        # Add values in cells
        for i in range(n_scales):
            for j in range(n_scales):
                text = ax.text(j, i, f'{xcorr_matrix[i, j]:.2f}',
                             ha="center", va="center", color="black", fontsize=9)
        
        title_suffix = f" - HR: {heart_rate:.1f} bpm" if heart_rate else ""
        ax.set_title(f'Wavelet Correlation Matrix ({wavelet_name}){title_suffix}',
                    fontsize=13, fontweight='bold')
        ax.set_xlabel('Scale', fontsize=11)
        ax.set_ylabel('Scale', fontsize=11)
        
        plt.tight_layout()
        
        # Convert to base64
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return img_base64
    
    def plot_graph_features_matlab_style(self, adj_matrix, wavelet_name='sym4', heart_rate=None):
        """
        Plot graph network from adjacency matrix (MATLAB style)
        Single plot showing network topology with colored edges
        Matches MATLAB's plot_features_euvip04.m implementation
        
        Parameters:
        -----------
        adj_matrix : np.ndarray or list
            Adjacency matrix
        wavelet_name : str
            Wavelet name
        heart_rate : float
            Current heart rate
            
        Returns:
        --------
        str : Base64 encoded PNG image
        """
        if isinstance(adj_matrix, list):
            adj_matrix = np.array(adj_matrix)
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Create graph from adjacency matrix
        G = nx.from_numpy_array(adj_matrix)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        title_suffix = f"HR: {heart_rate:.1f} bpm" if heart_rate else ""
        
        if G.number_of_edges() > 0:
            # Use spring layout (force-directed) to match MATLAB's default graph layout
            pos = nx.spring_layout(G, seed=42, k=1.5, iterations=50)
            
            # Get edge weights
            edges = list(G.edges())
            weights = np.array([G[u][v]['weight'] for u, v in edges])
            
            # MATLAB-style edge width normalization
            # minWidth + (maxWidth - minWidth) * (weights - min(weights)) / (max(weights) - min(weights))
            minWidth = 0.5
            maxWidth = 2.5
            if len(weights) > 0 and (max(weights) - min(weights)) > 0:
                normalized_widths = minWidth + (maxWidth - minWidth) * (weights - min(weights)) / (max(weights) - min(weights))
            else:
                normalized_widths = np.ones(len(weights)) * minWidth
            
            # Draw nodes
            node_labels = {i: str(i+1) for i in range(G.number_of_nodes())}
            nx.draw_networkx_nodes(G, pos, ax=ax, 
                                  node_color='cyan',
                                  node_size=600, 
                                  alpha=0.9,
                                  edgecolors='black',
                                  linewidths=1.5)
            
            # Draw node labels
            nx.draw_networkx_labels(G, pos, node_labels, ax=ax, 
                                   font_size=12, 
                                   font_weight='bold',
                                   font_color='black')
            
            # Draw edges with colors based on weights (MATLAB jet colormap)
            # Fixed colormap limits [0, 0.7] to match MATLAB: clim([0,0.7])
            edge_collection = nx.draw_networkx_edges(
                G, pos, ax=ax,
                width=normalized_widths,
                edge_color=weights,
                edge_cmap=plt.cm.jet,
                edge_vmin=0.0,
                edge_vmax=0.7,  # Fixed to 0.7 like MATLAB clim([0,0.7])
                alpha=0.8
            )
            
            # Add colorbar with fixed limits [0, 0.7]
            if edge_collection:
                sm = plt.cm.ScalarMappable(
                    cmap=plt.cm.jet,
                    norm=plt.Normalize(vmin=0.0, vmax=0.7)
                )
                sm.set_array([])
                cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
                cbar.set_label('Edge Weight (Correlation)', rotation=270, labelpad=20, fontsize=11)
        else:
            # No edges - show disconnected nodes
            pos = nx.spring_layout(G, seed=42)
            node_labels = {i: str(i+1) for i in range(G.number_of_nodes())}
            nx.draw_networkx_nodes(G, pos, ax=ax,
                                  node_color='lightgray',
                                  node_size=600,
                                  alpha=0.6)
            nx.draw_networkx_labels(G, pos, node_labels, ax=ax,
                                   font_size=12,
                                   font_weight='bold')
            
            ax.text(0.5, 0.05, 'No significant correlations detected', 
                   ha='center', fontsize=11, transform=ax.transAxes,
                   bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        ax.set_title(f'Graph Features ({wavelet_name}) - {title_suffix} - {timestamp}',
                    fontsize=13, fontweight='bold')
        ax.axis('off')
        ax.set_aspect('equal')
        
        plt.tight_layout()
        
        # Convert to base64
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return img_base64
    
    def plot_graph_features(self, adj_matrix, graph_features, heart_rate=None):
        """
        Plot graph network from adjacency matrix
        
        Parameters:
        -----------
        adj_matrix : np.ndarray or list
            Adjacency matrix
        graph_features : dict
            Graph features (n_nodes, n_edges, density, etc.)
        heart_rate : float
            Current heart rate
            
        Returns:
        --------
        str : Base64 encoded PNG image
        """
        if isinstance(adj_matrix, list):
            adj_matrix = np.array(adj_matrix)
        
        fig, ax1 = plt.subplots(figsize=(14, 6))
        
        # Plot 1: Network graph
        G = nx.from_numpy_array(adj_matrix)
        
        if G.number_of_edges() > 0:
            pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
            
            # Get edge weights
            edges = G.edges()
            weights = [G[u][v]['weight'] for u, v in edges]
            
            # Normalize edge widths
            if len(weights) > 0 and max(weights) > 0:
                norm_weights = [(w / max(weights)) * 3 + 0.5 for w in weights]
            else:
                norm_weights = [1.0] * len(weights)
            
            # Draw network
            nx.draw_networkx_nodes(G, pos, ax=ax1, node_color='lightblue',
                                  node_size=800, alpha=0.9)
            nx.draw_networkx_labels(G, pos, ax=ax1, font_size=10, font_weight='bold')
            
            # Draw edges with color based on weight
            edges_collection = nx.draw_networkx_edges(G, pos, ax=ax1, 
                                                     width=norm_weights,
                                                     edge_color=weights,
                                                     edge_cmap=plt.cm.plasma,
                                                     edge_vmin=0,
                                                     edge_vmax=max(weights) if weights else 1)
            
            # Add colorbar for edge weights
            if edges_collection:
                sm = plt.cm.ScalarMappable(cmap=plt.cm.plasma,
                                          norm=plt.Normalize(vmin=0, vmax=max(weights) if weights else 1))
                sm.set_array([])
                cbar = plt.colorbar(sm, ax=ax1, fraction=0.046, pad=0.04)
                cbar.set_label('Edge Weight', rotation=270, labelpad=15)
        else:
            # Empty graph
            ax1.text(0.5, 0.5, 'No edges detected\n(Disconnected network)', 
                    ha='center', va='center', fontsize=12, transform=ax1.transAxes)
        
        title_suffix = f" - HR: {heart_rate:.1f} bpm" if heart_rate else ""
        ax1.set_title(f'Graph Network Topology{title_suffix}', fontsize=12, fontweight='bold')
        ax1.axis('off')
        
        plt.tight_layout()
        
        # Convert to base64
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return img_base64
    
    def create_analysis_dashboard(self, analysis_result):
        """
        Create comprehensive dashboard with all analysis visualizations
        
        Parameters:
        -----------
        analysis_result : dict
            Complete analysis result from API
            
        Returns:
        --------
        dict : Dictionary with base64 encoded images for each plot type
        """
        plots = {}
        
        # Get data
        autocorr_data = analysis_result.get('autocorr_data', {})
        wavelet_data = analysis_result.get('wavelet_data', {})
        graph_data = analysis_result.get('graph_data', {})
        
        # Extract heart rate from API if provided, otherwise calculate from autocorr
        heart_rate = analysis_result.get('heart_rate')  # From API
        
        if heart_rate is None:
            # Calculate from first_peak_lag if not provided
            first_peak_lag = analysis_result.get('autocorr_first_peak_lag')
            fs = analysis_result.get('fs', 128.0)
            if first_peak_lag and first_peak_lag > 0:
                heart_rate = (fs * 60.0) / first_peak_lag
                # Sanity check: HR should be between 30-200 bpm for human
                if heart_rate < 30 or heart_rate > 200:
                    # If out of range, recalculate assuming typical range
                    heart_rate = 70.0  # Default fallback
            else:
                heart_rate = 70.0  # Default fallback
        
        # Generate plots
        try:
            if autocorr_data and 'autocorr' in autocorr_data:
                features = {
                    'first_min_lag': analysis_result.get('autocorr_first_min_lag'),
                    'first_min_value': analysis_result.get('autocorr_first_min_value'),
                    'first_peak_lag': analysis_result.get('autocorr_first_peak_lag'),
                    'first_peak_value': analysis_result.get('autocorr_first_peak_value'),
                    'periodicity_strength': analysis_result.get('autocorr_periodicity_strength'),
                    'decay_rate': analysis_result.get('autocorr_decay_rate'),
                }
                plots['autocorr'] = self.plot_autocorrelation(autocorr_data, 
                                                             analysis_result.get('fs', 128.0),
                                                             features)
        except Exception as e:
            print(f"Error creating autocorrelation plot: {e}")
        
        try:
            if wavelet_data and 'coeffs_d' in wavelet_data:
                plots['wavelet_scales'] = self.plot_wavelet_scales(wavelet_data,
                                                                   analysis_result.get('fs', 128.0),
                                                                   heart_rate)
        except Exception as e:
            print(f"Error creating wavelet scales plot: {e}")
        
        # NEW: Wavelet cross-correlation sequences plot (MATLAB RWW style)
        try:
            if wavelet_data and 'xcorr_sequences' in wavelet_data:
                plots['wavelet_xcorr_sequences'] = self.plot_wavelet_xcorr_sequences(
                    wavelet_data,
                    analysis_result.get('wavelet_name', 'sym4'),
                    heart_rate
                )
        except Exception as e:
            print(f"Error creating wavelet cross-correlation sequences plot: {e}")
        
        try:
            if wavelet_data and 'corr_matrix' in wavelet_data:
                plots['wavelet_xcorr'] = self.plot_wavelet_xcorr_heatmap(
                    wavelet_data['corr_matrix'],
                    analysis_result.get('wavelet_name', 'sym4'),
                    heart_rate
                )
        except Exception as e:
            print(f"Error creating correlation heatmap: {e}")
        
        # NEW: MATLAB-style graph visualization (single plot with colored edges)
        try:
            if graph_data and 'adj_matrix' in graph_data:
                plots['graph_matlab'] = self.plot_graph_features_matlab_style(
                    graph_data['adj_matrix'],
                    analysis_result.get('wavelet_name', 'sym4'),
                    heart_rate
                )
        except Exception as e:
            print(f"Error creating MATLAB-style graph plot: {e}")
        
        try:
            if graph_data and 'adj_matrix' in graph_data:
                graph_features = {
                    'n_nodes': analysis_result.get('graph_n_nodes'),
                    'n_edges': analysis_result.get('graph_n_edges'),
                    'density': analysis_result.get('graph_density'),
                    'avg_degree': analysis_result.get('graph_avg_degree'),
                    'avg_clustering': analysis_result.get('graph_avg_clustering'),
                    'n_components': analysis_result.get('graph_n_components'),
                    'is_connected': analysis_result.get('graph_is_connected'),
                    'diameter': analysis_result.get('graph_diameter'),
                }
                plots['graph'] = self.plot_graph_features(graph_data['adj_matrix'],
                                                         graph_features,
                                                         heart_rate)
        except Exception as e:
            print(f"Error creating graph plot: {e}")
        
        return plots
