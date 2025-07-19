from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('alumni', 'Alumni'),
    ]

    # Link to the User model
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # ✅ ADD THIS FIELD TO STORE THE USER'S REAL NAME (NOT UNIQUE)
    full_name = models.CharField(max_length=150)

    # Your existing profile fields
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

    def __str__(self):
        # Display the user's real name in the admin panel
        return self.full_name