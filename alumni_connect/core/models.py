from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('alumni', 'Alumni'),
    ]

    # Link to the User model
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # --- Profile Picture and Bio ---
    avatar = models.ImageField(default='avatars/default_avatar.png', upload_to='avatars/')
    bio = models.TextField(blank=True, null=True)
    full_name = models.CharField(max_length=150)

    # Existing profile fields
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    department = models.CharField(max_length=100)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    has_seen_verification_message = models.BooleanField(default=False)

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
    email_on_new_message = models.BooleanField(default=True)
    
    def __str__(self):
        return f'{self.user.username} Profile'