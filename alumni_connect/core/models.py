from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q


class Profile(models.Model):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('alumni', 'Alumni'),
    ]

    # Link to the User model
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # --- Profile Picture and Bio ---
    avatar = models.ImageField(default='avatars/default_avatar.png', upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    full_name = models.CharField(max_length=150)

    # Existing profile fields
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    department = models.CharField(max_length=100)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    has_seen_verification_message = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    # This field will store any warnings issued by an admin.
    fraud_warning = models.TextField(blank=True, null=True)

    has_edited_critical_details = models.BooleanField(
        default=False, 
        help_text="Tracks if the user has used their one-time edit for critical details."
    )
    
    # Current Job Info
    currently_employed = models.BooleanField(default=False)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    
    # Past Job Info
    had_past_job = models.BooleanField(default=False)
    past_job_title = models.CharField(max_length=100, blank=True, null=True)
    past_company_name = models.CharField(max_length=100, blank=True, null=True)

    # Notification settings
    email_on_connection_accepted = models.BooleanField(
        default=True, 
        help_text="Send an email when someone accepts your connection request."
    )
    
    def __str__(self):
        return f'{self.user.username} Profile'

class Connection(models.Model):
    """
    Represents a connection request and its status between two users.
    'sender' sends the request to the 'receiver'.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        # We will simply delete declined requests for cleanliness

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_connections'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_connections'
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Ensures a user can't send multiple requests to the same person
        unique_together = ('sender', 'receiver')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username} ({self.get_status_display()})"
    
class Notification(models.Model):
    # The user who will receive the notification
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    # The user who triggered the notification (optional)
    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='+', # We don't need a reverse relationship
        null=True, blank=True
    )
    # The main message (e.g., "accepted your connection request")
    verb = models.CharField(max_length=255)
    # A link to the relevant object (e.g., the actor's profile)
    link = models.URLField(blank=True, null=True)
    # Read/unread status
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.actor.username} {self.verb}"
    
class SearchHistory(models.Model):
    """Stores a record of a user's search queries on the find_alumni page."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
    department = models.CharField(max_length=100, blank=True, null=True)
    graduation_year = models.CharField(max_length=4, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Search by {self.user.username} at {self.timestamp.strftime('%Y-%m-%d')}"    