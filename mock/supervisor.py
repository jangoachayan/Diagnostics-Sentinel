import asyncio
import aiohttp
from aiohttp import web
import json
import logging
import random
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MockSupervisor")

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    logger.info("Client connected")

    # 1. Auth Flow
    # Send auth_required
    await ws.send_json({"type": "auth_required", "ha_version": "2023.12.0"})
    
    # Wait for auth response
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            data = json.loads(msg.data)
            if data.get("type") == "auth":
                logger.info(f"Received auth token: {data.get('access_token')}")
                await ws.send_json({"type": "auth_ok", "ha_version": "2023.12.0"})
                # Start event loop after auth
                asyncio.create_task(event_generator(ws))
                break 
        elif msg.type == aiohttp.WSMsgType.ERROR:
            logger.error(f"ws connection closed with exception {ws.exception()}")

    # 2. Main Loop (process subscriptions etc)
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            data = json.loads(msg.data)
            logger.info(f"Received command: {data}")
            if data.get("type") == "subscribe_events":
                await ws.send_json({
                    "id": data.get("id"),
                    "type": "result",
                    "success": True,
                    "result": None
                })
        elif msg.type == aiohttp.WSMsgType.ERROR:
            logger.error("ws connection closed with exception %s", ws.exception())

    logger.info("Client disconnected")
    return ws

async def event_generator(ws):
    """Generates synthetic events."""
    try:
        while not ws.closed:
            # Randomly decide to send an event
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Simulate state_changed
            event_data = {
                "type": "event",
                "event": {
                    "event_type": "state_changed",
                    "data": {
                        "entity_id": "sensor.voltage_L1",
                        "new_state": {
                            "state": str(random.randint(220, 240)),
                            "attributes": {},
                            "last_changed": datetime.datetime.now().isoformat()
                        },
                        "old_state": None
                    },
                    "origin": "LOCAL",
                    "time_fired": datetime.datetime.now().isoformat(),
                    "context": {"id": "mock_context_id"}
                }
            }
            logger.info("Sending mock event...")
            await ws.send_json(event_data)
            
    except Exception as e:
        logger.error(f"Event generator error: {e}")

async def start_server():
    app = web.Application()
    app.add_routes([web.get('/core/websocket', websocket_handler)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8123)
    logger.info("Starting Mock Supervisor on ws://localhost:8123/core/websocket")
    await site.start()
    
    # Keep running
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        pass
