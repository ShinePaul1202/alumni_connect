import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages as flash_messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.urls import reverse

from .models import Conversation, ConversationParticipant, Message
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
    # Ensure IDs are always in the same order (lower first)
    low_id, high_id = min(user1.id, user2.id), max(user1.id, user2.id)
    key = f"{low_id}-{high_id}"

    # Use get_or_create for an atomic database operation
    conversation, created = Conversation.objects.get_or_create(
        unique_key=key,
        defaults={'is_group': False}
    )

    # If a new conversation was created, we must add the participants
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
    convs = request.user.conversations.all().order_by("-updated_at")

    # If the filter is 'students', modify the query
    if filter_type == 'students':
        convs = convs.filter(memberships__user__profile__user_type='student')

    conv_list = []
    for c in convs:
        other = c.participants.exclude(pk=request.user.pk).first()
        last = c.last_message()
        conv_list.append({"conversation": c, "other": other, "last": last})
    
    profile = get_object_or_404(Profile, user=request.user)
    
    # --- UPDATED CONTEXT ---
    context = {
        "conversations": conv_list,
        "profile": profile,
        "active_filter": filter_type # Pass the filter to the template
    }
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
    
    # --- THE FIX: Redirect to the inbox with a parameter ---
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


@require_POST
@login_required
def send_message_ajax(request, pk):
    """AJAX endpoint: create new messages (text and/or multiple files)."""
    convo = get_object_or_404(Conversation, pk=pk, participants=request.user)
    text = (request.POST.get("text") or "").strip()
    
    # THE FIX: Use getlist() to handle multiple files
    files = request.FILES.getlist('file')

    if not text and not files:
        return JsonResponse({"ok": False, "error": "empty"})

    created_messages = []

    # Create a message for the text part if it exists
    if text:
        msg = Message.objects.create(conversation=convo, sender=request.user, text=text)
        created_messages.append(msg)

    # Create a separate message for each uploaded file
    for f in files:
        msg = Message.objects.create(conversation=convo, sender=request.user, file=f)
        created_messages.append(msg)
    
    convo.save()  # update updated_at

    # THE FIX: Return a list of all created messages
    response_data = {
        "ok": True,
        "messages": [
            {
                "id": m.id,
                "text": m.text,
                "sender_id": m.sender_id,
                "sender_username": m.sender.username,
                "created": m.created_at.strftime("%H:%M"),
                "file_url": m.file.url if m.file else None,
                "file_name": str(m.file).split('/')[-1] if m.file else None,
            }
            for m in created_messages
        ]
    }
    return JsonResponse(response_data)


@login_required
def fetch_messages(request, pk):
    """
    AJAX endpoint: fetch messages after the given id (GET ?after=123)
    Returns JSON list of new messages.
    """
    convo = get_object_or_404(Conversation, pk=pk, participants=request.user)
    after = int(request.GET.get("after", 0))
    new = convo.messages.select_related("sender").filter(id__gt=after)
    data = [
        {
            "id": m.id,
            "text": m.text,
            "sender_id": m.sender_id,
            "sender_username": m.sender.username,
            "created": m.created_at.strftime("%H:%M"),
        }
        for m in new
    ]
    return JsonResponse({"ok": True, "messages": data})

@login_required
def fetch_conversation_html(request, pk):
    """
    AJAX endpoint: Fetches the rendered HTML for a conversation window.
    """
    convo = get_object_or_404(Conversation, pk=pk, participants=request.user)
    
    # This logic is the same as your original conversation_view
    participant = ConversationParticipant.objects.get(conversation=convo, user=request.user)
    participant.last_read_at = timezone.now()
    participant.save(update_fields=['last_read_at'])

    messages_qs = convo.messages.select_related("sender").all()
    other = convo.participants.exclude(pk=request.user.pk).first()
    
    context = {
        "conversation": convo,
        "messages": messages_qs,
        "other_user": other,
    }
    # The only difference is we render the PARTIAL template
    return render(request, "messaging/_chat_window.html", context)

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