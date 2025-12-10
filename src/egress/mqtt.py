import json
import logging
import threading
import time
import socket
import ssl
import paho.mqtt.client as mqtt
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MQTTEgress:
    """
    Handles MQTT communication to the central broker.
    Supports TLS, LWT, and Heartbeats.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client_id = config.get("client_id", "default_client")
        self.site_id = config.get("site_id", "default_site")
        
        self.broker = config.get("mqtt_broker", "localhost")
        self.port = config.get("mqtt_port", 1883)
        self.username = config.get("mqtt_username")
        self.password = config.get("mqtt_password")
        self.use_tls = config.get("mqtt_use_tls", False)

        # Setup Client
        self.client = mqtt.Client(client_id=f"{self.client_id}-{self.site_id}-{int(time.time())}")
        
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        if self.use_tls:
            logger.info("Enabling TLS for MQTT connection")
            self.client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2)
            self.client.tls_insecure_set(False)

        # LWT
        lwt_topic = f"knx-monitor/{self.client_id}/{self.site_id}/system/status"
        self.client.will_set(lwt_topic, payload=json.dumps({"status": "offline", "reason": "unexpected_disconnect"}), retain=True)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        self._shutdown = False

    def start(self):
        """Start the MQTT loop and heartbeat thread."""
        try:
            logger.info(f"Connecting to MQTT Broker {self.broker}:{self.port}")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            
            # Start Heartbeat
            self.hb_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.hb_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")

    def stop(self):
        self._shutdown = True
        self.client.loop_stop()
        self.client.disconnect()

    def publish(self, metric_type: str, entity_id: str, payload: Dict[str, Any]):
        """
        Publish enriched telemetry.
        Topic: knx-monitor/{client}/{site}/{type}/{id}
        """
        topic = f"knx-monitor/{self.client_id}/{self.site_id}/{metric_type}/{entity_id}"
        
        # Enrich payload if needed, generally payload already has timestamp
        try:
            json_payload = json.dumps(payload)
            self.client.publish(topic, json_payload, qos=1)
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT Broker!")
            # Publish online status
            topic = f"knx-monitor/{self.client_id}/{self.site_id}/system/status"
            self.client.publish(topic, json.dumps({"status": "online", "uptime": time.time()}), retain=True)
        else:
            logger.error(f"Failed to connect to MQTT Broker, return code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning("Unexpected disconnection from MQTT Broker")

    def _heartbeat_loop(self):
        """Send synthetic heartbeat every 60s."""
        topic = f"knx-monitor/{self.client_id}/{self.site_id}/system/heartbeat"
        while not self._shutdown:
            try:
                payload = {
                    "online": True,
                    "timestamp": time.time(),
                    "memory": "TBD" # Could add psutil here later
                }
                self.client.publish(topic, json.dumps(payload), qos=0)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
            
            time.sleep(60)
