from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class IotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'iot'

    def ready(self):
        """Start MQTT client when Django starts"""
        import os
        # Only start MQTT client in the main process (not in reloader)
        if os.environ.get('RUN_MAIN') != 'true':
            return
            
        try:
            from .mqtt_client import mqtt_client
            mqtt_client.start()
            logger.info("MQTT client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MQTT client: {e}")
