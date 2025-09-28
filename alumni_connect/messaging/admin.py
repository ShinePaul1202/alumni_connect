# messaging/admin.py
from django.contrib import admin
from .models import Conversation, ConversationParticipant, Message

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    # THE FIX: Removed 'is_group' which no longer exists
    list_display = ("id", "unique_key", "updated_at")
    # THE FIX: Removed 'is_group' from here as well
    list_filter = () 

@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    # THE FIX: Removed 'last_read_at' which no longer exists
    list_display = ("id", "conversation", "user", "joined_at")

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "created_at")
    ordering = ("-created_at",)