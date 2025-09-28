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

class MessageFile(models.Model):
    file = models.FileField(upload_to='message_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

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