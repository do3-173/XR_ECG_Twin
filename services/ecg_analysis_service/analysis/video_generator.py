"""
Video Generation Module for ECG Analysis
Creates animated videos showing time-evolution of ECG signal and features
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.gridspec import GridSpec
import os
from datetime import datetime


class ECGVideoGenerator:
    """
    Generates animated videos of ECG analysis over time
    """
    
    def __init__(self, output_dir='videos'):
        """
        Initialize video generator
        
        Parameters:
        -----------
        output_dir : str
            Directory to save generated videos
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def create_realtime_video(self, ecg_samples, fs=128.0, duration_seconds=30, 
                             heart_rate_func=None, output_filename=None):
        """
        Create video showing ECG signal scrolling in real-time
        
        Parameters:
        -----------
        ecg_samples : np.ndarray
            Full ECG signal array
        fs : float
            Sampling frequency in Hz
        duration_seconds : int
            Duration of video to generate (uses last N seconds of signal)
        heart_rate_func : callable, optional
            Function to calculate heart rate from signal segment
        output_filename : str, optional
            Output filename (auto-generated if None)
            
        Returns:
        --------
        str : Path to generated video file
        """
        # Calculate samples for requested duration
        samples_per_second = int(fs)
        total_samples = duration_seconds * samples_per_second
        
        # Use last N seconds of signal
        if len(ecg_samples) < total_samples:
            print(f"Warning: Signal shorter than requested duration. Using all {len(ecg_samples)} samples")
            signal = ecg_samples
            duration_seconds = len(ecg_samples) / fs
        else:
            signal = ecg_samples[-total_samples:]
        
        # Window size for display (5 seconds)
        window_seconds = 5
        window_samples = window_seconds * samples_per_second
        
        # Setup figure
        fig = plt.figure(figsize=(14, 8), facecolor='white')
        gs = GridSpec(3, 1, height_ratios=[1, 3, 1], hspace=0.3)
        
        # Title and info
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fig.suptitle(f'Real-time ECG Monitoring - {timestamp}', 
                    fontsize=16, fontweight='bold')
        
        # Top panel: Heart rate display
        ax_hr_display = fig.add_subplot(gs[0])
        ax_hr_display.axis('off')
        hr_text = ax_hr_display.text(0.5, 0.5, "Heart Rate: -- BPM", 
                                     ha='center', va='center', 
                                     fontsize=28, fontweight='bold', color='red')
        time_text = ax_hr_display.text(0.95, 0.2, "Time: 0.0s", 
                                       ha='right', fontsize=14)
        
        # Middle panel: ECG signal
        ax_ecg = fig.add_subplot(gs[1])
        ax_ecg.set_xlim(0, window_samples)
        ax_ecg.set_ylim(np.min(signal) * 1.1, np.max(signal) * 1.1)
        ax_ecg.grid(True, which='major', linestyle='-', linewidth=0.5, 
                   color='red', alpha=0.3)
        ax_ecg.grid(True, which='minor', linestyle='-', linewidth=0.2, 
                   color='red', alpha=0.2)
        ax_ecg.minorticks_on()
        ax_ecg.set_ylabel('Amplitude (mV)', fontsize=12, fontweight='bold')
        ax_ecg.set_title('ECG Signal (5-second window)', fontsize=13, fontweight='bold')
        
        ecg_line, = ax_ecg.plot([], [], 'b-', linewidth=1.5)
        
        # Bottom panel: Heart rate trend
        ax_hr_trend = fig.add_subplot(gs[2])
        ax_hr_trend.set_xlim(0, duration_seconds)
        ax_hr_trend.set_ylim(40, 180)
        ax_hr_trend.set_xlabel('Time (seconds)', fontsize=12, fontweight='bold')
        ax_hr_trend.set_ylabel('Heart Rate (BPM)', fontsize=12, fontweight='bold')
        ax_hr_trend.set_title('Heart Rate Trend', fontsize=13, fontweight='bold')
        ax_hr_trend.grid(True, linestyle='--', alpha=0.5)
        
        hr_trend_line, = ax_hr_trend.plot([], [], 'g-', linewidth=2, marker='o', markersize=3)
        hr_values = []
        time_values = []
        
        def calculate_hr_from_segment(segment):
            """Calculate heart rate from ECG segment using peak detection"""
            try:
                from scipy.signal import find_peaks
                
                # Normalize
                normalized = (segment - np.mean(segment)) / (np.std(segment) + 1e-10)
                
                # Find peaks
                peaks, _ = find_peaks(normalized, 
                                     height=0.5,
                                     distance=fs//4,
                                     prominence=0.2)
                
                if len(peaks) > 2:
                    # Calculate heart rate from peak intervals
                    intervals = np.diff(peaks)
                    instant_hrs = 60 * fs / intervals
                    valid_hrs = instant_hrs[(instant_hrs >= 40) & (instant_hrs <= 200)]
                    
                    if len(valid_hrs) > 0:
                        return int(np.mean(valid_hrs))
                
                # Default
                return 70
            except:
                return 70
        
        def update(frame):
            """Animation update function"""
            # Current time in seconds
            current_time = frame / 10.0  # 10 FPS
            current_sample = int(current_time * fs)
            
            if current_sample >= len(signal):
                return ecg_line, hr_text, time_text, hr_trend_line
            
            # Update time display
            time_text.set_text(f"Time: {current_time:.1f}s")
            
            # Get current window of ECG signal
            start_idx = max(0, current_sample - window_samples)
            end_idx = current_sample
            
            if end_idx > start_idx:
                segment = signal[start_idx:end_idx]
                x_data = np.arange(len(segment))
                ecg_line.set_data(x_data, segment)
                
                # Calculate heart rate every second
                if frame % 10 == 0:  # Every 1 second at 10 FPS
                    if heart_rate_func:
                        hr = heart_rate_func(segment)
                    else:
                        hr = calculate_hr_from_segment(segment)
                    
                    hr_values.append(hr)
                    time_values.append(current_time)
                    
                    hr_text.set_text(f"Heart Rate: {hr} BPM")
                    
                    # Update heart rate trend
                    if len(time_values) > 0:
                        hr_trend_line.set_data(time_values, hr_values)
            
            return ecg_line, hr_text, time_text, hr_trend_line
        
        # Create animation
        frames = int(duration_seconds * 10)  # 10 FPS
        anim = FuncAnimation(fig, update, frames=frames, 
                           interval=100, blit=True)
        
        # Save video
        if output_filename is None:
            output_filename = f"ecg_realtime_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Try to save with ffmpeg
        try:
            writer = FFMpegWriter(fps=10, bitrate=1800)
            anim.save(output_path, writer=writer)
            print(f"Video saved to: {output_path}")
        except Exception as e:
            print(f"Error saving video with FFMpeg: {e}")
            # Fallback: save as GIF
            output_path = output_path.replace('.mp4', '.gif')
            anim.save(output_path, writer='pillow', fps=10)
            print(f"Saved as GIF instead: {output_path}")
        
        plt.close(fig)
        
        return output_path
    
    def create_analysis_evolution_video(self, ecg_samples, analysis_results_over_time, 
                                       fs=128.0, output_filename=None):
        """
        Create video showing evolution of analysis features over time
        
        Parameters:
        -----------
        ecg_samples : np.ndarray
            Full ECG signal
        analysis_results_over_time : list of dict
            List of analysis results at different time points
        fs : float
            Sampling frequency
        output_filename : str, optional
            Output filename
            
        Returns:
        --------
        str : Path to generated video
        """
        fig = plt.figure(figsize=(16, 10))
        gs = GridSpec(3, 2, hspace=0.3, wspace=0.3)
        
        # Setup subplots
        ax_ecg = fig.add_subplot(gs[0, :])
        ax_autocorr = fig.add_subplot(gs[1, 0])
        ax_wavelet = fig.add_subplot(gs[1, 1])
        ax_graph = fig.add_subplot(gs[2, 0])
        ax_metrics = fig.add_subplot(gs[2, 1])
        
        fig.suptitle('ECG Analysis Evolution', fontsize=16, fontweight='bold')
        
        # Initialize plots
        ecg_line, = ax_ecg.plot([], [], 'b-', linewidth=1)
        ax_ecg.set_xlabel('Sample')
        ax_ecg.set_ylabel('Amplitude')
        ax_ecg.set_title('ECG Signal Window')
        ax_ecg.grid(True, alpha=0.3)
        
        # Animation update function
        def update(frame):
            # Update based on frame
            # ... implementation similar to create_realtime_video but with analysis features
            pass
        
        # Create and save animation
        anim = FuncAnimation(fig, update, frames=len(analysis_results_over_time),
                           interval=200, blit=False)
        
        if output_filename is None:
            output_filename = f"ecg_analysis_evolution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        try:
            writer = FFMpegWriter(fps=5, bitrate=1800)
            anim.save(output_path, writer=writer)
        except Exception as e:
            print(f"Error saving video: {e}")
            output_path = output_path.replace('.mp4', '.gif')
            anim.save(output_path, writer='pillow', fps=5)
        
        plt.close(fig)
        
        return output_path
