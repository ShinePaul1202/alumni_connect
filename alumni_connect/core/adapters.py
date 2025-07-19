# core/adapters.py

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse  # ✅ Import the definitive exception
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

class RestrictSocialLoginAdapter(DefaultSocialAccountAdapter):
    """
    A stricter social login adapter that definitively blocks unregistered users.
    It uses ImmediateHttpResponse to halt the allauth login flow completely.
    """
    def pre_social_login(self, request, sociallogin):
        # Get the email from the social provider (e.g., Google)
        email = sociallogin.user.email

        # If the social provider doesn't give us an email, we must stop.
        if not email:
            messages.error(request, "Login failed: Your social account did not provide an email address.")
            # Halt the process and redirect
            raise ImmediateHttpResponse(redirect(reverse('login')))

        try:
            # Find a local user based ONLY on the email address.
            user = User.objects.get(email__iexact=email)

            # If a user is found, the login is potentially valid.
            # We now check if the social account is already connected to our user.
            # If sociallogin.is_existing is True, it means it's already connected, and we can let the login proceed.
            if not sociallogin.is_existing:
                # The social account is new, but the email matches our user.
                # We must explicitly connect this new social account to our email-matched user.
                sociallogin.connect(request, user)

        except User.DoesNotExist:
            # ✅ THIS IS THE CRITICAL PART
            # No user with this email exists. We must block them.
            messages.error(request, "This Google account is not registered. Please sign up manually first.")
            
            # Use ImmediateHttpResponse to stop the entire login process immediately
            # and redirect the user to our login page. Nothing else will run after this.
            raise ImmediateHttpResponse(redirect(reverse('login')))