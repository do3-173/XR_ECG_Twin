#!/usr/bin/env python3
"""
Configuration file for ECG processor and smartwatch simulator
"""

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_QOS = 0
MQTT_TOPIC_PREFIX = "smartwatch"

# Dataset Configuration
BASE_PATH = "dataset"
DEFAULT_SESSION = 1
DEFAULT_PARTICIPANT = 1

# Simulator Configuration
DEFAULT_DATA_INTERVAL = 1.0
DEFAULT_LOOP_FOREVER = False
DEFAULT_MAX_VIDEOS = None
DEFAULT_RANDOM_PARTICIPANTS = False

# ECG Processing Configuration
SAMPLING_RATE = 128

# Heart Rate Zones (BPM)
HEART_RATE_ZONES = {
    0: "Below normal",  # < 40 BPM
    1: "Rest",          # 40-60 BPM
    2: "Light activity", # 61-90 BPM
    3: "Moderate activity", # 91-110 BPM
    4: "Intense activity", # 111-130 BPM
    5: "Maximum effort"    # 131+ BPM
}