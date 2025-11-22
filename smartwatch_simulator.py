#!/usr/bin/env python3
import os
import time
import json
import numpy as np
import paho.mqtt.client as mqtt
from ecg_processor import ECGProcessor
import argparse
import signal
import sys
import random
import config

class SmartWatchSimulator:
    def __init__(self, broker=config.MQTT_BROKER, port=config.MQTT_PORT, qos=config.MQTT_QOS, 
                 base_path=config.BASE_PATH, session=config.DEFAULT_SESSION, participant=config.DEFAULT_PARTICIPANT, 
                 topic_prefix=config.MQTT_TOPIC_PREFIX, data_interval=config.DEFAULT_DATA_INTERVAL, 
                 loop_forever=config.DEFAULT_LOOP_FOREVER, max_videos=config.DEFAULT_MAX_VIDEOS, 
                 random_participants=config.DEFAULT_RANDOM_PARTICIPANTS):
        """
        Initialize the smartwatch simulator.
        
        Args:
            broker (str): MQTT broker address
            port (int): MQTT broker port
            qos (int): MQTT QoS level (0, 1, or 2)
            base_path (str): Path to the ECG dataset
            session (int): Session number to use from the dataset
            participant (int): Participant number to use from the dataset
            topic_prefix (str): Topic prefix for MQTT messages
            data_interval (float): Time interval between data points in seconds
            loop_forever (bool): Whether to loop the data continuously
            max_videos (int): Maximum number of videos to include from each participant
            random_participants (bool): Whether to randomly select participants for continuous data
        """
        self.broker = broker
        self.port = port
        self.qos = qos
        self.base_path = base_path
        self.session = session
        self.participant = participant
        self.topic_prefix = topic_prefix
        self.data_interval = data_interval
        self.loop_forever = loop_forever
        self.max_videos = max_videos
        self.random_participants = random_participants
        
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        
        self.processor = ECGProcessor(sampling_rate=128)
        
        self.running = False
        
    def on_connect(self, client, userdata, flags, rc):
        """
        Callback function for MQTT connection.
        
        Args:
            client: MQTT client instance
            userdata: User data passed to client
            flags: Connection flags
            rc (int): Return code from connection attempt
        """
        if rc == 0:
            print(f"Connected to MQTT broker at {self.broker}:{self.port}")
            status = {
                "status": "connected",
                "timestamp": time.time()
            }
            self.client.publish(f"{self.topic_prefix}/status", json.dumps(status), qos=self.qos)
        else:
            print(f"Failed to connect to MQTT broker, return code: {rc}")
    
    def load_data(self, session=None, participant=None):
        """
        Load ECG data for the simulation.
        
        Args:
            session (int): Optional override for session number
            participant (int): Optional override for participant number
            
        Returns:
            bool: True if data loaded successfully, False otherwise
        """
        session = session if session is not None else self.session
        participant = participant if participant is not None else self.participant
        
        print(f"Loading data for session {session}, participant {participant}")
        success = self.processor.load_participant_data(self.base_path, session, participant, max_videos=self.max_videos)
        
        if success:
            print(f"Successfully loaded {len(self.processor.source_files)} files")
            print(f"Source files: {', '.join(self.processor.source_files)}")
            return True
        return False
    
    def get_available_participants(self):
        """
        Get list of available participants based on folder structure.
        
        Returns:
            list: Sorted list of participant IDs available in the dataset
        """
        participants = set()
        ecg_path = os.path.join(self.base_path, "Raw Data", "Multimodal", "ECG")
        
        for filename in os.listdir(ecg_path):
            if filename.lower().startswith(f"ecgdata_s{self.session}p"):
                try:
                    p_str = filename.lower().split(f"s{self.session}p")[1].split("v")[0]
                    participants.add(int(p_str))
                except (IndexError, ValueError):
                    continue
        
        return sorted(list(participants))
    
    def start(self):
        """
        Start the simulation.
        
        Returns:
            bool: True if simulation completes successfully, False otherwise
        """
        try:
            self.client.connect(self.broker, self.port)
            self.client.loop_start()
        except Exception as e:
            print(f"Error connecting to MQTT broker: {e}")
            return False
        
        self.running = True
        
        try:
            if self.random_participants and self.loop_forever:
                available_participants = self.get_available_participants()
                if not available_participants:
                    print(f"No participants found for session {self.session}")
                    return False
                
                print(f"Available participants for session {self.session}: {available_participants}")
                
                while self.running:
                    participant = random.choice(available_participants)
                    print(f"Selected participant: {participant}")
                    
                    if not self.process_and_send_data(participant=participant):
                        print(f"Failed to process data for participant {participant}")
                    
                    if not self.running:
                        break
            else:
                while self.running:
                    if not self.process_and_send_data():
                        print("Failed to process data")
                        return False
                    
                    if not self.loop_forever or not self.running:
                        break
                        
            print("Simulation completed")
                
        except KeyboardInterrupt:
            print("\nSimulation interrupted by user")
        finally:
            self.stop()
            
        return True
    
    def process_and_send_data(self, session=None, participant=None):
        """
        Process and send data for a specific session and participant.
        
        Args:
            session (int): Optional override for session number
            participant (int): Optional override for participant number
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.load_data(session, participant):
            return False
        
        self.processor.calculate_heart_rate(window_seconds=3)
        if not self.processor.heart_rates:
            print("Failed to calculate heart rates")
            return False
            
        # Use raw ECG data directly without preprocessing
        ecg_data = self.processor.ecg_data
        if ecg_data is None:
            print("No ECG data available")
            return False
            
        print(f"Streaming {len(self.processor.heart_rates)} seconds of data")
        
        for i in range(len(self.processor.heart_rates)):
            if not self.running:
                return False
                
            heart_rate = self.processor.heart_rates[i]
            
            start_idx = i * self.processor.sampling_rate
            end_idx = start_idx + self.processor.sampling_rate
            if end_idx <= len(ecg_data):
                ecg_samples = ecg_data[start_idx:end_idx].tolist()
                
                zone = self.get_heart_rate_zone(heart_rate)
                
                payload = {
                    "timestamp": time.time(),
                    "heart_rate": heart_rate,
                    "zone": zone,
                    "ecg_samples": ecg_samples,
                    "source": self.processor.source_files[0] if self.processor.source_files else "unknown",
                    "participant": participant if participant is not None else self.participant
                }
                
                self.publish_data(payload)
                
                print(f"Time: {i}s | Heart Rate: {heart_rate} BPM | Zone: {zone}")
                
                time.sleep(self.data_interval)
        
        return True
    
    def get_heart_rate_zone(self, heart_rate):
        """
        Determine the heart rate zone based on heart rate value.
        
        Zones:
        0: Below normal (< 40 BPM)
        1: Rest (40-60 BPM)
        2: Light activity (61-90 BPM)
        3: Moderate activity (91-110 BPM)
        4: Intense activity (111-130 BPM)
        5: Maximum effort (131+ BPM)
        
        Args:
            heart_rate (int): Heart rate in BPM
            
        Returns:
            int: Heart rate zone (0-5)
        """
        if heart_rate < 40:
            return 0
        elif heart_rate <= 60:
            return 1
        elif heart_rate <= 90:
            return 2
        elif heart_rate <= 110:
            return 3
        elif heart_rate <= 130:
            return 4
        else:
            return 5
    
    def publish_data(self, payload):
        """
        Publish data to MQTT broker.
        
        Args:
            payload (dict): Data payload to publish
        """
        message = json.dumps(payload)
        self.client.publish(f"{self.topic_prefix}/data", message, qos=self.qos)
    
    def stop(self):
        """Stop the simulation and disconnect from MQTT broker."""
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
        print("Disconnected from MQTT broker")


def signal_handler(sig, frame):
    """
    Signal handler for graceful termination.
    
    Args:
        sig: Signal number
        frame: Current stack frame
    """
    print("\nReceived signal to terminate")
    if simulator:
        simulator.stop()
    sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smartwatch ECG Simulator")
    parser.add_argument("--broker", default="localhost", help="MQTT broker address")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--qos", type=int, default=0, choices=[0, 1, 2], help="MQTT QoS level")
    parser.add_argument("--session", type=int, default=1, help="Session number from the dataset (default: 1)")
    parser.add_argument("--participant", type=int, default=1, help="Participant number from the dataset (default: 1)")
    parser.add_argument("--topic", default="smartwatch", help="MQTT topic prefix")
    parser.add_argument("--interval", type=float, default=1.0, help="Data transmission interval in seconds")
    parser.add_argument("--loop", action="store_true", default=True, help="Loop the data continuously (default: True)")
    parser.add_argument("--random", action="store_true", default=False, help="Randomly select participants when looping (default: False)")
    parser.add_argument("--max-videos", type=int, default=1, help="Maximum number of videos to include per participant (default: 1, only v1)")
    
    args = parser.parse_args()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    simulator = SmartWatchSimulator(
        broker=args.broker,
        port=args.port,
        qos=args.qos,
        session=args.session,
        participant=args.participant,
        topic_prefix=args.topic,
        data_interval=args.interval,
        loop_forever=args.loop,
        max_videos=args.max_videos,
        random_participants=args.random
    )
    
    simulator.start()