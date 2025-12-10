import asyncio
import aiohttp
import json
import logging
import os
from typing import Callable, Optional
from src.ingestion.filter import FilterManager

logger = logging.getLogger(__name__)

class HomeAssistantClient:
    """
    Async WebSocket client for Home Assistant.
    Maintains persistent connection and subscribes to events.
    """
    def __init__(self, supervisor_url: str, token: str, on_message: Callable[[dict], None], filter_manager: FilterManager = None):
        self.url = supervisor_url
        self.token = token
        self.on_message_callback = on_message
        self.filter_manager = filter_manager
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._shutdown = False
        self.message_id = 1

    async def connect(self):
        """Main loop: connect, authenticate, listen, retry."""
        retry_delay = 1
        
        while not self._shutdown:
            try:
                logger.info(f"Connecting to {self.url}...")
                headers = {"Authorization": f"Bearer {self.token}"}
                logger.debug("Connecting with headers.")
                async with aiohttp.ClientSession() as session:
                    self.session = session
                    async with session.ws_connect(self.url, headers=headers) as ws:
                        self.ws = ws
                        logger.info("Connected.")
                        retry_delay = 1 # Reset backoff on successful connection
                        
                        await self._handle_messages()
                        
            except (aiohttp.ClientError, ConnectionError) as e:
                logger.warning(f"Connection lost/failed: {e}")
            except Exception as e:
                logger.exception("Unexpected error in WebSocket loop")
            finally:
                if not self._shutdown:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 60)

    async def _handle_messages(self):
        """Process incoming WebSocket messages."""
        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                await self._process_frame(data)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error("WebSocket connection closed with error")
                break

    async def _process_frame(self, data: dict):
        """Handle protocol specific messages (auth, events)."""
        msg_type = data.get("type")
        
        if msg_type == "auth_required":
            logger.info("Auth required. Sending token.")
            await self.ws.send_json({
                "type": "auth",
                "access_token": self.token
            })
            
        elif msg_type == "auth_ok":
            logger.info("Authentication successful.")
            await self._subscribe_events()
            
        elif msg_type == "auth_invalid":
            logger.error("Authentication failed! Check token.")
            # Fatal error, but for robustness we might retry or exit. 
            # Here we just shutdown to avoid Auth loop.
            # self._shutdown = True 
            
        elif msg_type == "event":
            event_data = data.get("event", {})
            entity_id = event_data.get("data", {}).get("entity_id")
            
            # Apply filter if set
            if self.filter_manager and entity_id:
                if not self.filter_manager.should_process(entity_id):
                    return # Skip this event
            
            if self.on_message_callback:
                # Dispatch to callback (non-blocking if possible)
                asyncio.create_task(self._safe_callback(data))
                
        else:
            # Handle command results etc.
            pass

    async def _safe_callback(self, data):
        try:
            self.on_message_callback(data)
        except Exception as e:
            logger.error(f"Error in message callback: {e}")

    async def _subscribe_events(self):
        """Subscribe to necessary event streams."""
        # Subscribe to state_changed
        await self._send_command("subscribe_events", event_type="state_changed")
        # Subscribe to raw knx_events
        await self._send_command("subscribe_events", event_type="knx_event")
        logger.info("Subscribed to state_changed and knx_event.")

    async def _send_command(self, type_str: str, **kwargs):
        """Send a JSON command with monotonic ID."""
        start_id = self.message_id
        self.message_id += 1
        payload = {"id": start_id, "type": type_str, **kwargs}
        await self.ws.send_json(payload)

    async def close(self):
        self._shutdown = True
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()

if __name__ == "__main__":
    # Simple smoke test (wont run without a real server)
    pass
