"""
Video generation module for heart activation visualization.
Translates video_Activation.m MATLAB code to Python.

Creates synchronized video between point cloud activation and ECG signal over time.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
from typing import Optional, Tuple
import os


class ActivationVideoGenerator:
    """
    Generates activation video showing heart point cloud states synchronized with ECG signal.
    """

    # Color mapping for activation states
    COLORS = {
        'ideal': {
            0: (0.5, 0.5, 0.5),  # inactive → gray
            1: (0.0, 1.0, 0.0),  # trigger → green
            2: (1.0, 0.0, 0.0),  # depolarization → red
            3: (0.0, 0.0, 1.0),  # repolarization → blue
        },
        'eigen': {
            # For eigenbeat visualization, use amplitude-based coloring
            'cmap': 'viridis'
        }
    }

    def __init__(
        self,
        points: np.ndarray,
        signal_on_pc: np.ndarray,
        signal: np.ndarray,
        t_ms: np.ndarray,
        type_of_signal: str = 'ideal'
    ):
        """
        Initialize video generator.
        
        Args:
            points: Point cloud coordinates (N × 3)
            signal_on_pc: Matrix of states over time (N × T)
            signal: ECG signal vector (T,)
            t_ms: Time vector in milliseconds (T,)
            type_of_signal: 'ideal' or 'eigen'
        """
        self.points = points
        self.signal_on_pc = signal_on_pc
        self.signal = signal.flatten() if signal.ndim > 1 else signal
        self.t_ms = t_ms.flatten() if t_ms.ndim > 1 else t_ms
        self.type_of_signal = type_of_signal.lower()
        
        # Validate dimensions
        assert signal_on_pc.shape[1] == len(self.signal) == len(self.t_ms), \
            "signal_on_pc, signal and t_ms must have same temporal dimension"
        
        self.n_points = points.shape[0]
        self.n_frames = len(self.t_ms)

    def get_point_colors(self, frame_idx: int) -> np.ndarray:
        """
        Get point colors for a specific frame.
        
        Args:
            frame_idx: Frame index
            
        Returns:
            N × 3 array of RGB colors
        """
        states = self.signal_on_pc[:, frame_idx]
        colors = np.zeros((self.n_points, 3))
        
        if self.type_of_signal == 'ideal':
            # Discrete state coloring
            for state, color in self.COLORS['ideal'].items():
                mask = (states == state)
                colors[mask] = color
        else:  # eigen
            # Continuous amplitude coloring
            # Normalize values for colormap
            vmin, vmax = self.signal_on_pc.min(), self.signal_on_pc.max()
            normalized = (states - vmin) / (vmax - vmin + 1e-10)
            cmap = plt.get_cmap(self.COLORS['eigen']['cmap'])
            colors = cmap(normalized)[:, :3]  # Remove alpha channel
        
        return colors

    def generate_video(
        self,
        output_path: str,
        frame_rate: int = 30,
        figsize: Tuple[int, int] = (14, 6),
        dpi: int = 100
    ) -> str:
        """
        Generate and save activation video.
        
        Args:
            output_path: Path to save video file
            frame_rate: Video frame rate (fps)
            figsize: Figure size in inches
            dpi: Dots per inch for video
            
        Returns:
            Path to saved video file
        """
        # Create figure with two subplots
        fig = plt.figure(figsize=figsize)
        
        # 3D point cloud subplot
        ax_pc = fig.add_subplot(121, projection='3d')
        ax_pc.set_xlabel('X')
        ax_pc.set_ylabel('Y')
        ax_pc.set_zlabel('Z')
        ax_pc.set_title('Heart Activation')
        
        # Set consistent view limits
        ax_pc.set_xlim([self.points[:, 0].min() - 1, self.points[:, 0].max() + 1])
        ax_pc.set_ylim([self.points[:, 1].min() - 1, self.points[:, 1].max() + 1])
        ax_pc.set_zlim([self.points[:, 2].min() - 1, self.points[:, 2].max() + 1])
        
        # ECG signal subplot
        ax_ecg = fig.add_subplot(122)
        ax_ecg.plot(self.t_ms, self.signal, 'b-', linewidth=0.5, alpha=0.3)
        ax_ecg.set_xlabel('Time (ms)')
        ax_ecg.set_ylabel('Amplitude')
        ax_ecg.set_title('ECG Signal')
        ax_ecg.set_xlim([self.t_ms[0], self.t_ms[-1]])
        ax_ecg.set_ylim([self.signal.min() - 0.1, self.signal.max() + 0.1])
        ax_ecg.grid(True, alpha=0.3)
        
        # Initialize plots
        colors_init = self.get_point_colors(0)
        scatter = ax_pc.scatter(
            self.points[:, 0],
            self.points[:, 1],
            self.points[:, 2],
            c=colors_init,
            s=1,
            alpha=0.6
        )
        
        # Current time marker on ECG
        time_marker, = ax_ecg.plot([self.t_ms[0], self.t_ms[0]], 
                                     [self.signal.min(), self.signal.max()],
                                     'r-', linewidth=2)
        
        # Highlight current signal portion
        signal_highlight, = ax_ecg.plot([], [], 'b-', linewidth=2)
        
        # Time text
        time_text = ax_ecg.text(0.02, 0.95, '', transform=ax_ecg.transAxes,
                                fontsize=12, verticalalignment='top',
                                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        def init():
            """Initialize animation."""
            return scatter, time_marker, signal_highlight, time_text

        def update(frame):
            """Update function for animation."""
            # Update point cloud colors
            colors = self.get_point_colors(frame)
            scatter._facecolors = colors
            
            # Update time marker
            t_current = self.t_ms[frame]
            time_marker.set_xdata([t_current, t_current])
            
            # Update highlighted signal
            signal_highlight.set_data(self.t_ms[:frame+1], self.signal[:frame+1])
            
            # Update time text
            time_text.set_text(f'Time: {t_current:.1f} ms')
            
            return scatter, time_marker, signal_highlight, time_text

        # Create animation
        anim = FuncAnimation(
            fig,
            update,
            init_func=init,
            frames=self.n_frames,
            interval=1000 / frame_rate,
            blit=False,
            repeat=True
        )
        
        # Save video
        writer = FFMpegWriter(fps=frame_rate, bitrate=1800)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        anim.save(output_path, writer=writer, dpi=dpi)
        plt.close(fig)
        
        return output_path

    def generate_frame_image(self, frame_idx: int, output_path: str) -> str:
        """
        Generate single frame as image.
        
        Args:
            frame_idx: Frame index to render
            output_path: Path to save image
            
        Returns:
            Path to saved image
        """
        fig = plt.figure(figsize=(14, 6))
        
        # 3D point cloud
        ax_pc = fig.add_subplot(121, projection='3d')
        colors = self.get_point_colors(frame_idx)
        ax_pc.scatter(
            self.points[:, 0],
            self.points[:, 1],
            self.points[:, 2],
            c=colors,
            s=1,
            alpha=0.6
        )
        ax_pc.set_xlabel('X')
        ax_pc.set_ylabel('Y')
        ax_pc.set_zlabel('Z')
        ax_pc.set_title(f'Heart Activation - Time: {self.t_ms[frame_idx]:.1f} ms')
        
        # ECG signal
        ax_ecg = fig.add_subplot(122)
        ax_ecg.plot(self.t_ms, self.signal, 'b-', linewidth=0.5, alpha=0.3)
        ax_ecg.plot(self.t_ms[:frame_idx+1], self.signal[:frame_idx+1], 'b-', linewidth=2)
        ax_ecg.axvline(self.t_ms[frame_idx], color='r', linewidth=2)
        ax_ecg.set_xlabel('Time (ms)')
        ax_ecg.set_ylabel('Amplitude')
        ax_ecg.set_title('ECG Signal')
        ax_ecg.grid(True, alpha=0.3)
        
        plt.tight_layout()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        return output_path
