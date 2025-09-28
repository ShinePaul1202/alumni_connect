# messaging/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from django.utils import timezone
from .models import Message, ReadReceipt, Conversation
from core.models import Profile
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # --- PRINT STATEMENT 1: See who is trying to connect ---
        print(f"--- WebSocket connect attempt for user: {self.scope.get('user')} ---")

        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            # --- PRINT STATEMENT 2: Log if the user is not logged in ---
            print("--- REJECTION: User is not authenticated. Closing connection. ---")
            await self.close()
            return

        self.conversation_id = self.scope['url_route']['kwargs']['pk']
        self.room_group_name = f'chat_{self.conversation_id}'

        # --- Security Check: Ensure user is a participant of this conversation ---
        if not await self.is_user_participant():
            # --- PRINT STATEMENT 3: Log if the user is not part of the chat ---
            print(f"--- REJECTION: User '{self.user}' is not a participant of conversation '{self.conversation_id}'. Closing connection. ---")
            await self.close()
            return
        
        # --- PRINT STATEMENT 4: Confirm a successful connection ---
        print(f"--- SUCCESS: User '{self.user}' connected to chat '{self.conversation_id}'. ---")
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Broadcast that this user is now online
        await self.broadcast_user_status(is_online=True)

    async def disconnect(self, close_code):
        # Broadcast that this user is now offline
        await self.broadcast_user_status(is_online=False)
        
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Handles messages sent FROM the client's browser TO the server via WebSocket.
        """
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'mark_as_read':
            await self.mark_messages_as_read(data.get('message_ids', []))

    # --- Handlers for events broadcast FROM the backend TO the group ---

    async def chat_message(self, event):
        """
        Handler for the 'chat_message' type. Sends the new message to the client.
        """
        await self.send(text_data=json.dumps(event))

    async def read_receipt(self, event):
        """
        Handler for the 'read_receipt' type. Sends confirmation to the client
        that messages have been seen.
        """
        await self.send(text_data=json.dumps(event))
        
    async def user_status(self, event):
        """
        Handler for the 'user_status' type. Sends the other user's
        online/offline status to the client.
        """
        await self.send(text_data=json.dumps(event))

    # --- Database Methods (wrapped for async execution) ---

    @database_sync_to_async
    def is_user_participant(self):
        """Checks if the connected user is a valid participant of the conversation."""
        return Conversation.objects.filter(pk=self.conversation_id, participants=self.user).exists()

    @database_sync_to_async
    def broadcast_user_status(self, is_online):
        """Updates the user's Profile and broadcasts their status."""
        Profile.objects.filter(user=self.user).update(last_seen=timezone.now())
        
        # This is an async context, so we can call channel_layer directly
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'is_online': is_online,
                'last_seen': timezone.now().isoformat()
            }
        )

    @database_sync_to_async
    def mark_messages_as_read(self, message_ids):
        """Creates ReadReceipts and broadcasts the update."""
        if not message_ids:
            return
            
        # Find messages that this user has not yet read
        messages_to_mark = Message.objects.filter(
            pk__in=message_ids, 
            conversation_id=self.conversation_id
        ).exclude(receipts__user=self.user)

        receipts = [ReadReceipt(message=msg, user=self.user) for msg in messages_to_mark]
        
        if receipts:
            ReadReceipt.objects.bulk_create(receipts)
            
            # Get the IDs of the messages that were just marked as read
            newly_read_ids = [r.message_id for r in receipts]
            
            # Broadcast the read receipt to the room
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'read_receipt',
                    'reader_id': self.user.id,
                    'message_ids': newly_read_ids
                }
            )