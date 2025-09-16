from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Conversation(models.Model):
    unique_key = models.CharField(max_length=50, unique=True, null=True, blank=True)
    is_group = models.BooleanField(default=False)
    participants = models.ManyToManyField(User, through="ConversationParticipant", related_name="conversations")
    updated_at = models.DateTimeField(auto_now=True)

    # --- FIX: Indent this method ---
    def __str__(self):
        if self.unique_key:
            return f"1-on-1 Conversation ({self.unique_key})"
        return f"Group Conversation {self.pk}"

    # --- FIX: Indent this method too ---
    def last_message(self):
        return self.messages.order_by("-created_at").first()

class ConversationParticipant(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conversation_memberships")
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("conversation", "user")

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
        # Removed null=True and blank=True for better data integrity
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    
    # MODIFICATION: Text is now optional
    text = models.TextField(blank=True)
    
    # NEW FIELD: To store uploaded files
    file = models.FileField(upload_to='message_files/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]
