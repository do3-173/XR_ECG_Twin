"""
ECG Signal Processing Module
Python replacement for MATLAB ECG processing functions
"""
import numpy as np
from scipy import signal
from scipy.signal import butter, filtfilt, find_peaks
import pywt


class ECGProcessor:
    """
    ECG signal processing and feature extraction
    Replaces MATLAB functions from the original project
    """
    
    def __init__(self, sampling_rate=128):
        self.sampling_rate = sampling_rate
        
    def preprocess_ecg(self, ecg_signal):
        """
        Preprocess ECG signal (bandpass filter + baseline wander removal)
        Replaces: compute_ECGpreproc.m
        """
        # Bandpass filter (0.5-40 Hz)
        nyquist = self.sampling_rate / 2
        low = 0.5 / nyquist
        high = 40.0 / nyquist
        b, a = butter(4, [low, high], btype='band')
        filtered = filtfilt(b, a, ecg_signal)
        
        # Remove baseline wander using median filter
        baseline = signal.medfilt(filtered, kernel_size=int(0.2 * self.sampling_rate) | 1)
        clean_signal = filtered - baseline
        
        return clean_signal
    
    def detect_r_peaks(self, ecg_signal):
        """
        Detect R-peaks in ECG signal
        Returns peak indices and heart rates
        """
        clean_signal = self.preprocess_ecg(ecg_signal)
        
        # Find peaks
        distance = int(0.6 * self.sampling_rate)  # Minimum 0.6s between peaks
        height = np.percentile(clean_signal, 75)  # Adaptive threshold
        
        peaks, properties = find_peaks(
            clean_signal,
            distance=distance,
            height=height,
            prominence=height * 0.3
        )
        
        # Calculate heart rate
        if len(peaks) > 1:
            rr_intervals = np.diff(peaks) / self.sampling_rate
            heart_rates = 60.0 / rr_intervals
        else:
            heart_rates = np.array([])
        
        return peaks, heart_rates
    
    def compute_hrv_features(self, ecg_signal):
        """
        Compute Heart Rate Variability features
        """
        peaks, heart_rates = self.detect_r_peaks(ecg_signal)
        
        if len(peaks) < 2:
            return {}
        
        rr_intervals = np.diff(peaks) / self.sampling_rate * 1000  # in ms
        
        features = {
            'mean_hr': np.mean(heart_rates) if len(heart_rates) > 0 else 0,
            'std_hr': np.std(heart_rates) if len(heart_rates) > 0 else 0,
            'rmssd': np.sqrt(np.mean(np.square(np.diff(rr_intervals)))),
            'sdnn': np.std(rr_intervals),
            'pnn50': self._calculate_pnn50(rr_intervals),
        }
        
        return features
    
    def _calculate_pnn50(self, rr_intervals):
        """Calculate percentage of successive RR intervals > 50ms"""
        if len(rr_intervals) < 2:
            return 0
        diff_rr = np.abs(np.diff(rr_intervals))
        return 100.0 * np.sum(diff_rr > 50) / len(diff_rr)
    
    def wavelet_analysis(self, ecg_signal, wavelet='db4', level=5):
        """
        Wavelet decomposition for feature extraction
        Replaces: modwtxcorr_stf.m and computeFeat_modwtxcorr03.m
        """
        coeffs = pywt.wavedec(ecg_signal, wavelet, level=level)
        
        features = {}
        for i, coeff in enumerate(coeffs):
            features[f'wavelet_level_{i}_energy'] = np.sum(coeff ** 2)
            features[f'wavelet_level_{i}_mean'] = np.mean(np.abs(coeff))
            features[f'wavelet_level_{i}_std'] = np.std(coeff)
        
        return features
    
    def extract_all_features(self, ecg_signal):
        """
        Extract comprehensive feature set from ECG signal
        Combines all processing methods
        """
        try:
            features = {}
            
            # HRV features
            hrv_features = self.compute_hrv_features(ecg_signal)
            features.update(hrv_features)
            
            # Wavelet features
            wavelet_features = self.wavelet_analysis(ecg_signal)
            features.update(wavelet_features)
            
            # Statistical features
            clean_signal = self.preprocess_ecg(ecg_signal)
            features['signal_mean'] = np.mean(clean_signal)
            features['signal_std'] = np.std(clean_signal)
            features['signal_min'] = np.min(clean_signal)
            features['signal_max'] = np.max(clean_signal)
            
            return features
            
        except Exception as e:
            return {'error': str(e)}
    
    def classify_heart_rate_zone(self, heart_rate):
        """
        Classify heart rate into zones
        """
        if heart_rate < 40:
            return 0, "Below normal"
        elif 40 <= heart_rate <= 60:
            return 1, "Rest"
        elif 61 <= heart_rate <= 90:
            return 2, "Light activity"
        elif 91 <= heart_rate <= 110:
            return 3, "Moderate activity"
        elif 111 <= heart_rate <= 130:
            return 4, "Intense activity"
        else:
            return 5, "Maximum effort"
