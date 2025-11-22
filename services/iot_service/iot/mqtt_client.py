import paho.mqtt.client as mqtt
import json
import logging
from django.conf import settings
from .models import Device, SensorData

logger = logging.getLogger(__name__)

class MQTTClient:
    def __init__(self):
        self.client = None
        self.broker = settings.MQTT_BROKER
        self.port = settings.MQTT_PORT
        self.topic = settings.MQTT_TOPIC
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Connected to MQTT Broker at {self.broker}:{self.port}")
            client.subscribe(self.topic)
            logger.info(f"Subscribed to topic: {self.topic}")
        else:
            logger.error(f"Failed to connect to MQTT Broker, return code {rc}")
    
    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            logger.debug(f"Received message on {msg.topic}: {payload}")
            
            # Extract data from payload
            device_id = payload.get('device_id', 'smartwatch_1')
            heart_rate = payload.get('heart_rate')
            zone = payload.get('zone')
            timestamp = payload.get('timestamp')
            ecg_samples = payload.get('ecg_samples', [])
            
            # Convert timestamp to datetime if it's a string
            from django.utils import timezone
            from datetime import datetime, timezone as dt_timezone
            
            if isinstance(timestamp, str):
                timestamp_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif isinstance(timestamp, (int, float)):
                timestamp_dt = datetime.fromtimestamp(timestamp, tz=dt_timezone.utc)
            else:
                timestamp_dt = timezone.now()
            
            # Get or create device
            device, created = Device.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_type': 'smartwatch',
                    'name': f'Smartwatch {device_id}',
                    'is_active': True
                }
            )
            
            if created:
                logger.info(f"Created new device: {device_id}")
            
            # Store sensor data
            sensor_data = SensorData.objects.create(
                device=device,
                heart_rate=heart_rate,
                zone=zone,
                timestamp=timestamp_dt,
                ecg_samples=json.dumps(ecg_samples) if ecg_samples else None
            )
            
            logger.info(f"Stored sensor data: HR={heart_rate}, Zone={zone}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection. Will auto-reconnect. RC: {rc}")
    
    def start(self):
        """Start the MQTT client"""
        self.client = mqtt.Client(client_id="iot_service_client")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            logger.info("MQTT client started")
        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")
    
    def stop(self):
        """Stop the MQTT client"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT client stopped")

# Global MQTT client instance
mqtt_client = MQTTClient()
