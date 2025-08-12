# server_connector.py
import json
import asyncio
import websockets
from typing import Callable, List
from models import Alert

class AlertServerConnector:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.callbacks = []
        
    async def connect(self):
        """Connect to the alert server via WebSocket"""
        self.websocket = await websockets.connect(self.server_url)
        
    async def listen_for_alerts(self):
        """Continuously listen for new alerts"""
        try:
            async for message in self.websocket:
                alerts = [Alert(**alert_data) for alert_data in json.loads(message)]
                for callback in self.callbacks:
                    callback(alerts)
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed, attempting to reconnect...")
            await self.connect()
            await self.listen_for_alerts()
            
    def register_callback(self, callback: Callable[[List[Alert]], None]):
        """Register a callback for new alerts"""
        self.callbacks.append(callback)
        
    async def update_alert_status(self, alert_id: str, action: str, user: str, comment: str = None):
        """Send alert status update to server"""
        update = {
            "alert_id": alert_id,
            "action": action,
            "user": user,
            "comment": comment,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.websocket.send(json.dumps(update))