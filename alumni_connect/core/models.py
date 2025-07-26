# C:\project\alumni_connect\core\models.py

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
    # This field is named 'avatar'. We will use this name everywhere.
    # IMPORTANT: You must create a folder named 'media/avatars/' and place an image named 'default_avatar.png' inside it.
    avatar = models.ImageField(default='avatars/default_avatar.png', upload_to='avatars/')
    bio = models.TextField(blank=True, null=True)
    
    # User's real name (This seems to duplicate User.first_name and User.last_name, but we'll keep it as it's in your model)
    full_name = models.CharField(max_length=150)

    # Existing profile fields
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    department = models.CharField(max_length=100)
    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    
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
        # Using user.username is safer in case full_name is not set
        return f'{self.user.username} Profile'