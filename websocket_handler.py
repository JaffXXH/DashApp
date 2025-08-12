# websocket_handler.py
import asyncio
from typing import List, Dict, Any
from dash import Dash
from server_connector import AlertServerConnector

class WebSocketHandler:
    def __init__(self, app: Dash):
        self.app = app
        self.connector = AlertServerConnector("ws://alert-server:8000/ws")
        
    async def start(self):
        """Start the WebSocket connection"""
        await self.connector.connect()
        self.connector.register_callback(self.handle_new_alerts)
        asyncio.create_task(self.connector.listen_for_alerts())
        
    def handle_new_alerts(self, alerts: List[Dict[str, Any]]):
        """Handle incoming alerts and update the Dash app"""
        if not alerts:
            return
            
        @self.app.callback(
            Output("alert-store", "data"),
            Input("dummy-websocket-input", "value"),
            State("alert-store", "data")
        )
        def update_alerts(_, current_data):
            # Merge new alerts with existing ones
            current_ids = {alert["id"] for alert in current_data}
            new_alerts = [alert.dict() for alert in alerts if alert.id not in current_ids]
            return new_alerts + current_data