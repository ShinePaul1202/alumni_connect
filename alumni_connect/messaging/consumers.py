# messaging/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = f"chat_{self.scope['url_route']['kwargs']['pk']}"
        
        # This is the simplest possible connection logic
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        print(f"--- MINIMAL CONSUMER: Successfully connected and accepted for group {self.room_group_name} ---")

    async def disconnect(self, close_code):
        print(f"--- MINIMAL CONSUMER: Disconnected with code {close_code} ---")
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        # We will just print whatever we receive and not process it
        print(f"--- MINIMAL CONSUMER: Received message: {text_data} ---")

    # This method is required to handle the broadcast from the view
    async def chat_message(self, event):
        # We will just print that we received it from the channel layer
        print(f"--- MINIMAL CONSUMER: Received event from channel layer: {event} ---")
        # And we'll pass it on to the client
        await self.send(text_data=json.dumps(event))