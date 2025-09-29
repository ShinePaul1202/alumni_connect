import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages as flash_messages
from django.utils import timezone
from django.views.decorators.http import require_POST


from .models import Conversation, ConversationParticipant, Message, MessageFile, ReadReceipt
from core.models import Connection, Profile

User = get_user_model()


def user_is_verified(user):
    """Return True only if user has profile and is_verified (and not flagged)."""
    try:
        p = user.profile
        return bool(p.is_verified) and not bool(getattr(p, "fraud_warning", False))
    except Exception:
        # If no profile or error, treat as not verified
        return False


def _get_or_create_1to1_conversation(user1, user2):
    """
    Finds or creates a 1-on-1 conversation using a unique, sorted key.
    This is atomic and prevents race conditions.
    """
    low_id, high_id = min(user1.id, user2.id), max(user1.id, user2.id)
    key = f"{low_id}-{high_id}"

    # THE FIX: The 'defaults' dictionary is now empty because 'is_group' was removed.
    conversation, created = Conversation.objects.get_or_create(
        unique_key=key
    )

    if created:
        ConversationParticipant.objects.create(conversation=conversation, user=user1)
        ConversationParticipant.objects.create(conversation=conversation, user=user2)

    return conversation


@login_required
def inbox(request):
    if not user_is_verified(request.user):
        flash_messages.error(request, "Messaging is available after your profile is verified.")
        return redirect("core:account_settings")

    # --- NEW LOGIC: Check for a filter in the URL ---
    filter_type = request.GET.get('filter')
    
    # Start with all of the user's conversations
    convs = request.user.conversations.all().exclude(deleted_by=request.user).order_by("-updated_at")

    if filter_type == 'students':
        convs = convs.filter(memberships__user__profile__user_type='student')

    conv_list = []
    for c in convs:
        other = c.participants.exclude(pk=request.user.pk).first()
        last = c.last_message()
        last_message_text = "No messages yet"
        if last:
            sender_prefix = "You: " if last.sender == request.user else ""
            last_message_text = f"{sender_prefix}{last.text}"

        conv_list.append({
            "conversation": c, 
            "other": other, 
            "last": last,
            "last_message_text": last_message_text # Pass this new text to the template
        })
    
    profile = get_object_or_404(Profile, user=request.user)
    context = { "conversations": conv_list, "profile": profile, "active_filter": filter_type }
    return render(request, "messaging/inbox.html", context)


@login_required
def chat_with_user(request, user_id):
    """
    Finds or creates a 1:1 conversation and redirects to the main inbox,
    with a query parameter to auto-open the chat via JavaScript.
    """
    other = get_object_or_404(User, pk=user_id)
    if other == request.user:
        return redirect("messaging:inbox")

    connection = Connection.objects.filter(
        status=Connection.Status.ACCEPTED
    ).filter(
        (Q(sender=request.user, receiver=other) | Q(sender=other, receiver=request.user))
    ).first()

    if not connection:
        flash_messages.error(request, "You must be connected with this user to send a message.")
        return redirect("core:profile_page", user_id=user_id)
    
    convo = _get_or_create_1to1_conversation(request.user, other)
    
    # --- THIS IS THE FIX ---
    # "Resurrect" the chat if the current user had previously deleted it.
    if request.user in convo.deleted_by.all():
        convo.deleted_by.remove(request.user)
    # --- End of the fix ---

    inbox_url = reverse('messaging:inbox')
    return redirect(f'{inbox_url}?open_chat={convo.pk}')


@login_required
def conversation_view(request, pk):
    """Render a conversation (chat window)."""
    convo = get_object_or_404(Conversation, pk=pk, participants=request.user)

    if not user_is_verified(request.user):
        flash_messages.error(request, "Messaging is available after your profile is verified.")
        return redirect("core:account_settings")
    
    participant = ConversationParticipant.objects.get(
        conversation=convo,
        user=request.user
    )
    # Update the timestamp to now
    participant.last_read_at = timezone.now()
    participant.save(update_fields=['last_read_at'])

    messages_qs = convo.messages.select_related("sender").all()  # ordered by created_at by model Meta
    other = convo.participants.exclude(pk=request.user.pk).first()
    
    profile = get_object_or_404(Profile, user=request.user)
    context = {
        "conversation": convo,
        "messages": messages_qs,
        "other_user": other,
        "profile": profile, # <-- Add the profile here
    }
    return render(request, "messaging/conversation.html", context)


# messaging/views.py

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Conversation, Message, MessageFile


@require_POST
@login_required
def send_message_ajax(request, pk):
    """
    Saves a single message with text and/or multiple files,
    then broadcasts it via the WebSocket consumer.
    """
    # 1. SECURITY CHECK: Get the conversation and ensure the current user is a participant.
    # This prevents users from sending messages to conversations they don't belong to.
    convo = get_object_or_404(Conversation, pk=pk, participants=request.user)

    # 2. DATA EXTRACTION: Get text and files from the incoming request.
    text = (request.POST.get("text") or "").strip()
    files = request.FILES.getlist('file')

    # 3. VALIDATION: Ensure the message is not empty.
    if not text and not files:
        return JsonResponse({"ok": False, "error": "Message cannot be empty"}, status=400)

    # 4. DATABASE: Create the Message object and link any files.
    # Create the main message object with the text content.
    msg = Message.objects.create(conversation=convo, sender=request.user, text=text)

    # Process and link each uploaded file to the message.
    file_data_list = []
    for f in files:
        # Create a MessageFile instance for each file.
        message_file = MessageFile.objects.create(file=f)
        # Add it to the many-to-many relationship on the message.
        msg.files.add(message_file)
        # Prepare file data for the WebSocket payload.
        file_data_list.append({
            'url': message_file.file.url,
            'name': str(message_file.file.name).split('/')[-1] # Get just the filename
        })

    # 5. UPDATE CONVERSATION: Trigger the `updated_at` field by saving the conversation.
    # This is crucial for sorting the conversation list correctly.
    convo.save()

    # 6. BROADCAST: Send the new message data to the WebSocket group.
    channel_layer = get_channel_layer()

    # The payload dictionary must contain everything the frontend needs to render the message
    # AND update the conversation list.
    payload = {
        'type': 'chat_message',  # This tells the consumer which method to run
        'message': {
            "id": msg.id,
            "conversation_id": pk, # Essential for updating the correct chat in the list
            "sender_id": msg.sender.id,
            "sender_username": msg.sender.username,
            "text": msg.text,
            "created": msg.created_at.strftime("%H:%M"),
            "files": file_data_list, # List of dictionaries for any files
        }
    }

    # Use async_to_sync to call the async group_send method from this sync view.
    async_to_sync(channel_layer.group_send)(
        f'chat_{pk}',  # The group name must match the one in the consumer
        payload
    )

    # 7. RESPONSE: Return a success response to the client's AJAX call.
    return JsonResponse({"ok": True})

@login_required
def fetch_messages(request, pk):
    """
    AJAX endpoint: fetch messages after a given id, ensuring the JSON
    response format is IDENTICAL to the WebSocket broadcast structure.
    """
    convo = get_object_or_404(Conversation, pk=pk, participants=request.user)
    after = int(request.GET.get("after", 0))
    
    # Use prefetch_related for efficiency
    new_messages = convo.messages.select_related("sender").prefetch_related('files').filter(id__gt=after)
    
    # --- THIS IS THE FIX ---
    # We now build the exact same data structure as the send_message_ajax view.
    data = []
    for m in new_messages:
        # Create a list of file data for each message
        file_data_list = []
        for f in m.files.all():
            file_data_list.append({
                'url': f.file.url,
                'name': str(f.file.name).split('/')[-1]
            })

        # Append the message with the 'files' array, just like the WebSocket consumer expects
        data.append({
            "id": m.id,
            "text": m.text,
            "sender_id": m.sender_id,
            "sender_username": m.sender.username,
            "created": m.created_at.strftime("%H:%M"),
            "files": file_data_list, # <-- This now matches the WebSocket structure
        })

    return JsonResponse({"ok": True, "messages": data})

@login_required
def fetch_conversation_html(request, pk):
    """
    AJAX endpoint: Fetches the rendered HTML for a conversation window.
    """
    convo = get_object_or_404(Conversation, pk=pk, participants=request.user)
    
    # --- THIS IS THE FIX ---
    # We have removed the old, incorrect code that was trying to save to 'last_read_at'.
    # The new read receipt logic will be handled by the ReadReceipt model when we implement it.
    
    messages_qs = convo.messages.select_related("sender").prefetch_related('files').all()
    other = convo.participants.exclude(pk=request.user.pk).first()
    
    context = {
        "conversation": convo,
        "messages": messages_qs,
        "other_user": other,
    }
    return render(request, "messaging/_chat_window.html", context)

@require_POST
@login_required
def leave_conversation_ajax(request, pk):
    """
    Adds the current user to the 'deleted_by' list for a conversation.
    If both participants have deleted it, the conversation is permanently deleted.
    """
    try:
        convo = get_object_or_404(Conversation, pk=pk, participants=request.user)
        
        # Add the current user to the list of users who have deleted this chat
        convo.deleted_by.add(request.user)
        
        # --- NEW LOGIC: Check if it should be permanently deleted ---
        if convo.deleted_by.count() >= convo.participants.count():
            # If everyone has "deleted" the chat, remove it for real
            convo.delete()
        
        return JsonResponse({"ok": True})

    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@require_POST
@login_required
def delete_message_ajax(request, pk):
    """AJAX endpoint: delete a message by its pk."""
    try:
        # Find the message
        message = get_object_or_404(Message, pk=pk)
        
        # SECURITY CHECK: Ensure the user deleting the message is the original sender.
        if request.user != message.sender:
            return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
            
        # If the check passes, delete the message
        message.delete()
        
        return JsonResponse({"ok": True})

    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
    
@require_POST
@login_required
def delete_messages_bulk_ajax(request):
    """AJAX endpoint: delete a list of messages by their PKs."""
    try:
        # Get the list of message IDs from the POST request body
        data = json.loads(request.body)
        message_ids = data.get('ids', [])

        if not message_ids:
            return JsonResponse({"ok": False, "error": "No message IDs provided."}, status=400)

        # SECURITY: This is the most important part.
        # This query ensures that a user can ONLY delete messages that
        # they are the sender of. It's impossible to delete someone else's messages.
        messages_to_delete = Message.objects.filter(
            pk__in=message_ids,
            sender=request.user
        )
        
        # Get the count before deleting for the response
        count, _ = messages_to_delete.delete()

        return JsonResponse({"ok": True, "deleted_count": count})

    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON."}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)