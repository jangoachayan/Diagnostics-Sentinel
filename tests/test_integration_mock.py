import asyncio
import unittest
from aiohttp import web
from mock.supervisor import websocket_handler
from src.ingestion.websocket_client import HomeAssistantClient
import logging

# Mute logs for test clarity
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("src.ingestion.websocket_client").setLevel(logging.DEBUG)

class TestIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Start Mock Server
        self.app = web.Application()
        self.app.add_routes([web.get('/core/websocket', websocket_handler)])
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, 'localhost', 8124)
        await self.site.start()
        
        self.received_messages = []

    async def asyncTearDown(self):
        await self.runner.cleanup()

    def callback(self, data):
        self.received_messages.append(data)

    async def test_connect_auth_subscribe(self):
        client = HomeAssistantClient(
            supervisor_url="ws://localhost:8124/core/websocket",
            token="fake_token",
            on_message=self.callback
        )
        
        # Run client connect in background, but we need to cancel it eventually
        # because it has an infinite loop
        task = asyncio.create_task(client.connect())
        
        # Give it time to connect, auth, and receive an event
        await asyncio.sleep(3)
        
        # Check if we got at least one event (mock supervisor sends one every 0.5-2.0s)
        await client.close()
        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.TimeoutError:
            pass # Expected, task was cancelled or finished
        except Exception:
            pass
            
        print(f"Received {len(self.received_messages)} messages")
        # Validation:
        # 1. We expect client to have subscribed (logs would show)
        # 2. We expect to receive at least 1 mock event
        self.assertGreater(len(self.received_messages), 0, "Should have received events from mock server")
        
if __name__ == "__main__":
    unittest.main()
