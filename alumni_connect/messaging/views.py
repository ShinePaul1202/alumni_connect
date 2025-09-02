from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages as flash_messages
from django.utils import timezone

from .models import Conversation, ConversationParticipant, Message
from core.models import Connection

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
    Find a non-group conversation that has exactly these two participants.
    If none, create it and add both participants.
    """
    conversation = (
        Conversation.objects
        .filter(is_group=False, participants=user1)
        .filter(participants=user2)
        .annotate(pcount=Count("participants"))
        .filter(pcount=2)
        .first()
    )
    if conversation:
        return conversation

    conversation = Conversation.objects.create(is_group=False)
    ConversationParticipant.objects.create(conversation=conversation, user=user1)
    ConversationParticipant.objects.create(conversation=conversation, user=user2)
    return conversation


@login_required
def inbox(request):
    """Show list of conversations for the logged-in user."""
    if not user_is_verified(request.user):
        flash_messages.error(request, "Messaging is available after your profile is verified.")
        return redirect("core:account_settings")  # adjust if you use a different url name

    convs = request.user.conversations.all().order_by("-updated_at")
    # Build a small list so template can easily access "other" and "last"
    conv_list = []
    for c in convs:
        other = c.participants.exclude(pk=request.user.pk).first()
        last = c.last_message()
        conv_list.append({"conversation": c, "other": other, "last": last})
    return render(request, "messaging/inbox.html", {"conversations": conv_list})


@login_required
def chat_with_user(request, user_id):
    """
    Checks for an accepted connection first, then opens or creates a 1:1
    conversation with the given user id, then redirects to conversation view.
    """
    other = get_object_or_404(User, pk=user_id)
    if other == request.user:
        return redirect("messaging:inbox")

    # --- GATEKEEPING LOGIC ---
    connection = Connection.objects.filter(
        status=Connection.Status.ACCEPTED
    ).filter(
        (Q(sender=request.user, receiver=other) | Q(sender=other, receiver=request.user))
    ).first()

    if not connection:
        flash_messages.error(request, "You must be connected with this user to send a message.")
        # Redirect to the user's profile page, or wherever is appropriate
        return redirect("core:profile_page", user_id=user_id)
    # --- END GATEKEEPING LOGIC ---

    # If the check passes, proceed as before
    convo = _get_or_create_1to1_conversation(request.user, other)
    return redirect("messaging:conversation", pk=convo.pk)


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
    return render(
        request,
        "messaging/conversation.html",
        {"conversation": convo, "messages": messages_qs, "other_user": other},
    )


@login_required
def send_message_ajax(request, pk):
    """AJAX endpoint: create a new message in conversation pk (POST)."""
    if request.method != "POST":
        return HttpResponseForbidden()

    convo = get_object_or_404(Conversation, pk=pk, participants=request.user)
    text = (request.POST.get("text") or "").strip()
    if not text:
        return JsonResponse({"ok": False, "error": "empty"})

    msg = Message.objects.create(conversation=convo, sender=request.user, text=text)
    convo.save()  # update updated_at
    return JsonResponse(
        {
            "ok": True,
            "id": msg.id,
            "text": msg.text,
            "sender_id": msg.sender_id,
            "sender_username": msg.sender.username,
            "created": msg.created_at.strftime("%H:%M"),
        }
    )


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