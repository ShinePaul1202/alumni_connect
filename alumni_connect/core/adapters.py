# alumni_connect/core/adapters.py

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils.translation import gettext as _

class RestrictSocialLoginAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        email = sociallogin.user.email

        if not email:
            messages.error(request, "Google login failed: No email returned.")
            raise PermissionDenied("No email associated with this social account.")

        try:
            # Check if the user with this email already exists
            user = User.objects.get(email=email)
            
            # ✅ Connect the social account to this user
            sociallogin.connect(request, user)

        except User.DoesNotExist:
            # ❌ Block login if the user is not registered manually
            messages.error(request, _("This Google account is not registered. Please sign up manually first."))
            raise PermissionDenied("Google account not registered.")

