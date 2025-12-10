import asyncio
import json
import logging
import os
import signal
import sys
from typing import Dict, Any

from src.ingestion.websocket_client import HomeAssistantClient
from src.ingestion.filter import FilterManager
from src.egress.mqtt import MQTTEgress
from src.kernel.math_engine import ZScoreEngine, SolarDiagnostic, LinearDiagnostic

# Configure Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("KNXSentinel")

# Global State
z_engines: Dict[str, ZScoreEngine] = {}
hvac_engines: Dict[str, LinearDiagnostic] = {}

def load_options() -> Dict[str, Any]:
    """Load options from /data/options.json or env vars."""
    options_path = "/data/options.json"
    if os.path.exists(options_path):
        try:
            with open(options_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load options: {e}")
            return {}
    return {
        "client_id": os.environ.get("CLIENT_ID", "dev_client"),
        "site_id": os.environ.get("SITE_ID", "dev_site"),
        "mqtt_broker": os.environ.get("MQTT_BROKER", "localhost"),
        "mqtt_port": int(os.environ.get("MQTT_PORT", 1883)),
        "target_entities": ["sensor.*", "input_boolean.*"]
    }

def get_supervisor_token() -> str:
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        logger.warning("SUPERVISOR_TOKEN not found! Using 'fake_token' for dev.")
        return "fake_token"
    return token

def handle_event(event: dict, mqtt: MQTTEgress):
    """Callback for incoming HA events."""
    event_type = event.get("event", {}).get("event_type")
    data = event.get("event", {}).get("data", {})
    entity_id = data.get("entity_id")
    
    if event_type == "state_changed":
        new_state = data.get("new_state", {})
        if not new_state: 
            return
            
        try:
            state_val = float(new_state.get("state"))
            
            # 1. Z-Score Analysis
            if entity_id not in z_engines:
                z_engines[entity_id] = ZScoreEngine()
            
            analysis = z_engines[entity_id].process(state_val)
            
            # 2. Enrich Payload
            payload = {
                "value": state_val,
                "timestamp": new_state.get("last_updated"),
                "attributes": new_state.get("attributes"),
                "analysis": analysis
            }
            
            # 3. Publish
            mqtt.publish("telemetry", entity_id, payload)
            
        except ValueError:
            # Non-numeric state (string), just pass through or ignore
            # But maybe we want to log it as status
            pass
            
    elif event_type == "knx_event":
        # Raw KNX Event
        payload = {
            "timestamp": event.get("event", {}).get("time_fired"),
            "data": data
        }
        mqtt.publish("raw", "knx_bus", payload)

async def main():
    logger.info("Starting KNX Sentinel Agent...")
    
    # 1. Configuration
    options = load_options()
    token = get_supervisor_token()
    supervisor_url = "ws://supervisor/core/websocket"
    
    # 2. Components
    filter_mgr = FilterManager(options.get("target_entities", []))
    mqtt_client = MQTTEgress(options)
    
    # 3. Main Logic Callback
    def on_message(msg):
        if msg.get("type") == "event":
            handle_event(msg, mqtt_client)

    ha_client = HomeAssistantClient(
        supervisor_url=supervisor_url, 
        token=token, 
        on_message=on_message,
        filter_manager=filter_mgr
    )
    
    # 4. Start Services
    mqtt_client.start()
    
    # Graceful Shutdown
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    
    def signal_handler():
        logger.info("Shutdown signal received")
        stop_event.set()

    # Register signal handlers if not Windows (for dev) or handle properly
    if sys.platform != "win32":
        loop.add_signal_handler(signal.SIGTERM, signal_handler)
        loop.add_signal_handler(signal.SIGINT, signal_handler)
    
    # 5. Connect and Run
    task = asyncio.create_task(ha_client.connect())
    
    try:
        # If on windows/local dev, use simple sleep loop to wait for ctrl-c if logic above fails
        if sys.platform == "win32":
             while not stop_event.is_set():
                await asyncio.sleep(1)
        else:
             await stop_event.wait()
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Stopping services...")
        await ha_client.close()
        mqtt_client.stop()
        logger.info("Goodbye.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
