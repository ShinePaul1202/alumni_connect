# C:\project\alumni_connect\core\context_processors.py

from core.models import Notification, Connection
# === ADD IMPORTS for messaging models ===
from messaging.models import Conversation, ConversationParticipant

def global_context(request):
    if request.user.is_authenticated:
        # Count of unread notifications
        unread_notification_count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()

        # Count of pending connection requests
        pending_request_count = Connection.objects.filter(
            receiver=request.user, status=Connection.Status.PENDING
        ).count()

        # === ADD THIS LOGIC TO COUNT UNREAD MESSAGES ===
        unread_message_count = 0
        # Get all conversations the user is a part of
        user_conversations = Conversation.objects.filter(participants=request.user)
        
        for convo in user_conversations:
            try:
                # Get the last time this user read this convo
                participant = ConversationParticipant.objects.get(conversation=convo, user=request.user)
                last_read_time = participant.last_read_at
                
                # Get the last message in the conversation
                last_message = convo.messages.latest('created_at')

                # If a message exists and was sent by someone else
                if last_message and last_message.sender != request.user:
                    # If the user has never read it, or the last message is newer than their last read time
                    if last_read_time is None or last_message.created_at > last_read_time:
                        unread_message_count += 1
            except (ConversationParticipant.DoesNotExist, Exception):
                # Handle cases with no messages or other errors gracefully
                continue
        # === END OF MESSAGE COUNTING LOGIC ===

        return {
            'unread_notification_count': unread_notification_count,
            'pending_request_count': pending_request_count,
            'unread_message_count': unread_message_count, # <-- ADD to context
        }
        
    return {}