# messaging/consumers.py
import json
from django.contrib.auth import get_user_model
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

from .models import Message, Conversation, ReadReceipt, DeliveryReceipt
from core.models import Profile

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return

        self.conversation_id = self.scope['url_route']['kwargs']['pk']
        self.room_group_name = f'chat_{self.conversation_id}'
        
        is_participant = await self.is_user_participant(self.user, self.conversation_id)
        if not is_participant:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # 1. Announce your own presence to the group (for others' benefit)
        await self.update_user_status(is_online=True)

        # 2. Get the other user's status and send it directly to yourself
        other_user_status = await self.get_other_participant_status()
        if other_user_status:
            await self.send(text_data=json.dumps({
                'type': 'user_status',
                'user_id': other_user_status['user_id'],
                'is_online': other_user_status['is_online'],
                'last_seen': other_user_status['last_seen'],
            }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name') and self.user.is_authenticated:
            await self.update_user_status(is_online=False)
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'chat_message':
            await self.handle_new_message(data)
        elif message_type == 'delivery_confirmation':
            await self.handle_delivery_confirmation(data)
        elif message_type == 'read_receipt':
            await self.handle_read_receipt(data)

    # === Handler Methods ===
    async def handle_delivery_confirmation(self, data):
        """Handles a delivery confirmation from a client."""
        message_ids = data.get('message_ids', [])
        if not message_ids: return

        await self.create_delivery_receipts(message_ids)
        
        # Broadcast to the group that the messages were delivered
        payload = {
            'type': 'broadcast_message_delivered',
            'message_ids': message_ids,
            'delivered_to_id': self.user.id,
        }
        await self.channel_layer.group_send(self.room_group_name, payload)
    
    async def handle_new_message(self, data):
        message_text = data.get('message', '').strip()
        if not message_text:
            return
        new_message = await self.create_message(message_text)
        payload = {
            'type': 'broadcast_message',
            'message': {
                'id': new_message.id,
                'conversation_id': self.conversation_id,
                'sender_id': self.user.id,
                'sender_username': self.user.username,
                'text': new_message.text,
                'created_at': new_message.created_at.isoformat(),
                'created_at_formatted': new_message.created_at.strftime('%H:%M'),
                'files': []
            }
        }
        await self.channel_layer.group_send(self.room_group_name, payload)

    async def handle_read_receipt(self, data):
        """
        Handles a read receipt from a client.
        Crucially, it also ensures a delivery receipt exists.
        """
        message_ids = data.get('message_ids', [])
        if not message_ids: return

        # This is now the single point of truth for marking messages as read.
        # It creates both delivery and read receipts to ensure consistency.
        await self.create_delivery_receipts(message_ids)
        await self.create_read_receipts(message_ids)
        
        # Broadcast to the group that the messages were read
        payload = {
            'type': 'broadcast_read_receipt',
            'message_ids': message_ids,
            'reader_id': self.user.id,
        }
        await self.channel_layer.group_send(self.room_group_name, payload)

    # === Broadcast Methods (sent to clients) ===

    async def broadcast_message_delivered(self, event):
        """Sends delivery confirmation to the WebSocket client."""
        await self.send(text_data=json.dumps({
            'type': 'message_delivered',
            'message_ids': event['message_ids'],
            'delivered_to_id': event['delivered_to_id'],
        }))

    async def broadcast_message(self, event):
        await self.send(text_data=json.dumps({'type': 'new_message', 'message': event['message']}))

    async def broadcast_user_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user_id': event['user_id'],
            'is_online': event['is_online'],
            'last_seen': event.get('last_seen'),
        }))

    async def broadcast_read_receipt(self, event):
        await self.send(text_data=json.dumps({'type': 'messages_read', 'message_ids': event['message_ids'], 'reader_id': event['reader_id']}))

    async def broadcast_message_deleted(self, event):
        await self.send(text_data=json.dumps({'type': 'message_deleted', 'message_id': event['message_id']}))

    # === DB & Helper Methods ===

    async def update_user_status(self, is_online):
        last_seen_iso = await self.update_profile_last_seen(is_online)
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'broadcast_user_status',
            'user_id': self.user.id,
            'is_online': is_online,
            'last_seen': last_seen_iso,
        })

    @database_sync_to_async
    def create_delivery_receipts(self, message_ids):
        """Creates DeliveryReceipt objects for a list of message IDs."""
        messages = Message.objects.filter(id__in=message_ids).exclude(sender=self.user)
        receipts = [
            DeliveryReceipt(message=msg, user=self.user)
            for msg in messages
            if not DeliveryReceipt.objects.filter(message=msg, user=self.user).exists()
        ]
        DeliveryReceipt.objects.bulk_create(receipts)

    @database_sync_to_async
    def is_user_participant(self, user, conversation_id):
        return Conversation.objects.filter(id=conversation_id, participants=user).exists()

    @database_sync_to_async
    def create_message(self, text):
        """Saves a new message and resurrects the conversation if needed."""
        convo = Conversation.objects.get(id=self.conversation_id)

        # --- ADD THIS RESURRECTION LOGIC ---
        if convo.deleted_by.exists():
            convo.deleted_by.clear()
        # --- END OF ADDITION ---

        msg = Message.objects.create(conversation=convo, sender=self.user, text=text)
        convo.save() # Updates `updated_at` for sorting
        return msg

    @database_sync_to_async
    def create_read_receipts(self, message_ids):
        messages = Message.objects.filter(id__in=message_ids).exclude(sender=self.user)
        receipts = [ReadReceipt(message=msg, user=self.user) for msg in messages if not ReadReceipt.objects.filter(message=msg, user=self.user).exists()]
        ReadReceipt.objects.bulk_create(receipts)

    @database_sync_to_async
    def update_profile_last_seen(self, is_online):
        profile, _ = Profile.objects.get_or_create(user=self.user)
        profile.last_seen = timezone.now()
        profile.save()
        return profile.last_seen.isoformat()
    
    @database_sync_to_async
    def get_other_participant_status(self):
        """Fetches the profile and online status of the other user in the conversation."""
        try:
            # Use prefetch_related for a more efficient query
            conversation = Conversation.objects.prefetch_related('participants__profile').get(id=self.conversation_id)
            other_user = conversation.participants.exclude(id=self.user.id).first()
            if other_user and hasattr(other_user, 'profile'):
                profile = other_user.profile
                return {
                    'user_id': other_user.id,
                    'is_online': profile.is_online(),
                    'last_seen': profile.last_seen.isoformat() if profile.last_seen else None,
                }
        except Conversation.DoesNotExist:
            return None
        return None