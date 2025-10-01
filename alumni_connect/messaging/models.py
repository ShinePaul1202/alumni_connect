# messaging/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Conversation(models.Model):
    unique_key = models.CharField(max_length=50, unique=True, null=True, blank=True)
    participants = models.ManyToManyField(User, through="ConversationParticipant", related_name="conversations")
    updated_at = models.DateTimeField(auto_now=True)

    deleted_by = models.ManyToManyField(User, related_name="deleted_conversations", blank=True)
    
    def last_message(self):
        return self.messages.order_by("-created_at").first()

class ConversationParticipant(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conversation_memberships")
    joined_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # NEW: Link to multiple files
    files = models.ManyToManyField('MessageFile', blank=True, related_name='messages')
    
    class Meta:
        ordering = ["created_at"]

    def is_delivered_to_all(self):
        """Checks if the message has been delivered to all participants except the sender."""
        participants_count = self.conversation.participants.exclude(id=self.sender.id).count()
        return self.delivery_receipts.count() >= participants_count

    def is_read_by_all(self):
        """Checks if the message has been read by all participants except the sender."""
        participants_count = self.conversation.participants.exclude(id=self.sender.id).count()
        return self.receipts.count() >= participants_count

class MessageFile(models.Model):
    file = models.FileField(upload_to='message_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class DeliveryReceipt(models.Model):
    """Tracks when a message is successfully delivered to a user's client."""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='delivery_receipts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_receipts')
    delivered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('message', 'user')

class ReadReceipt(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='receipts')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='receipts')
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('message', 'user')

class Report(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    reason = models.TextField()
    referenced_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)